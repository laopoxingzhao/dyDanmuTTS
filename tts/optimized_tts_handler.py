import asyncio
import threading
import edge_tts
from config.config import config_manager
from config.log import g_logger
import re
import time
from collections import deque
from queue import Empty, PriorityQueue
import os
import glob
import hashlib
import pygame
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Optional, Dict, Tuple
import weakref
from tool.qt_audio_player import get_audio_player
from tool.memory_manager import get_memory_manager, get_temp_file_manager


@dataclass
class TTSItem:
    """TTS播放项目"""
    priority: int  # 优先级，数字越小优先级越高
    content: str
    timestamp: float = field(default_factory=time.time)
    voice: str = ""
    rate: str = ""
    volume: str = ""
    retry_count: int = 0
    
    def __lt__(self, other):
        """优先级比较，用于优先队列"""
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.timestamp < other.timestamp


class AudioCache:
    """音频缓存管理器"""
    
    def __init__(self, max_size: int = 100, cache_dir: str = "output/cache"):
        self.max_size = max_size
        self.cache_dir = cache_dir
        self.cache: Dict[str, str] = {}  # 内容哈希 -> 文件路径
        self.access_times: Dict[str, float] = {}  # 访问时间记录
        self.lock = threading.RLock()
        
        # 确保缓存目录存在
        os.makedirs(cache_dir, exist_ok=True)
        
        # 启动时加载现有缓存
        self._load_existing_cache()
    
    def _load_existing_cache(self):
        """加载现有的缓存文件"""
        try:
            if os.path.exists(self.cache_dir):
                for file_path in glob.glob(os.path.join(self.cache_dir, "*.mp3")):
                    # 从文件名提取哈希值
                    hash_key = os.path.basename(file_path).replace('.mp3', '')
                    if os.path.exists(file_path):
                        self.cache[hash_key] = file_path
                        self.access_times[hash_key] = os.path.getmtime(file_path)
                
                g_logger.info(f"加载了 {len(self.cache)} 个缓存音频文件")
        except Exception as e:
            g_logger.error(f"加载音频缓存失败: {e}")
    
    def _get_content_hash(self, content: str, voice: str, rate: str, volume: str) -> str:
        """生成内容哈希"""
        content_str = f"{content}|{voice}|{rate}|{volume}"
        return hashlib.md5(content_str.encode('utf-8')).hexdigest()[:16]
    
    def get(self, content: str, voice: str, rate: str, volume: str) -> Optional[str]:
        """获取缓存的音频文件路径"""
        hash_key = self._get_content_hash(content, voice, rate, volume)
        
        with self.lock:
            if hash_key in self.cache:
                file_path = self.cache[hash_key]
                if os.path.exists(file_path):
                    # 更新访问时间
                    self.access_times[hash_key] = time.time()
                    g_logger.debug(f"命中音频缓存: {content[:20]}...")
                    return file_path
                else:
                    # 文件不存在，从缓存中移除
                    del self.cache[hash_key]
                    if hash_key in self.access_times:
                        del self.access_times[hash_key]
        
        return None
    
    def put(self, content: str, voice: str, rate: str, volume: str, source_file: str) -> str:
        """将音频文件添加到缓存"""
        hash_key = self._get_content_hash(content, voice, rate, volume)
        
        with self.lock:
            # 检查缓存大小，如果超出则清理最旧的文件
            if len(self.cache) >= self.max_size:
                self._cleanup_oldest()
            
            # 目标缓存文件路径
            cache_file = os.path.join(self.cache_dir, f"{hash_key}.mp3")
            
            try:
                # 如果源文件和目标文件不同，则复制文件
                if source_file != cache_file and os.path.exists(source_file):
                    import shutil
                    shutil.move(source_file, cache_file)
                
                self.cache[hash_key] = cache_file
                self.access_times[hash_key] = time.time()
                
                g_logger.debug(f"添加音频缓存: {content[:20]}...")
                return cache_file
                
            except Exception as e:
                g_logger.error(f"添加音频缓存失败: {e}")
                return source_file
    
    def _cleanup_oldest(self):
        """清理最旧的缓存文件"""
        if not self.access_times:
            return
        
        # 找到最旧的文件
        oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        
        try:
            oldest_file = self.cache[oldest_key]
            if os.path.exists(oldest_file):
                os.remove(oldest_file)
                g_logger.debug(f"清理旧缓存文件: {oldest_file}")
            
            del self.cache[oldest_key]
            del self.access_times[oldest_key]
            
        except Exception as e:
            g_logger.error(f"清理缓存文件失败: {e}")
    
    def clear(self):
        """清空所有缓存"""
        with self.lock:
            for file_path in self.cache.values():
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as e:
                    g_logger.warning(f"删除缓存文件失败 {file_path}: {e}")
            
            self.cache.clear()
            self.access_times.clear()
            g_logger.info("已清空音频缓存")


