from threading import Thread
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from config.config import config_manager
import queue
from config.log import g_logger
from dy_danmu.liveMan import DouyinLiveWebFetcher
import time
from typing import Dict, Optional
from tts.tts_controller import TTSController

checkbox_labels = {
    'WebcastChatMessage': '聊天消息',
    'WebcastGiftMessage': '礼物消息',
    'WebcastLikeMessage': '点赞消息',
    'WebcastMemberMessage': '进入消息',
    'WebcastSocialMessage': '关注',
    'WebcastFansclubMessage': '粉丝团消息',
    'WebcastEmojiChatMessage': '聊天表情包消息',
    'WebcastRoomStatsMessage': '直播间统计信息',
    'WebcastRoomUserSeqMessage': '直播间统计',
    'WebcastRoomMessage': '直播间信息',
    'WebcastRoomRankMessage': '直播间排行榜信息',
    'WebcastRoomStreamAdaptationMessage': '直播间流配置',
}


class OptimizedDanmuController:
    """优化的弹幕控制器"""
    
    room_id = None
    
    def __init__(self):
        super().__init__()
        # 使用全局配置管理器
        self.config_manager = config_manager

        self.dy_fetcher = None
        self.dy_fetcher_thread = None
        
        # 弹幕队列
        self.danmu_queue = queue.Queue()
        
        # TTS控制器
        self.tts_controller = None
        
        # 性能监控
        self.performance_stats = {
            'start_time': time.time(),
            'total_messages': 0,
            'filtered_messages': 0,
            'last_update': time.time()
        }
    
    def start(self, room_id):
        """启动弹幕控制器"""
        self.cleanup()
        """启动弹幕控制器"""
        self.room_id = room_id
        g_logger.info(f"启动优化的弹幕控制器，房间ID：{room_id}")
        
        # 重置统计
        self.performance_stats = {
            'start_time': time.time(),
            'total_messages': 0,
            'filtered_messages': 0,
            'last_update': time.time()
        }
        
        # 启动抖音直播抓取器
        self.dy_fetcher = DouyinLiveWebFetcher(room_id)
        self.dy_fetcher.fn_ptr = self.add_danmu
        
        # 启动抓取线程
        self.dy_fetcher_thread = Thread(target=self.dy_fetcher.start)
        self.dy_fetcher_thread.start()
        
        # 启动TTS控制器
        self._start_tts_controller()
        
    
    def add_danmu(self, method, danmu):
        """添加弹幕"""
        try:
            # 更新统计
            self.performance_stats['total_messages'] += 1
            
            if self.is_message_type_enabled(method):
                # 添加到基础队列
                self.danmu_queue.put((method, danmu))
                g_logger.debug(f"添加到队列: {method}---{danmu}")
                
                # 添加到TTS处理
                if self.tts_controller and self.config_manager.tts_settings.enabled:
                    self.tts_controller.add_danmu(danmu, method)
            else:
                self.performance_stats['filtered_messages'] += 1
                
        except Exception as e:
            g_logger.error(f"添加弹幕失败: {e}")
    
    def is_message_type_enabled(self, message_type):
        """检查消息类型是否在配置中启用"""
        config_key = self.get_config_key_for_message_type(message_type)
        if config_key:
            danmu_settings = self.config_manager.danmu_settings
            return getattr(danmu_settings, config_key, True)
        return False

    def get_config_key_for_message_type(self, message_type):
        """获取消息类型对应的配置键名"""
        type_mapping = {
            'WebcastChatMessage': 'WebcastChatMessage',
            'WebcastGiftMessage': 'WebcastGiftMessage',
            'WebcastLikeMessage': 'WebcastLikeMessage',
            'WebcastMemberMessage': 'WebcastMemberMessage',
            'WebcastSocialMessage': 'WebcastSocialMessage',
            'WebcastFansclubMessage': 'WebcastFansclubMessage',
            'WebcastEmojiChatMessage': 'WebcastEmojiChatMessage',
            'WebcastRoomStatsMessage': 'WebcastRoomStatsMessage',
            'WebcastRoomUserSeqMessage': 'WebcastRoomUserSeqMessage',
            'WebcastRoomMessage': 'WebcastRoomMessage',
            'WebcastRoomRankMessage': 'WebcastRoomRankMessage',
            'WebcastRoomStreamAdaptationMessage': 'WebcastRoomStreamAdaptationMessage'
        }
        return type_mapping.get(message_type)

    def cleanup(self):
        """清理资源"""
        g_logger.info("开始清理弹幕控制器资源...")
        
        # 停止TTS控制器
        self._stop_tts_controller()
        
        # 停止弹幕获取线程
        if self.dy_fetcher and hasattr(self.dy_fetcher, 'stop'):
            self.dy_fetcher.stop()
        
        # 清空队列
        with self.danmu_queue.mutex:
            self.danmu_queue.queue.clear()
        
        g_logger.info("弹幕控制器资源清理完成")
    
    def _start_tts_controller(self):
        """启动TTS控制器"""
        try:
            if self.tts_controller is None:
                # 获取TTS配置
                tts_config = {
                    'voice': self.config_manager.tts_settings.voice,
                    'rate': self.config_manager.tts_settings.rate,
                    'volume': self.config_manager.tts_settings.volume,
                    'playback_volume': self.config_manager.tts_settings.playback_volume,
                    'play_interval': self.config_manager.tts_settings.play_interval,
                    'max_queue_size': self.config_manager.tts_settings.max_queue_size,
                    'cache_dir': self.config_manager.tts_settings.cache_dir,
                    'cache_max_age': self.config_manager.tts_settings.cache_max_age,
                    'cache_max_size_mb': self.config_manager.tts_settings.cache_max_size_mb,
                    'enable_cache': self.config_manager.tts_settings.enable_cache,
                    'event_announcement': self.config_manager.tts_settings.event_announcement,
                    'keyword_rules': self.config_manager.tts_settings.keyword_rules
                }
                
                self.tts_controller = TTSController(tts_config)
                self.tts_controller.start()
                
                g_logger.info("TTS控制器已启动")
        except Exception as e:
            g_logger.error(f"启动TTS控制器失败: {e}")
    
    def _stop_tts_controller(self):
        """停止TTS控制器"""
        try:
            if self.tts_controller:
                self.tts_controller.stop()
                self.tts_controller = None
                g_logger.info("TTS控制器已停止")
        except Exception as e:
            g_logger.error(f"停止TTS控制器失败: {e}")
    
    def update_tts_config(self, config: Dict):
        """更新TTS配置"""
        if self.tts_controller:
            self.tts_controller.update_config(config)
            g_logger.info("TTS配置已更新")
    
    def get_tts_controller(self) -> Optional[TTSController]:
        """获取TTS控制器实例"""
        return self.tts_controller
    
    def get_danmu(self):
        """获取弹幕"""
        if self.danmu_queue.empty():
            return None, None
        else:
            return self.danmu_queue.get()

    
    def get_performance_stats(self) -> Dict:
        """获取性能统计信息"""
        current_time = time.time()
        runtime = current_time - self.performance_stats['start_time']
        
        stats = {
            'runtime_seconds': runtime,
            'total_messages': self.performance_stats['total_messages'],
            'filtered_messages': self.performance_stats['filtered_messages'],
            'messages_per_second': self.performance_stats['total_messages'] / max(runtime, 1),
            'filter_rate': self.performance_stats['filtered_messages'] / max(self.performance_stats['total_messages'], 1),
        }
        
        return stats
    
    def get_queue_status(self) -> Dict:
        """获取队列状态信息"""
        status = {
            'danmu_queue_size': self.danmu_queue.qsize(),
        }
        
        return status
    