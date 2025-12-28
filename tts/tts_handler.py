import asyncio
import threading
import edge_tts
from config.config import config_manager
from config.log import g_logger
import re
import time
from collections import deque
from queue import Empty
import os
import glob


class TTSHandler:
    def __init__(self, config_manager=None):
        # 使用传入的配置管理器或全局配置管理器
        if config_manager:
            self.config_manager = config_manager
        else:
            from config.config import config_manager
            self.config_manager = config_manager
            
        # 用于存储已处理消息的信息，防止重复播报
        self.message_history = {}
        # TTS队列配置
        tts_settings = self.config_manager.tts_settings
        self.queue_settings = {
            "dedup_time_window": 30,  # 去重时间窗口（秒）
            "min_interval": 5,        # 同类型消息最小间隔（秒）
            "max_queue_size": 20      # 队列最大长度
        }
        self.is_running = False
        self.tts_thread = None
        self._lock = threading.Lock()
        self._cleanup_timer = None
        self._current_playing_file = None
        
        # 从配置加载TTS参数
        self._load_tts_settings()
        
    def _load_tts_settings(self):
        """从配置加载TTS参数"""
        tts_settings = self.config_manager.tts_settings
        
        with self._lock:
            self.volume = f"+{tts_settings.volume - 50}%"  # 转换为edge-tts格式
            self.voice = self._get_voice_name(tts_settings.voice)
            speed_value = tts_settings.speed
            # 修正语速计算：避免负值
            rate_value = (speed_value - 10) * 5  # 减小倍数，避免超出范围
            if rate_value >= 0:
                self.rate = f"+{rate_value}%"
            else:
                self.rate = f"{rate_value}%"  # 负值不加+号
            
            # 记录当前TTS启用状态
            self.tts_enabled = tts_settings.tts_enabled
            
        # 注册配置变更回调
        self._register_config_callback()

    def _get_voice_name(self, voice_index):
        """根据索引获取语音名称"""
        voice_map = {
            0: "zh-CN-XiaoxiaoNeural",  # 普通话-女声
            1: "zh-CN-YunxiNeural",    # 普通话-男声
            2: "zh-HK-HiuGaaiNeural",  # 粤语-女声
            3: "zh-HK-HiuMaanNeural",  # 粤语-女声（可能需要调整）
            4: "en-US-JennyNeural",    # 英语-女声
            5: "en-US-GuyNeural"       # 英语-男声
        }
        return voice_map.get(voice_index, "zh-CN-XiaoxiaoNeural")
    
    def update_config(self):
        """更新配置参数"""
        g_logger.info("正在更新TTS配置...")
        self._load_tts_settings()
        g_logger.info(f"TTS配置已更新 - 音量:{self.volume}, 语速:{self.rate}, 声音:{self.voice}, 启用状态:{self.tts_enabled}")
        
    def _register_config_callback(self):
        """注册配置变更回调"""
        try:
            self.config_manager.add_config_change_callback(self._on_config_changed)
            g_logger.debug("TTS处理器已注册配置变更回调")
        except Exception as e:
            g_logger.error(f"注册配置变更回调失败: {e}")
            
    def _on_config_changed(self, config_type: str, key: str, value):
        """配置变更回调处理"""
        try:
            if config_type == 'tts':
                g_logger.debug(f"检测到TTS配置变更: {key} = {value}")
                
                # 如果是TTS总开关变更，立即停止当前播放
                if key == 'tts_enabled':
                    with self._lock:
                        self.tts_enabled = value
                    if not value:
                        self._stop_current_playback()
                        g_logger.info("TTS已禁用，已停止当前播放")
                    else:
                        g_logger.info("TTS已启用")
                        
                # 其他TTS配置变更也会在下次播放时生效
                # 这里可以添加更多特定配置的处理逻辑
                
        except Exception as e:
            g_logger.error(f"处理配置变更回调失败: {e}")
    
    def start(self):
        """启动TTS处理器"""
        if self.is_running:
            return
            
        self.is_running = True
        self.tts_thread = threading.Thread(target=self._process_tts_queue, daemon=True)
        self.tts_thread.start()
        
        # 启动定时清理任务
        self._start_cleanup_timer()
        g_logger.info("TTS处理器已启动，包含定时清理任务")
    
    def stop(self):
        """停止TTS处理器"""
        self.is_running = False
        
        # 停止清理定时器
        if self._cleanup_timer:
            self._cleanup_timer.cancel()
            self._cleanup_timer = None
            
        # 停止当前播放
        self._stop_current_playback()
        
        if self.tts_thread:
            self.tts_thread.join(timeout=2)  # 等待最多2秒
            
        # 清理所有临时文件
        self._cleanup_all_temp_files()
        g_logger.info("TTS处理器已停止")
    
    def _process_tts_queue(self):
        """处理TTS队列的后台线程"""
        from tool.myqueue import ttsq
        
        while self.is_running:
            try:
                # 检查TTS总开关状态
                if not self._is_tts_enabled():
                    time.sleep(0.5)  # TTS未启用时，稍长等待
                    continue
                    
                # 从TTS队列获取消息
                tts_item = ttsq.get()
                if tts_item:
                    content = tts_item.get('content', '')
                    if content.strip():
                        g_logger.debug(f"播放TTS: {content}")
                        self._play_tts(content)
                else:
                    time.sleep(0.1)  # 队列为空时稍作等待
            except Exception as e:
                g_logger.error(f"处理TTS队列时出错: {e}")
                time.sleep(1)  # 出错时等待一段时间再继续

    def _is_tts_enabled(self):
        """检查TTS是否启用"""
        try:
            # 实时检查配置中的TTS启用状态
            current_tts_enabled = self.config_manager.tts_settings.tts_enabled
            if current_tts_enabled != getattr(self, 'tts_enabled', None):
                # 配置发生变化，更新本地状态
                with self._lock:
                    self.tts_enabled = current_tts_enabled
                    g_logger.info(f"TTS启用状态变更: {current_tts_enabled}")
            return current_tts_enabled
        except Exception as e:
            g_logger.error(f"检查TTS启用状态失败: {e}")
            return False
    
    def _play_tts(self, text):
        """播放TTS文本"""
        try:
            # 再次检查TTS是否启用（防止配置在队列处理后发生变化）
            if not self._is_tts_enabled():
                g_logger.debug(f"TTS已禁用，跳过播放: {text}")
                return
                
            # 创建临时事件循环来运行async函数
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    self._tts_generation_and_play(text, self.voice, self.rate, self.volume)
                )
            finally:
                loop.close()
        except Exception as e:
            g_logger.error(f"TTS播放失败: {e}")
            # 清理可能残留的文件
            self._cleanup_current_file()
    
    async def _tts_generation_and_play(self, text, voice, rate, volume):
        """生成TTS音频并播放"""
        output_file = None
        try:
            import pygame
            
            # 确保输出目录存在
            os.makedirs("output", exist_ok=True)
            
            # 生成唯一音频文件名
            import uuid
            unique_id = str(uuid.uuid4())[:8]
            output_file = f"output/temp_tts_{unique_id}.mp3"
            
            # 记录当前播放的文件
            with self._lock:
                self._current_playing_file = output_file
            
            communicate = edge_tts.Communicate(text, voice=voice, rate=rate, volume=volume)
            await communicate.save(output_file)
            
            # 播放音频文件
            if os.path.exists(output_file):
                # 初始化pygame mixer（只在第一次时初始化）
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                
                # 停止当前播放
                pygame.mixer.music.stop()
                
                pygame.mixer.music.load(output_file)
                pygame.mixer.music.play()
                
                # 等待播放完成，同时检查TTS是否仍然启用
                while pygame.mixer.music.get_busy():
                    if not self._is_tts_enabled():
                        g_logger.debug("TTS播放过程中被禁用，停止播放")
                        pygame.mixer.music.stop()
                        break
                    await asyncio.sleep(0.1)
                
                g_logger.debug(f"TTS播放完成: {text}")
            else:
                g_logger.error(f"TTS音频文件未生成: {output_file}")
                
        except Exception as e:
            g_logger.error(f"TTS生成和播放失败: {e}")
        finally:
            # 清理临时文件
            self._cleanup_current_file()
            
    def _cleanup_current_file(self):
        """清理当前播放的音频文件"""
        with self._lock:
            if self._current_playing_file and os.path.exists(self._current_playing_file):
                try:
                    os.remove(self._current_playing_file)
                    g_logger.debug(f"已清理音频文件: {self._current_playing_file}")
                except Exception as e:
                    g_logger.warning(f"清理音频文件失败: {e}")
                finally:
                    self._current_playing_file = None

    def _stop_current_playback(self):
        """停止当前播放"""
        try:
            import pygame
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
                g_logger.debug("已停止当前TTS播放")
        except Exception as e:
            g_logger.warning(f"停止播放失败: {e}")

    def _start_cleanup_timer(self):
        """启动定时清理任务"""
        def cleanup_task():
            while self.is_running:
                try:
                    self._cleanup_old_files()
                    time.sleep(60)  # 每分钟清理一次
                except Exception as e:
                    g_logger.error(f"定时清理任务出错: {e}")
                    time.sleep(60)
        
        cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
        cleanup_thread.start()

    def _cleanup_old_files(self):
        """清理旧的临时音频文件"""
        try:
            output_dir = "output"
            if not os.path.exists(output_dir):
                return
                
            # 查找所有临时TTS文件
            pattern = os.path.join(output_dir, "temp_tts_*.mp3")
            temp_files = glob.glob(pattern)
            
            current_time = time.time()
            for file_path in temp_files:
                try:
                    # 获取文件修改时间
                    file_time = os.path.getmtime(file_path)
                    # 删除超过5分钟的文件
                    if current_time - file_time > 300:  # 5分钟
                        os.remove(file_path)
                        g_logger.debug(f"已清理旧文件: {file_path}")
                except Exception as e:
                    g_logger.warning(f"清理文件失败 {file_path}: {e}")
                    
        except Exception as e:
            g_logger.error(f"清理旧文件失败: {e}")

    def _cleanup_all_temp_files(self):
        """清理所有临时音频文件"""
        try:
            output_dir = "output"
            if not os.path.exists(output_dir):
                return
                
            pattern = os.path.join(output_dir, "temp_tts_*.mp3")
            temp_files = glob.glob(pattern)
            
            for file_path in temp_files:
                try:
                    os.remove(file_path)
                    g_logger.debug(f"已清理临时文件: {file_path}")
                except Exception as e:
                    g_logger.warning(f"清理临时文件失败 {file_path}: {e}")
                    
        except Exception as e:
            g_logger.error(f"清理所有临时文件失败: {e}")


# 全局TTS处理器实例
tts_handler = None

def init_tts_handler(config_manager=None):
    """初始化TTS处理器"""
    global tts_handler
    if tts_handler is None:
        tts_handler = TTSHandler(config_manager)
    return tts_handler