"""
音频播放器模块 - 使用PyQt5播放音频
"""
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl, QTimer, pyqtSignal, QObject
from typing import Optional
from config.log import g_logger


class AudioPlayer(QObject):
    """音频播放器"""
    
    # 信号定义
    playback_finished = pyqtSignal()  # 播放完成信号
    playback_error = pyqtSignal(str)   # 播放错误信号
    
    def __init__(self):
        super().__init__()
        self.player = QMediaPlayer()
        self.current_file = None
        self.is_playing = False
        self.min_play_interval = 0.5  # 最小播放间隔（秒）
        self.last_play_time = 0
        
        # 连接播放器信号
        self.player.stateChanged.connect(self._on_state_changed)
        self.player.error.connect(self._on_error)
    
    def play(self, file_path: str, wait: bool = False) -> bool:
        """
        播放音频文件
        
        Args:
            file_path: 音频文件路径
            wait: 是否等待播放完成
            
        Returns:
            bool: 是否成功开始播放
        """
        try:
            import time
            import os
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                g_logger.error(f"音频文件不存在: {file_path}")
                return False
            
            # 检查播放间隔
            current_time = time.time()
            if current_time - self.last_play_time < self.min_play_interval:
                g_logger.debug(f"播放间隔过短，跳过: {file_path}")
                return False
            
            # 设置媒体源
            url = QUrl.fromLocalFile(file_path)
            self.player.setMedia(QMediaContent(url))
            
            # 开始播放
            self.player.play()
            self.current_file = file_path
            self.is_playing = True
            self.last_play_time = current_time
            
            g_logger.debug(f"开始播放音频: {file_path}")
            
            # 如果需要等待播放完成
            if wait:
                self._wait_for_completion()
            
            return True
            
        except Exception as e:
            g_logger.error(f"播放音频失败: {file_path}, 错误: {e}")
            self.playback_error.emit(str(e))
            return False
    
    def stop(self):
        """停止播放"""
        if self.is_playing:
            self.player.stop()
            self.is_playing = False
            g_logger.debug("停止播放音频")
    
    def pause(self):
        """暂停播放"""
        if self.is_playing:
            self.player.pause()
            g_logger.debug("暂停播放音频")
    
    def resume(self):
        """恢复播放"""
        if self.current_file and not self.is_playing:
            self.player.play()
            self.is_playing = True
            g_logger.debug("恢复播放音频")
    
    def set_volume(self, volume: int):
        """
        设置音量
        
        Args:
            volume: 音量值 (0-100)
        """
        self.player.setVolume(volume)
        g_logger.debug(f"设置音量: {volume}")
    
    def get_volume(self) -> int:
        """获取当前音量"""
        return self.player.volume()
    
    def set_min_play_interval(self, interval: float):
        """
        设置最小播放间隔
        
        Args:
            interval: 间隔时间（秒）
        """
        self.min_play_interval = interval
        g_logger.debug(f"设置最小播放间隔: {interval}秒")
    
    def get_min_play_interval(self) -> float:
        """获取最小播放间隔"""
        return self.min_play_interval
    
    def get_state(self) -> str:
        """获取播放状态"""
        state = self.player.state()
        if state == QMediaPlayer.PlayingState:
            return "playing"
        elif state == QMediaPlayer.PausedState:
            return "paused"
        else:
            return "stopped"
    
    def _on_state_changed(self, state):
        """播放状态改变回调"""
        if state == QMediaPlayer.StoppedState:
            self.is_playing = False
            self.playback_finished.emit()
            g_logger.debug("播放完成")
    
    def _on_error(self, error):
        """播放错误回调"""
        error_str = self.player.errorString()
        g_logger.error(f"播放器错误: {error_str}")
        self.playback_error.emit(error_str)
    
    def _wait_for_completion(self, timeout: int = 30):
        """
        等待播放完成
        
        Args:
            timeout: 超时时间（秒）
        """
        import time
        start_time = time.time()
        
        while self.is_playing and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        if self.is_playing:
            g_logger.warning("播放超时，强制停止")
            self.stop()