class OptimizedTTSHandler:
    """优化的TTS处理器"""
    
    def __init__(self, config_manager=None):
        # 配置管理器
        if config_manager:
            self.config_manager = config_manager
        else:
            from config.config import config_manager
            self.config_manager = config_manager
        
        # 音频缓存
        self.audio_cache = AudioCache(max_size=50)
        
        # 优先队列（高优先级先播放）
        self.tts_queue = PriorityQueue(maxsize=30)
        
        # 线程池用于异步TTS生成
        self.tts_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="TTS-Gen")
        
        # 播放控制
        self.is_running = False
        self.tts_thread = None
        self._lock = threading.RLock()
        self._current_playing = None
        self._playback_lock = threading.Lock()
        
        # 使用优化的音频播放器和内存管理器
        self.audio_player = get_audio_player()
        self.memory_manager = get_memory_manager()
        self.temp_file_manager = get_temp_file_manager()
        
        # 注册内存管理清理回调
        self.memory_manager.add_cleanup_callback(self.cleanup_temp_files)
        
        # 性能统计
        self.stats = {
            'total_played': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'generation_time': 0,
            'playback_time': 0
        }
        
        # 从配置加载TTS参数
        self._load_tts_settings()
        
        # 注册配置变更回调
        self._register_config_callback()
    
    def _init_pygame_mixer(self):
        """初始化pygame mixer（使用优化的音频播放器）"""
        try:
            if not self.audio_player.initialized:
                self.audio_player.initialize()
                g_logger.info("优化音频播放器初始化成功")
        except Exception as e:
            g_logger.error(f"优化音频播放器初始化失败: {e}")
    
    def _load_tts_settings(self):
        """从配置加载TTS参数"""
        tts_settings = self.config_manager.tts_settings
        
        with self._lock:
            self.volume = f"+{tts_settings.volume - 50}%"
            self.voice = self._get_voice_name(tts_settings.voice)
            speed_value = tts_settings.speed
            rate_value = (speed_value - 10) * 5
            if rate_value >= 0:
                self.rate = f"+{rate_value}%"
            else:
                self.rate = f"{rate_value}%"
            
            self.tts_enabled = tts_settings.tts_enabled
    
    def _get_voice_name(self, voice_index):
        """根据索引获取语音名称"""
        voice_map = {
            0: "zh-CN-XiaoxiaoNeural",
            1: "zh-CN-YunxiNeural",
            2: "zh-HK-HiuGaaiNeural",
            3: "zh-HK-HiuMaanNeural",
            4: "en-US-JennyNeural",
            5: "en-US-GuyNeural"
        }
        return voice_map.get(voice_index, "zh-CN-XiaoxiaoNeural")
    
    def _get_message_priority(self, content: str) -> int:
        """根据消息内容获取优先级"""
        # 礼物消息优先级最高
        if any(keyword in content for keyword in ["送出", "赠送", "礼物"]):
            return 1
        # 关注消息
        elif any(keyword in content for keyword in ["关注", "加入粉丝团"]):
            return 2
        # 进入消息
        elif any(keyword in content for keyword in ["进入", "来到"]):
            return 3
        # 普通聊天消息
        else:
            return 4
    
    def add_tts_item(self, content: str, priority: Optional[int] = None):
        """添加TTS播放项目到队列"""
        if not content or not content.strip():
            return False
        
        if not self._is_tts_enabled():
            return False
        
        try:
            if priority is None:
                priority = self._get_message_priority(content)
            
            tts_item = TTSItem(
                priority=priority,
                content=content.strip(),
                voice=self.voice,
                rate=self.rate,
                volume=self.volume
            )
            
            # 非阻塞添加到队列
            try:
                self.tts_queue.put_nowait(tts_item)
                g_logger.debug(f"添加TTS项目到队列: {content[:30]}... (优先级: {priority})")
                return True
            except:
                # 队列满了，移除一个最低优先级的旧项目
                try:
                    # 获取并丢弃最低优先级的项目
                    old_items = []
                    while not self.tts_queue.empty():
                        old_items.append(self.tts_queue.get_nowait())
                    
                    # 保留除了最低优先级之外的项目
                    if old_items:
                        # 找到最低优先级的项目
                        min_priority_item = max(old_items, key=lambda x: x.priority)
                        old_items.remove(min_priority_item)
                        
                        # 重新添加剩余项目
                        for item in old_items:
                            self.tts_queue.put_nowait(item)
                    
                    # 添加新项目
                    self.tts_queue.put_nowait(tts_item)
                    g_logger.warning(f"TTS队列已满，已移除低优先级项目")
                    return True
                    
                except Exception as e:
                    g_logger.error(f"处理TTS队列满时出错: {e}")
                    return False
                    
        except Exception as e:
            g_logger.error(f"添加TTS项目失败: {e}")
            return False
    
    def start(self):
        """启动TTS处理器"""
        if self.is_running:
            return
        
        self.is_running = True
        self.tts_thread = threading.Thread(target=self._process_tts_queue, daemon=True)
        self.tts_thread.start()
        
        g_logger.info("优化的TTS处理器已启动")
    
    def stop(self):
        """停止TTS处理器"""
        self.is_running = False
        
        # 停止当前播放
        self._stop_current_playback()
        
        # 等待线程结束
        if self.tts_thread:
            self.tts_thread.join(timeout=3)
        
        # 关闭线程池
        self.tts_executor.shutdown(wait=True)
        
        # 清理缓存和临时文件
        self.audio_cache.clear()
        self.cleanup_temp_files()
        
        # 移除内存管理回调
        self.memory_manager.remove_cleanup_callback(self.cleanup_temp_files)
        
        g_logger.info("优化的TTS处理器已停止")
    
    def _process_tts_queue(self):
        """处理TTS队列的后台线程"""
        while self.is_running:
            try:
                if not self._is_tts_enabled():
                    time.sleep(0.5)
                    continue
                
                # 从优先队列获取消息
                try:
                    tts_item = self.tts_queue.get(timeout=0.1)
                except:
                    continue
                
                # 异步处理TTS生成和播放
                future = self.tts_executor.submit(self._process_tts_item, tts_item)
                
                # 等待当前播放完成再处理下一个
                try:
                    future.result(timeout=30)  # 最多等待30秒
                except Exception as e:
                    g_logger.error(f"TTS处理超时或失败: {e}")
                
            except Exception as e:
                g_logger.error(f"处理TTS队列时出错: {e}")
                time.sleep(1)
    
    def _process_tts_item(self, tts_item: TTSItem):
        """处理单个TTS项目"""
        start_time = time.time()
        
        try:
            # 检查TTS是否仍然启用
            if not self._is_tts_enabled():
                return
            
            content = tts_item.content
            
            # 尝试从缓存获取
            cached_file = self.audio_cache.get(
                content, tts_item.voice, tts_item.rate, tts_item.volume
            )
            
            if cached_file:
                self.stats['cache_hits'] += 1
                self._play_audio_file(cached_file, content)
            else:
                self.stats['cache_misses'] += 1
                # 生成新的音频
                audio_file = self._generate_audio_sync(tts_item)
                if audio_file:
                    # 添加到缓存
                    cached_file = self.audio_cache.put(
                        content, tts_item.voice, tts_item.rate, tts_item.volume, audio_file
                    )
                    self._play_audio_file(cached_file, content)
            
            # 更新统计
            self.stats['total_played'] += 1
            self.stats['generation_time'] += time.time() - start_time
            
        except Exception as e:
            g_logger.error(f"处理TTS项目失败: {e}")
    
    def _generate_audio_sync(self, tts_item: TTSItem) -> Optional[str]:
        """同步生成音频文件"""
        temp_file = None
        try:
            # 使用内存管理器创建临时文件
            temp_file = self.memory_manager.create_temp_file("tts", ".mp3")
            if not temp_file:
                # 备用方案
                import uuid
                unique_id = str(uuid.uuid4())[:8]
                temp_file = f"output/temp_{unique_id}.mp3"
            
            # 添加到临时文件管理
            self.temp_file_manager.add_temp_file(temp_file)
            
            # 使用edge_tts生成音频
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                communicate = edge_tts.Communicate(
                    tts_item.content,
                    voice=tts_item.voice,
                    rate=tts_item.rate,
                    volume=tts_item.volume
                )
                loop.run_until_complete(communicate.save(temp_file))
                
                if os.path.exists(temp_file):
                    return temp_file
                else:
                    g_logger.error(f"生成的音频文件不存在: {temp_file}")
                    return None
                    
            finally:
                loop.close()
                
        except Exception as e:
            g_logger.error(f"生成音频失败: {e}")
            if temp_file:
                self.temp_file_manager.remove_temp_file(temp_file)
            return None
    
    def _play_audio_file(self, file_path: str, content: str):
        """播放音频文件（使用优化的音频播放器）"""
        if not os.path.exists(file_path):
            g_logger.error(f"音频文件不存在: {file_path}")
            return
        
        start_time = time.time()
        
        with self._playback_lock:
            try:
                # 确保音频播放器已初始化
                if not self.audio_player.initialized:
                    self.audio_player.initialize()
                
                # 记录当前播放
                self._current_playing = file_path
                
                # 设置音量（从TTS音量设置转换）
                volume_percent = int(self.volume.replace('+', '').replace('%', '')) / 100
                self.audio_player.set_volume(volume_percent)
                
                # 预加载音频（如果还没有）
                cache_key = f"tts_{content[:20]}"
                self.audio_player.preload_audio(file_path, cache_key)
                
                # 播放音频
                success = self.audio_player.play_file(file_path, cache_key)
                
                if success:
                    g_logger.debug(f"TTS播放完成: {content[:30]}...")
                else:
                    g_logger.error(f"TTS播放失败: {content[:30]}...")
                
            except Exception as e:
                g_logger.error(f"播放音频失败: {e}")
            finally:
                self._current_playing = None
                self.stats['playback_time'] += time.time() - start_time
    
    def _stop_current_playback(self):
        """停止当前播放"""
        with self._playback_lock:
            try:
                if self.audio_player.initialized:
                    self.audio_player.stop()
                    g_logger.debug("已停止当前TTS播放")
            except Exception as e:
                g_logger.warning(f"停止播放失败: {e}")
    
    def _is_tts_enabled(self):
        """检查TTS是否启用"""
        try:
            current_tts_enabled = self.config_manager.tts_settings.tts_enabled
            if current_tts_enabled != getattr(self, 'tts_enabled', None):
                with self._lock:
                    self.tts_enabled = current_tts_enabled
                    g_logger.info(f"TTS启用状态变更: {current_tts_enabled}")
            return current_tts_enabled
        except Exception as e:
            g_logger.error(f"检查TTS启用状态失败: {e}")
            return False
    
    def _register_config_callback(self):
        """注册配置变更回调"""
        try:
            self.config_manager.add_config_change_callback(self._on_config_changed)
            g_logger.debug("优化TTS处理器已注册配置变更回调")
        except Exception as e:
            g_logger.error(f"注册配置变更回调失败: {e}")
    
    def _on_config_changed(self, config_type: str, key: str, value):
        """配置变更回调处理"""
        try:
            if config_type == 'tts':
                g_logger.debug(f"检测到TTS配置变更: {key} = {value}")
                
                if key == 'tts_enabled':
                    with self._lock:
                        self.tts_enabled = value
                    if not value:
                        self._stop_current_playback()
                        g_logger.info("TTS已禁用，已停止当前播放")
                    else:
                        g_logger.info("TTS已启用")
                else:
                    # 其他配置变更，重新加载设置
                    self._load_tts_settings()
                    g_logger.info(f"TTS配置已更新")
                    
        except Exception as e:
            g_logger.error(f"处理配置变更回调失败: {e}")
    
    def get_stats(self) -> Dict:
        """获取性能统计信息"""
        with self._lock:
            stats = self.stats.copy()
            if stats['cache_hits'] + stats['cache_misses'] > 0:
                stats['cache_hit_rate'] = stats['cache_hits'] / (stats['cache_hits'] + stats['cache_misses'])
            else:
                stats['cache_hit_rate'] = 0
            
            if stats['total_played'] > 0:
                stats['avg_generation_time'] = stats['generation_time'] / stats['total_played']
                stats['avg_playback_time'] = stats['playback_time'] / stats['total_played']
            else:
                stats['avg_generation_time'] = 0
                stats['avg_playback_time'] = 0
            
            stats['queue_size'] = self.tts_queue.qsize()
            stats['cache_size'] = len(self.audio_cache.cache)
            
            return stats
    
    def preload_audio(self, text: str) -> bool:
        """预加载音频到缓存"""
        try:
            # 检查是否已在缓存中
            cached_file = self.audio_cache.get(text, self.voice, self.rate, self.volume)
            if cached_file:
                return True
            
            # 生成音频并添加到缓存
            tts_item = TTSItem(
                priority=1,
                content=text,
                voice=self.voice,
                rate=self.rate,
                volume=self.volume
            )
            
            audio_file = self._generate_audio_sync(tts_item)
            if audio_file:
                self.audio_cache.put(text, self.voice, self.rate, self.volume, audio_file)
                g_logger.debug(f"预加载音频成功: {text[:30]}...")
                return True
            
            return False
            
        except Exception as e:
            g_logger.error(f"预加载音频失败: {e}")
            return False
    
    def pause(self):
        """暂停TTS播放"""
        with self._playback_lock:
            try:
                if self.audio_player.initialized:
                    self.audio_player.pause()
                    g_logger.info("TTS播放已暂停")
            except Exception as e:
                g_logger.error(f"暂停TTS播放失败: {e}")
    
    def resume(self):
        """恢复TTS播放"""
        with self._playback_lock:
            try:
                if self.audio_player.initialized:
                    self.audio_player.resume()
                    g_logger.info("TTS播放已恢复")
            except Exception as e:
                g_logger.error(f"恢复TTS播放失败: {e}")
    
    def clear_cache(self):
        """清空音频缓存"""
        self.audio_cache.clear()
        g_logger.info("已清空音频缓存")
    
    def cleanup_temp_files(self):
        """清理临时文件"""
        self.temp_file_manager.cleanup_temp_files()
    
    def get_memory_stats(self) -> Dict:
        """获取内存使用统计"""
        memory_stats = self.memory_manager.get_cleanup_stats()
        temp_stats = {
            'temp_file_count': self.temp_file_manager.get_temp_file_count(),
            'cache_size': len(self.audio_cache.cache)
        }
        
        return {
            'memory_manager': memory_stats,
            'temp_files': temp_stats
        }
    
    def update_config(self):
        """更新配置参数"""
        g_logger.info("正在更新优化TTS配置...")
        self._load_tts_settings()
        g_logger.info(f"优化TTS配置已更新 - 音量:{self.volume}, 语速:{self.rate}, 声音:{self.voice}")


# 全局优化TTS处理器实例
optimized_tts_handler = None

def init_optimized_tts_handler(config_manager=None):
    """初始化优化的TTS处理器"""
    global optimized_tts_handler
    if optimized_tts_handler is None:
        optimized_tts_handler = OptimizedTTSHandler(config_manager)
    return optimized_tts_handler