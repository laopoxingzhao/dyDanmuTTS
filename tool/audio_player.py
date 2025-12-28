import pygame
import threading
import time
import os
from typing import Optional, Dict
from config.log import g_logger


class OptimizedAudioPlayer:
    """优化的音频播放器，提供更好的性能和内存管理"""
    
    def __init__(self, sample_rate: int = 22050, buffer_size: int = 512):
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.initialized = False
        self._lock = threading.RLock()
        self._current_file = None
        self._is_paused = False
        self._volume = 1.0
        
        # 预加载的音频缓存
        self._preloaded_sounds: Dict[str, pygame.mixer.Sound] = {}
        self._max_preload = 10  # 最多预加载10个音频
        
        # 播放统计
        self.stats = {
            'total_played': 0,
            'total_duration': 0,
            'average_load_time': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    def initialize(self) -> bool:
        """初始化音频系统"""
        with self._lock:
            if self.initialized:
                return True
            
            try:
                # 设置pygame音频参数以获得更好的性能
                pygame.mixer.pre_init(
                    frequency=self.sample_rate,
                    size=-16,  # 16位音频
                    channels=2,  # 立体声
                    buffer=self.buffer_size,  # 较小的缓冲区以减少延迟
                    allowedchanges=pygame.AUDIO_ALLOW_FREQUENCY_CHANGE | pygame.AUDIO_ALLOW_CHANNELS_CHANGE
                )
                
                pygame.mixer.init()
                self.initialized = True
                
                # 设置默认音量
                pygame.mixer.music.set_volume(self._volume)
                
                g_logger.info(f"优化音频播放器初始化成功 - 采样率:{self.sample_rate}, 缓冲区:{self.buffer_size}")
                return True
                
            except Exception as e:
                g_logger.error(f"音频播放器初始化失败: {e}")
                return False
    
    def shutdown(self):
        """关闭音频系统"""
        with self._lock:
            if not self.initialized:
                return
            
            try:
                # 停止当前播放
                self.stop()
                
                # 清理预加载的音频
                for sound in self._preloaded_sounds.values():
                    try:
                        sound.stop()
                    except:
                        pass
                self._preloaded_sounds.clear()
                
                # 关闭pygame mixer
                pygame.mixer.quit()
                self.initialized = False
                
                g_logger.info("优化音频播放器已关闭")
                
            except Exception as e:
                g_logger.error(f"音频播放器关闭失败: {e}")
    
    def preload_audio(self, file_path: str, cache_key: Optional[str] = None) -> bool:
        """预加载音频文件到内存"""
        if not self.initialized:
            if not self.initialize():
                return False
        
        with self._lock:
            try:
                if cache_key is None:
                    cache_key = file_path
                
                # 检查是否已预加载
                if cache_key in self._preloaded_sounds:
                    return True
                
                # 检查预加载限制
                if len(self._preloaded_sounds) >= self._max_preload:
                    self._cleanup_oldest_preload()
                
                # 预加载音频
                start_time = time.time()
                sound = pygame.mixer.Sound(file_path)
                load_time = time.time() - start_time
                
                self._preloaded_sounds[cache_key] = sound
                
                # 更新统计
                self.stats['average_load_time'] = (
                    (self.stats['average_load_time'] * self.stats['cache_hits'] + load_time) / 
                    (self.stats['cache_hits'] + 1)
                )
                self.stats['cache_hits'] += 1
                
                g_logger.debug(f"预加载音频成功: {file_path} (加载时间: {load_time:.3f}s)")
                return True
                
            except Exception as e:
                g_logger.error(f"预加载音频失败 {file_path}: {e}")
                self.stats['cache_misses'] += 1
                return False
    
    def play_file(self, file_path: str, cache_key: Optional[str] = None, 
                 fade_in: int = 0, loops: int = 0) -> bool:
        """播放音频文件"""
        if not os.path.exists(file_path):
            g_logger.error(f"音频文件不存在: {file_path}")
            return False
        
        if not self.initialized:
            if not self.initialize():
                return False
        
        with self._lock:
            try:
                start_time = time.time()
                
                # 停止当前播放
                self.stop()
                
                self._current_file = file_path
                self._is_paused = False
                
                # 尝试使用预加载的音频
                if cache_key and cache_key in self._preloaded_sounds:
                    sound = self._preloaded_sounds[cache_key]
                    
                    # 设置音量
                    sound.set_volume(self._volume)
                    
                    # 播放音频
                    if fade_in > 0:
                        sound.play(loops, fade_ms=fade_in)
                    else:
                        sound.play(loops)
                    
                    # 等待播放完成
                    while pygame.mixer.get_busy():
                        if self._is_paused:
                            pygame.mixer.pause()
                            while self._is_paused:
                                time.sleep(0.01)
                            pygame.mixer.unpause()
                        
                        if not self._current_file:  # 被停止了
                            break
                        time.sleep(0.01)
                    
                    self.stats['total_played'] += 1
                    self.stats['total_duration'] += time.time() - start_time
                    
                    g_logger.debug(f"播放预加载音频完成: {file_path}")
                    return True
                
                else:
                    # 使用music模块播放（适用于较大的文件）
                    pygame.mixer.music.load(file_path)
                    pygame.mixer.music.set_volume(self._volume)
                    
                    if fade_in > 0:
                        pygame.mixer.music.play(loops, fade_ms=fade_in)
                    else:
                        pygame.mixer.music.play(loops)
                    
                    # 等待播放完成
                    while pygame.mixer.music.get_busy():
                        if self._is_paused:
                            pygame.mixer.music.pause()
                            while self._is_paused:
                                time.sleep(0.01)
                            pygame.mixer.music.unpause()
                        
                        if not self._current_file:  # 被停止了
                            break
                        time.sleep(0.01)
                    
                    self.stats['total_played'] += 1
                    self.stats['total_duration'] += time.time() - start_time
                    
                    g_logger.debug(f"播放音频文件完成: {file_path}")
                    return True
                
            except Exception as e:
                g_logger.error(f"播放音频失败 {file_path}: {e}")
                return False
            finally:
                self._current_file = None
    
    def play_sound_effect(self, file_path: str, volume: float = 1.0) -> bool:
        """播放音效（叠加播放）"""
        if not self.initialized:
            if not self.initialize():
                return False
        
        try:
            sound = pygame.mixer.Sound(file_path)
            sound.set_volume(volume * self._volume)
            sound.play()
            return True
            
        except Exception as e:
            g_logger.error(f"播放音效失败 {file_path}: {e}")
            return False
    
    def stop(self):
        """停止当前播放"""
        with self._lock:
            try:
                if self.initialized:
                    pygame.mixer.music.stop()
                    pygame.mixer.stop()
                
                self._current_file = None
                self._is_paused = False
                
                g_logger.debug("音频播放已停止")
                
            except Exception as e:
                g_logger.error(f"停止音频播放失败: {e}")
    
    def pause(self):
        """暂停播放"""
        with self._lock:
            if self.initialized and not self._is_paused:
                try:
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.pause()
                    
                    self._is_paused = True
                    g_logger.debug("音频播放已暂停")
                    
                except Exception as e:
                    g_logger.error(f"暂停音频播放失败: {e}")
    
    def resume(self):
        """恢复播放"""
        with self._lock:
            if self.initialized and self._is_paused:
                try:
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.unpause()
                    
                    self._is_paused = False
                    g_logger.debug("音频播放已恢复")
                    
                except Exception as e:
                    g_logger.error(f"恢复音频播放失败: {e}")
    
    def set_volume(self, volume: float):
        """设置音量 (0.0 - 1.0)"""
        with self._lock:
            self._volume = max(0.0, min(1.0, volume))
            
            if self.initialized:
                pygame.mixer.music.set_volume(self._volume)
                
                # 更新预加载音频的音量
                for sound in self._preloaded_sounds.values():
                    sound.set_volume(self._volume)
    
    def get_volume(self) -> float:
        """获取当前音量"""
        return self._volume
    
    def is_playing(self) -> bool:
        """检查是否正在播放"""
        if not self.initialized:
            return False
        
        try:
            return pygame.mixer.music.get_busy() or pygame.mixer.get_busy()
        except:
            return False
    
    def is_paused(self) -> bool:
        """检查是否已暂停"""
        return self._is_paused
    
    def get_current_file(self) -> Optional[str]:
        """获取当前播放的文件"""
        return self._current_file
    
    def _cleanup_oldest_preload(self):
        """清理最旧的预加载音频"""
        if not self._preloaded_sounds:
            return
        
        # 移除第一个预加载的音频
        oldest_key = next(iter(self._preloaded_sounds))
        del self._preloaded_sounds[oldest_key]
        
        g_logger.debug(f"清理最旧的预加载音频: {oldest_key}")
    
    def clear_preloaded_cache(self):
        """清空预加载缓存"""
        with self._lock:
            for sound in self._preloaded_sounds.values():
                try:
                    sound.stop()
                except:
                    pass
            
            self._preloaded_sounds.clear()
            g_logger.info("已清空预加载音频缓存")
    
    def get_stats(self) -> Dict:
        """获取播放统计信息"""
        with self._lock:
            stats = self.stats.copy()
            stats['preloaded_count'] = len(self._preloaded_sounds)
            stats['cache_hit_rate'] = (
                stats['cache_hits'] / max(stats['cache_hits'] + stats['cache_misses'], 1)
            )
            
            if stats['total_played'] > 0:
                stats['average_duration'] = stats['total_duration'] / stats['total_played']
            else:
                stats['average_duration'] = 0
            
            return stats
    
    def get_device_info(self) -> Dict:
        """获取音频设备信息"""
        if not self.initialized:
            return {}
        
        try:
            info = {
                'initialized': self.initialized,
                'sample_rate': self.sample_rate,
                'buffer_size': self.buffer_size,
                'frequency': pygame.mixer.get_init()[0] if pygame.mixer.get_init() else 0,
                'size': pygame.mixer.get_init()[1] if pygame.mixer.get_init() else 0,
                'channels': pygame.mixer.get_init()[2] if pygame.mixer.get_init() else 0,
            }
            
            return info
            
        except Exception as e:
            g_logger.error(f"获取音频设备信息失败: {e}")
            return {}


# 全局音频播放器实例
audio_player = OptimizedAudioPlayer()

def get_audio_player() -> OptimizedAudioPlayer:
    """获取全局音频播放器实例"""
    return audio_player