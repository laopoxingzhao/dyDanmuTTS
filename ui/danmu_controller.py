from threading import Thread
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from config.config import config_manager
import queue
from config.log import g_logger
from dy_danmu.liveMan import DouyinLiveWebFetcher
from tool.myqueue import ttsq
from tts.tts_handler import init_tts_handler
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

        self.dy_fetcher = None
        self.dy_fetcher_thread = None
        # TTS队列引用
        self.tts_queue = ttsq
        self.danmu_queue = queue.Queue()
        
        # 初始化TTS处理器
        self.tts_handler = init_tts_handler(self.config_manager)
    
    def start(self, room_id):
        """初始化弹幕控制器"""
        self.cleanup()
        """启动弹幕控制器"""
        self.room_id = room_id
        g_logger.info(f"启动弹幕控制器，房间ID：{room_id}")
        self.dy_fetcher = DouyinLiveWebFetcher(room_id)

        self.dy_fetcher.fn_ptr = self.add_danmu
        #new  thread start
        self.dy_fetcher_thread = Thread(target=self.dy_fetcher.start)
        # self.dy_fetcher_thread.daemon = True
        self.dy_fetcher_thread.start()
        
        # 启动TTS处理器
        if self.tts_handler:
            self.tts_handler.start()
            g_logger.info("TTS处理器已启动")
       
    
    def add_danmu(self, method, danmu):
        """添加弹幕，根据配置过滤和分发到不同队列"""
        if self.is_message_type_enabled(method):
            # 获取配置信息
            danmu_settings = self.config_manager.danmu_settings
            tts_settings = self.config_manager.tts_settings
            
            # 添加到基础队列（保持原有功能）
            self.danmu_queue.put((method, danmu))
            g_logger.debug(f"添加到基础队列: {method}---{danmu}")
            
            # 根据TTS配置决定是否添加到TTS队列
            if tts_settings.tts_enabled and self._should_add_to_tts_queue(method, tts_settings):
                self._add_to_tts_queue(method, danmu)
        
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
        # 停止弹幕获取线程
        if self.dy_fetcher and hasattr(self.dy_fetcher, 'stop'):
            self.dy_fetcher.stop()
        
        # 停止TTS处理器
        if self.tts_handler:
            self.tts_handler.stop()
            g_logger.info("TTS处理器已停止")
        
        # 清空队列
        with self.danmu_queue.mutex:
            self.danmu_queue.queue.clear()
    
    def get_danmu(self):
        """获取弹幕"""
        if self.danmu_queue.empty():
            return None, None
        else:
            return self.danmu_queue.get()

    def _should_add_to_tts_queue(self, method, tts_settings):
        """检查是否应该添加到TTS队列"""
        # 检查消息类型是否在TTS配置中启用
        tts_enabled_mapping = {
            'WebcastChatMessage': 'chat_tts',
            'WebcastGiftMessage': 'gift_tts',
            'WebcastLikeMessage': 'like_tts',
            'WebcastMemberMessage': 'member_tts',
            'WebcastSocialMessage': 'social_tts',
            'WebcastFansclubMessage': 'fansclub_tts'
        }
        
        tts_key = tts_enabled_mapping.get(method)
        if tts_key:
            return getattr(tts_settings, tts_key, True)
        return False

    def _add_to_tts_queue(self, method, danmu):
        """添加消息到TTS队列"""
        try:
            # 根据消息类型生成TTS文本
            tts_text = self._generate_tts_text(method, danmu)
            if tts_text:
                # 使用正确的TTS队列put方法参数
                self.tts_queue.put(method, tts_text)
                g_logger.debug(f"添加到TTS队列: {tts_text}")
        except Exception as e:
            g_logger.error(f"添加TTS消息失败: {e}")

    def _generate_tts_text(self, method, danmu):
        """生成TTS文本"""
        if method == 'WebcastChatMessage':
            return f"用户{danmu.get('user_name', '未知用户')}说：{danmu.get('content', '')}"
        elif method == 'WebcastGiftMessage':
            return f"用户{danmu.get('user_name', '未知用户')}赠送了{danmu.get('gift_name', '礼物')}"
        elif method == 'WebcastLikeMessage':
            return f"用户{danmu.get('user_name', '未知用户')}点赞了"
        elif method == 'WebcastMemberMessage':
            return f"用户{danmu.get('user_name', '未知用户')}进入了直播间"
        elif method == 'WebcastSocialMessage':
            return f"用户{danmu.get('user_name', '未知用户')}关注了主播"
        elif method == 'WebcastFansclubMessage':
            content = danmu.get('content', '').strip()
            if content:
                return f"粉丝团消息：{content}"
            else:
                return "有用户加入了粉丝团"
        return None

