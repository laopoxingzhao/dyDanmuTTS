import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, 
                             QListWidget, QSplitter, QLineEdit, QCheckBox, QGroupBox, QGridLayout)
from PyQt5.QtCore import Qt, pyqtSignal
from threading import Thread
import time


class DanmuDisplayWindow(QMainWindow):
    # 定义信号，用于在不同线程间传递消息
    danmu_received = pyqtSignal(dict)
    stats_updated = pyqtSignal(dict)
    
    def __init__(self, room_id):
        super().__init__()
        self.room_id = room_id
        self.init_ui()
        # 连接信号到处理函数
        self.danmu_received.connect(self.display_danmu)
        self.stats_updated.connect(self.update_stats)
        
    def init_ui(self):
        # 设置窗口属性
        self.setWindowTitle(f"抖音直播间弹幕监控 - 房间ID: {self.room_id}")
        self.setGeometry(100, 100, 1000, 700)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # 顶部信息栏
        top_layout = QHBoxLayout()
        
        # 房间信息
        room_label = QLabel(f"直播间ID: {self.room_id}")
        room_label.setStyleSheet("font-weight: bold;")
        top_layout.addWidget(room_label)
        
        # 分割线
        separator = QLabel("|")
        top_layout.addWidget(separator)
        
        # 在线人数统计
        self.viewer_count_label = QLabel("在线人数: --")
        top_layout.addWidget(self.viewer_count_label)
        
        # 总观看人数统计
        self.total_viewer_count_label = QLabel("总观看人数: --")
        top_layout.addWidget(self.total_viewer_count_label)
        
        # 分割线
        separator2 = QLabel("|")
        top_layout.addWidget(separator2)
        
        # 点赞数
        self.like_count_label = QLabel("点赞数: 0")
        top_layout.addWidget(self.like_count_label)
        
        top_layout.addStretch()  # 添加弹性空间
        
        # 停止按钮
        self.stop_button = QPushButton("停止监控")
        self.stop_button.clicked.connect(self.stop_monitoring)
        top_layout.addWidget(self.stop_button)
        
        main_layout.addLayout(top_layout)
        
        # 创建分割器用于分隔不同类型的弹幕
        splitter = QSplitter(Qt.Horizontal)
        
        # 全部弹幕区域
        all_danmu_widget = QWidget()
        all_danmu_layout = QVBoxLayout()
        all_danmu_widget.setLayout(all_danmu_layout)
        
        all_danmu_label = QLabel("全部弹幕")
        all_danmu_label.setAlignment(Qt.AlignCenter)
        all_danmu_label.setStyleSheet("font-weight: bold; background-color: #f0f0f0;")
        all_danmu_layout.addWidget(all_danmu_label)
        
        self.all_danmu_list = QListWidget()
        all_danmu_layout.addWidget(self.all_danmu_list)
        
        # 特殊消息区域
        special_danmu_widget = QWidget()
        special_danmu_layout = QVBoxLayout()
        special_danmu_widget.setLayout(special_danmu_layout)
        
        special_danmu_label = QLabel("特殊消息")
        special_danmu_label.setAlignment(Qt.AlignCenter)
        special_danmu_label.setStyleSheet("font-weight: bold; background-color: #f0f0f0;")
        special_danmu_layout.addWidget(special_danmu_label)
        
        self.special_danmu_list = QListWidget()
        special_danmu_layout.addWidget(self.special_danmu_list)
        
        # 添加部件到分割器
        splitter.addWidget(all_danmu_widget)
        splitter.addWidget(special_danmu_widget)
        splitter.setSizes([600, 400])  # 设置初始大小
        
        main_layout.addWidget(splitter)
        
        # 底部控制区域
        bottom_layout = QHBoxLayout()
        
        # 消息类型过滤 - 使用复选框组
        filter_group = QGroupBox("消息类型过滤")
        filter_layout = QGridLayout()
        
        # 创建复选框
        self.chat_checkbox = QCheckBox("聊天")
        self.enter_checkbox = QCheckBox("进场")
        self.like_checkbox = QCheckBox("点赞")
        self.gift_checkbox = QCheckBox("礼物")
        self.follow_checkbox = QCheckBox("关注")
        self.share_checkbox = QCheckBox("分享")
        self.stat_checkbox = QCheckBox("统计")
        
        # 默认全部选中
        self.chat_checkbox.setChecked(True)
        self.enter_checkbox.setChecked(True)
        self.like_checkbox.setChecked(True)
        self.gift_checkbox.setChecked(True)
        self.follow_checkbox.setChecked(True)
        self.share_checkbox.setChecked(True)
        self.stat_checkbox.setChecked(True)
        
        # 添加到布局
        filter_layout.addWidget(self.chat_checkbox, 0, 0)
        filter_layout.addWidget(self.enter_checkbox, 0, 1)
        filter_layout.addWidget(self.like_checkbox, 0, 2)
        filter_layout.addWidget(self.gift_checkbox, 1, 0)
        filter_layout.addWidget(self.follow_checkbox, 1, 1)
        filter_layout.addWidget(self.share_checkbox, 1, 2)
        filter_layout.addWidget(self.stat_checkbox, 2, 0)
        
        filter_group.setLayout(filter_layout)
        bottom_layout.addWidget(filter_group)
        
        # 关键词过滤
        keyword_layout = QVBoxLayout()
        keyword_label = QLabel("关键词过滤:")
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("输入关键词进行过滤")
        keyword_layout.addWidget(keyword_label)
        keyword_layout.addWidget(self.keyword_input)
        bottom_layout.addLayout(keyword_layout)
        
        # 清屏按钮
        self.clear_button = QPushButton("清屏")
        self.clear_button.clicked.connect(self.clear_screen)
        bottom_layout.addWidget(self.clear_button)
        
        main_layout.addLayout(bottom_layout)
        
        # 连接信号
        self.stop_button.clicked.connect(self.stop_monitoring)
        # 连接所有复选框的状态变化信号
        self.chat_checkbox.stateChanged.connect(self.filter_messages)
        self.enter_checkbox.stateChanged.connect(self.filter_messages)
        self.like_checkbox.stateChanged.connect(self.filter_messages)
        self.gift_checkbox.stateChanged.connect(self.filter_messages)
        self.follow_checkbox.stateChanged.connect(self.filter_messages)
        self.share_checkbox.stateChanged.connect(self.filter_messages)
        self.stat_checkbox.stateChanged.connect(self.filter_messages)
        self.keyword_input.textChanged.connect(self.filter_messages)
        
    def display_danmu(self, danmu_data):
        """显示弹幕信息"""
        # 获取弹幕类型和内容
        msg_type = danmu_data.get('type', 'unknown')
        payload = danmu_data.get('payload', {})
        
        # 如果是统计信息，只更新统计数据，不显示在弹幕列表中
        if msg_type == 'stat':
            self.update_stats(payload)
            return
        
        # 构造显示文本
        display_text = self.format_danmu_message(msg_type, payload)
        
        # 检查对应类型的复选框是否被选中
        type_checkbox_map = {
            "chat": self.chat_checkbox,
            "enter": self.enter_checkbox,
            "like": self.like_checkbox,
            "gift": self.gift_checkbox,
            "follow": self.follow_checkbox,
            "share": self.share_checkbox
        }
        
        # 如果对应类型的复选框未选中，则不显示
        if msg_type in type_checkbox_map and not type_checkbox_map[msg_type].isChecked():
            return
                
        # 关键词过滤
        keyword = self.keyword_input.text().strip()
        if keyword and keyword not in display_text:
            return
        
        # 添加到全部弹幕列表
        self.all_danmu_list.addItem(display_text)
        self.all_danmu_list.scrollToBottom()
        
        # 如果是特殊消息，也添加到特殊消息列表
        if msg_type in ['gift', 'follow', 'share']:
            special_text = f"[{msg_type.upper()}] {display_text}"
            self.special_danmu_list.addItem(special_text)
            self.special_danmu_list.scrollToBottom()
            
    def format_danmu_message(self, msg_type, payload):
        """格式化弹幕消息"""
        if msg_type == 'chat':
            user = payload.get('user', '未知用户')
            content = payload.get('content', '')
            return f"[聊天] {user}: {content}"
        elif msg_type == 'enter':
            user = payload.get('user', '未知用户')
            return f"[进场] {user} 进入直播间"
        elif msg_type == 'like':
            user = payload.get('user', '未知用户')
            count = payload.get('count', 1)
            return f"[点赞] {user} 点了{count}个赞"
        elif msg_type == 'gift':
            user = payload.get('user', '未知用户')
            gift_name = payload.get('gift_name', '未知礼物')
            gift_cnt = payload.get('gift_cnt', 1)
            return f"[礼物] {user} 送出 {gift_name} x{gift_cnt}"
        elif msg_type == 'follow':
            user = payload.get('user', '未知用户')
            return f"[关注] {user} 关注了主播"
        elif msg_type == 'share':
            user = payload.get('user', '未知用户')
            return f"[分享] {user} 分享了直播间"
        elif msg_type == 'stat':
            # 统计信息不在此处显示，而是更新统计标签
            return ""
        else:
            return f"[{msg_type}] {payload}"
            
    def update_stats(self, stats_data):
        """更新统计数据"""
        viewer_count = stats_data.get('viewer_count', '--')
        total_viewer_count = stats_data.get('total_viewer_count', '--')
        like_count = stats_data.get('like_count', 0)
        
        self.viewer_count_label.setText(f"在线人数: {viewer_count}")
        self.total_viewer_count_label.setText(f"总观看人数: {total_viewer_count}")
        self.like_count_label.setText(f"点赞数: {like_count}")
        
    def filter_messages(self):
        """根据条件过滤消息"""
        # 这里可以实现更复杂的消息过滤逻辑
        pass
        
    def clear_screen(self):
        """清屏"""
        self.all_danmu_list.clear()
        self.special_danmu_list.clear()
        
    def stop_monitoring(self):
        """停止监控"""
        # 发送停止信号
        self.stop_requested = True
        self.close()
        
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.stop_monitoring()
        event.accept()


def main():
    """主函数 - 演示UI使用"""
    app = QApplication(sys.argv)
    window = DanmuDisplayWindow("123456789")
    window.show()
    
    # 模拟一些测试数据
    def simulate_danmu():
        test_messages = [
            {'type': 'enter', 'payload': {'user': '用户A'}},
            {'type': 'chat', 'payload': {'user': '用户B', 'content': '主播好厉害！'}},
            {'type': 'like', 'payload': {'user': '用户C', 'count': 5}},
            {'type': 'gift', 'payload': {'user': '用户D', 'gift_name': '小心心', 'gift_cnt': 1}},
            {'type': 'follow', 'payload': {'user': '用户E'}},
            {'type': 'share', 'payload': {'user': '用户F'}}
        ]
        
        for msg in test_messages:
            time.sleep(1)
            window.danmu_received.emit(msg)
            
        # 发送统计数据
        stats = {'viewer_count': 123, 'total_viewer_count': 456, 'like_count': 789}
        window.stats_updated.emit(stats)
    
    # 在后台线程中模拟弹幕数据
    thread = Thread(target=simulate_danmu)
    thread.daemon = True
    thread.start()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()