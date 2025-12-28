import threading
import time
import os
from typing import Optional, Dict
from PyQt5.QtCore import QObject, QUrl, pyqtSignal, QTimer
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from config.log import g_logger


class QtAudioPlayer(QObject):
    """基于Qt的音频播放器，提供更好的性能和内存管理"""
    
    # 信号定义
    playback_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self, sample_rate: int = 22050, buffer_size: int = 512):
        super().__init__()
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.initialized = False
        self._lock = threading.RLock()
        self._current_file = None
        self._is_paused = False
        self._volume = 1.0
        
        # Qt媒体播放器
        self.media_player = None
        self._playback_timer = None
        
        # 预加载的音频缓存
        self._preloaded_sounds: Dict[str, QMediaContent] = {}
        self._max_preload = 10  # 最多预加载10个音频
        
        # 播放统计
        self.stats = {
            'total_played': 0,
            'total_duration': 0,
            'average_load_time': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        # 初始化媒体播放器
        self._init_media_player()
    
    def _init_media_player(self):
        """初始化Qt媒体播放器"""
        try:
            self.media_player = QMediaPlayer()
            
            # 连接信号
            self.media_player.stateChanged.connect(self._on_state_changed)
            self.media_player.error.connect(self._on_error)
            self.media_player.positionChanged.connect(self._on_position_changed)
            self.media_player.durationChanged.connect(self._on_duration_changed)
            
            # 设置播放完成定时器
            self._playback_timer = QTimer()
            self._playback_timer.timeout.connect(self._check_playback_finished)
            self._playback_timer.setSingleShot(True)
            
            self.initialized = True
            g_logger.info(f"Qt音频播放器初始化成功 - 采样率:{self.sample_rate}")
            
        except Exception as e:
            g_logger.error(f"Qt音频播放器初始化失败: {e}")
            self.initialized = False
    
    def initialize(self) -> bool:
        """初始化音频系统"""
        if self.initialized:
            return True
        
        try:
            self._init_media_player()
            
            # 设置默认音量
            self.set_volume(self._volume)
            
            g_logger.info(f"Qt音频播放器初始化成功 - 采样率:{self.sample_rate}")
            return True
            
        except Exception as e:
            g_logger.error(f"Qt音频播放器初始化失败: {e}")
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
                self._preloaded_sounds.clear()
                
                # 释放媒体播放器
                if self.media_player:
                    self.media_player.stop()
                    self.media_player.setMedia(QMediaContent())
                    self.media_player = None
                
                if self._playback_timer:
                    self._playback_timer.stop()
                    self._playback_timer = None
                
                self.initialized = False
                
                g_logger.info("Qt音频播放器已关闭")
                
            except Exception as e:
                g_logger.error(f"Qt音频播放器关闭失败: {e}")
    
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
                
                if os.path.exists(file_path):
                    url = QUrl.fromLocalFile(file_path)
                    media_content = QMediaContent(url)
                    self._preloaded_sounds[cache_key] = media_content
                    
                    load_time = time.time() - start_time
                    
                    # 更新统计
                    self.stats['average_load_time'] = (
                        (self.stats['average_load_time'] * self.stats['cache_hits'] + load_time) / 
                        (self.stats['cache_hits'] + 1)
                    )
                    self.stats['cache_hits'] += 1
                    
                    g_logger.debug(f"预加载音频成功: {file_path} (加载时间: {load_time:.3f}s)")
                    return True
                else:
                    g_logger.error(f"音频文件不存在: {file_path}")
                    self.stats['cache_misses'] += 1
                    return False
                
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
                    media_content = self._preloaded_sounds[cache_key]
                    self.media_player.setMedia(media_content)
                else:
                    # 直接加载文件
                    url = QUrl.fromLocalFile(file_path)
                    media_content = QMediaContent(url)
                    self.media_player.setMedia(media_content)
                
                # 设置音量
                self.set_volume(self._volume)
                
                # 开始播放
                self.media_player.play()
                
                # Qt的QMediaPlayer不支持loops参数，但可以通过信号重新播放
                # 这里简化处理，只播放一次
                
                # 等待播放完成
                self._wait_for_playback_complete()
                
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
        # Qt的QMediaPlayer不支持叠加播放，需要创建多个实例
        # 这里简化处理，创建一个新的播放器实例
        try:
            if not os.path.exists(file_path):
                return False
            
            effect_player = QMediaPlayer()
            url = QUrl.fromLocalFile(file_path)
            media_content = QMediaContent(url)
            effect_player.setMedia(media_content)
            effect_player.setVolume(int(volume * self._volume * 100))
            effect_player.play()
            
            # 播放完成后自动清理
            def cleanup_effect():
                effect_player.stop()
                effect_player.deleteLater()
            
            effect_player.stateChanged.connect(
                lambda state: cleanup_effect() if state == QMediaPlayer.StoppedState else None
            )
            
            return True
            
        except Exception as e:
            g_logger.error(f"播放音效失败 {file_path}: {e}")
            return False
    
    def stop(self):
        """停止当前播放"""
        with self._lock:
            try:
                if self.initialized and self.media_player:
                    self.media_player.stop()
                    self.media_player.setMedia(QMediaContent())
                
                if self._playback_timer:
                    self._playback_timer.stop()
                
                self._current_file = None
                self._is_paused = False
                
                g_logger.debug("音频播放已停止")
                
            except Exception as e:
                g_logger.error(f"停止音频播放失败: {e}")
    
    def pause(self):
        """暂停播放"""
        with self._lock:
            if self.initialized and self.media_player and not self._is_paused:
                try:
                    self.media_player.pause()
                    self._is_paused = True
                    g_logger.debug("音频播放已暂停")
                    
                except Exception as e:
                    g_logger.error(f"暂停音频播放失败: {e}")
    
    def resume(self):
        """恢复播放"""
        with self._lock:
            if self.initialized and self.media_player and self._is_paused:
                try:
                    self.media_player.play()
                    self._is_paused = False
                    g_logger.debug("音频播放已恢复")
                    
                except Exception as e:
                    g_logger.error(f"恢复音频播放失败: {e}")
    
    def set_volume(self, volume: float):
        """设置音量 (0.0 - 1.0)"""
        with self._lock:
            self._volume = max(0.0, min(1.0, volume))
            
            if self.initialized and self.media_player:
                # Qt的音量范围是0-100
                qt_volume = int(self._volume * 100)
                self.media_player.setVolume(qt_volume)
    
    def get_volume(self) -> float:
        """获取当前音量"""
        return self._volume
    
    def is_playing(self) -> bool:
        """检查是否正在播放"""
        if not self.initialized or not self.media_player:
            return False
        
        try:
            return self.media_player.state() == QMediaPlayer.PlayingState
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
                'available': self.media_player is not None and self.media_player.isAvailable(),
                'supported_formats': ['mp3', 'wav', 'ogg', 'm4a'],  # Qt支持的常见格式
            }
            
            return info
            
        except Exception as e:
            g_logger.error(f"获取音频设备信息失败: {e}")
            return {}
    
    def _wait_for_playback_complete(self):
        """等待播放完成"""
        try:
            if self.media_player:
                # 使用定时器检查播放状态
                while self.media_player.state() == QMediaPlayer.PlayingState:
                    if self._is_paused:
                        time.sleep(0.01)
                        continue
                    
                    if not self._current_file:  # 被停止了
                        break
                    
                    time.sleep(0.01)
                    
        except Exception as e:
            g_logger.error(f"等待播放完成失败: {e}")
    
    def _on_state_changed(self, state):
        """媒体播放器状态变化回调"""
        try:
            if state == QMediaPlayer.StoppedState:
                self._current_file = None
                self._is_paused = False
                self.playback_finished.emit()
            elif state == QMediaPlayer.PausedState:
                self._is_paused = True
            elif state == QMediaPlayer.PlayingState:
                self._is_paused = False
                
        except Exception as e:
            g_logger.error(f"处理播放器状态变化失败: {e}")
    
    def _on_error(self):
        """媒体播放器错误回调"""
        try:
            if self.media_player:
                error_string = self.media_player.errorString()
                g_logger.error(f"媒体播放器错误: {error_string}")
                self.error_occurred.emit(error_string)
                
        except Exception as e:
            g_logger.error(f"处理播放器错误失败: {e}")
    
    def _on_position_changed(self, position):
        """播放位置变化回调"""
        # 可以用于实现进度显示等功能
        pass
    
    def _on_duration_changed(self, duration):
        """音频时长变化回调"""
        # 可以用于显示音频总时长
        pass
    
    def _check_playback_finished(self):
        """检查播放是否完成"""
        if self.media_player and self.media_player.state() == QMediaPlayer.StoppedState:
            self.playback_finished.emit()


# 全局Qt音频播放器实例
qt_audio_player = None

def get_qt_audio_player() -> QtAudioPlayer:
    """获取全局Qt音频播放器实例"""
    global qt_audio_player
    if qt_audio_player is None:
        qt_audio_player = QtAudioPlayer()
    return qt_audio_player


# 兼容性函数，保持与原有pygame音频播放器的接口一致
def get_audio_player() -> QtAudioPlayer:
    """获取音频播放器实例（兼容性函数）"""
    return get_qt_audio_player()