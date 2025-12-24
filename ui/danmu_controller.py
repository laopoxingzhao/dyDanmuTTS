import sys
import random
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from config.config_manager import ConfigManager
from tool.myqueue import uiq, ttsq
from collections import deque
from config.log import g_logger
checkbox_labels = {
    'WebcastChatMessage': '聊天消息',
    'WebcastGiftMessage': '礼物消息',
    'WebcastLikeMessage': '点赞消息',
    'WebcastMemberMessage': '进入消息',
    'WebcastSocialMessage': '关注',
    'WebcastFansclubMessage': '粉丝团消息',
    'WebcastEmojiChatMessage': '聊天表情包消息',
    # 'WebcastRoomStatsMessage': '直播间统计信息',
    # 'WebcastRoomUserSeqMessage': '直播间统计',
    # 'WebcastRoomMessage': '直播间信息',
    # 'WebcastRoomRankMessage': '直播间排行榜信息',
    # 'WebcastRoomStreamAdaptationMessage': '直播间流配置',
}

class DanmuController:
    # 定义信号，用于关闭窗口事件
    window_closed = pyqtSignal()
    add_danmu_signal = pyqtSignal()
    
    def __init__(self, room_id):
        super().__init__()
        g_logger.debug(f"init room_id: {room_id}")
        self.room_id = room_id
        self.config_manager = ConfigManager()  # 初始化配置管理器
        self.danmu_counter = 0  # 弹幕计数器
        self.checkboxes = {}
        self.add_danmu_timer = None
        self.clean_danmu_timer = None
        self.danmu_list_widget = None  # 存储弹幕列表的引用
        self.setup_timers()  # 设置定时器
        
    def setup_timers(self):
        """设置所有定时器"""
        self.add_danmu_timer = QTimer()
        # 连接到内部方法，该方法将调用带参数的add_danmu方法
        self.add_danmu_timer.timeout.connect(self._process_add_danmu)
        self.add_danmu_timer.start(500)
        
        # 设置清理弹幕的定时器，每5分钟清理一半旧数据
        self.clean_danmu_timer = QTimer()
        self.clean_danmu_timer.timeout.connect(self._process_clean_old_danmu)
        self.clean_danmu_timer.start(5 * 1000 * 60)  # 每5分钟触发一次 (5 * 60 * 1000 毫秒)

        # self.add_danmu_signal.connect(self.add_danmu)

    def set_danmu_list_widget(self, danmu_list_widget):
        """设置弹幕列表控件的引用"""
        self.danmu_list_widget = danmu_list_widget

    def _process_add_danmu(self):
        """内部方法，用于定时器调用，不接受参数"""
        if self.danmu_list_widget:
            self.add_danmu(self.danmu_list_widget)

    def _process_clean_old_danmu(self):
        """内部方法，用于定时器调用，不接受参数"""
        if self.danmu_list_widget:
            self.clean_old_danmu(self.danmu_list_widget)

    def on_checkbox_state_changed(self, key, state):
        """当复选框状态改变时保存设置"""
        self.config_manager.set_config("danmu_settings", key, state == Qt.Checked)

    def add_danmu(self, danmu_list_widget):
        """添加一条弹幕到UI列表"""
        g_logger.debug(f"add_danmu: {uiq.size()}")
        if not uiq.empty():
            for i in range(uiq.size()):
                d = uiq.queue.get()
                # 直接添加到列表，过滤逻辑由UI层处理
                t = str(d)
                # print(t)
                danmu_list_widget.addItem(t)
                self.danmu_counter += 1

    def clean_old_danmu(self, danmu_list_widget):
        """清理一半的旧数据"""
        num_items = danmu_list_widget.count()
        for i in range(num_items // 2):
            item = danmu_list_widget.takeItem(0)
            del item
        self.danmu_counter = danmu_list_widget.count()

    def clear_danmu(self, danmu_list_widget):
        """清空弹幕列表"""
        danmu_list_widget.clear()
        self.danmu_counter = 0  # 重置计数器
        
    def cleanup(self):
        """清理资源"""
        uiq.clear()
        """窗口关闭事件"""
        # 停止所有定时器
        if self.add_danmu_timer:
            self.add_danmu_timer.stop()
        if self.clean_danmu_timer:
            self.clean_danmu_timer.stop()
            
        # 发射窗口关闭信号
        self.window_closed.emit()