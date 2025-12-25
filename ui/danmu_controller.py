from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from config.config import config_manager
import queue
from config.log import g_logger

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

class DanmuController:
     
    room_id = None
    
    def __init__(self):
        super().__init__()
        # 使用全局配置管理器
        self.config_manager = config_manager
        self.queue = queue.Queue()

    def add_danmu(self, method, danmu):
        """添加弹幕，根据配置过滤"""
        if self.is_message_type_enabled(method):
            self.queue.put((method, danmu))
        
    def is_message_type_enabled(self, message_type):
        """检查消息类型是否在配置中启用"""
        config_key = self.get_config_key_for_message_type(message_type)
        if config_key:
            danmu_settings = self.config_manager.get_app_config().danmu_settings
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
            'WebcastEmojiChatMessage': 'WebcastEmojiChatMessage'
        }
        return type_mapping.get(message_type)

    def cleanup(self):
        """清理资源"""
        with self.queue.mutex:
            self.queue.queue.clear()
    
    def get_danmu(self):
        """获取弹幕"""
        try:
            return self.queue.get_nowait()
        except queue.Empty:
            return None, None
    