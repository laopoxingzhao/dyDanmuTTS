import sys
import random
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QListWidget, QPushButton, 
                             QSplitter, QTextEdit, QCheckBox,QTabWidget,QGroupBox)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor
import datetime
from tool.myqueue import uiq
checkbox_labels = {
                    'WebcastChatMessage':  '聊天消息',
                    'WebcastGiftMessage':   '礼物消息',
                    'WebcastLikeMessage':    '点赞消息',
                    'WebcastMemberMessage':   '进入消息',
                    'WebcastSocialMessage':'关注',
                    'WebcastFansclubMessage':   '粉丝团消息',
                    'WebcastEmojiChatMessage':    '聊天表情包消息',
                    # 'WebcastRoomStatsMessage':   '直播间统计信息',
                    #  'WebcastRoomUserSeqMessage':    '直播间统计',
                    # 'WebcastRoomMessage':   '直播间信息',
                    # 'WebcastRoomRankMessage':  '直播间排行榜信息',
                    # 'WebcastRoomStreamAdaptationMessage':  '直播间流配置',
        }
class RoomDanmuWindow(QMainWindow):
    # 定义信号，用于关闭窗口事件
    window_closed = pyqtSignal()
    add_danmuSign = pyqtSignal()
    
    def __init__(self, room_id):
        super().__init__()
        self.room_id = room_id
        self.danmu_counter = 0  # 弹幕计数器
        self.init_ui()
        self.setup_timers()  # 设置定时器
        
    def init_ui(self):
        # 设置窗口属性
        self.setWindowTitle(f"直播间 {self.room_id} 弹幕")
        self.setGeometry(100, 100, 900, 700)
        

        qtw = QTabWidget()
        
     
        # qtw.addTab(central_widget, "tts_config")
        self.setCentralWidget(qtw)
        

        # 创建中央部件
       
        self.danmugui(qtw)
        self.ttsPlayerConfigGui(qtw)

    def danmugui(self, qtw):
        central_widget = QWidget()
        qtw.addTab(central_widget, "弹幕")
        # 设置样式表
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QLabel {
                color: #333333;
                font-size: 14px;
            }
            QListWidget {
                background-color: white;
                border: 1px solid #cccccc;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
                selection-background-color: #d0e1ff;  /* 选择时的背景色 */
                selection-color: black;  /* 选择时的文字颜色 */
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #eeeeee;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
            QListWidget::item:selected {
                background-color: #d0e1ff;
                color: black;
            }
            QPushButton {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 8px 16px;
                text-align: center;
                font-size: 14px;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QCheckBox {
                spacing: 5px;
                font-size: 14px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #cccccc;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #4CAF50;
                border-radius: 3px;
                background-color: #4CAF50;
            }
        """)
      

        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        central_widget.setLayout(main_layout)
        
        # 添加标题
        title_label = QLabel(f"直播间 {self.room_id} 实时弹幕")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin: 10px;")
        main_layout.addWidget(title_label)
        
        # 添加第一排5个复选按钮
        checkbox_layout = QHBoxLayout()
        checkbox_layout.setSpacing(15)
        self.checkboxes = {}
     
        for key, label in checkbox_labels.items():
            checkbox = QCheckBox(label)
            checkbox.setChecked(True)  # 默认选中
            self.checkboxes[key] = checkbox
            checkbox_layout.addWidget(checkbox)
        checkbox_layout.addStretch()  # 添加弹性空间
        main_layout.addLayout(checkbox_layout)
        
        # 创建弹幕列表
        danmu_list_widget = QWidget()
        danmu_list_layout = QVBoxLayout()
        danmu_list_widget.setLayout(danmu_list_layout)
        
        danmu_label = QLabel("弹幕列表:")
        danmu_label.setStyleSheet("font-weight: bold; color: #2c3e50; margin-left: 5px;")
        danmu_list_layout.addWidget(danmu_label)
        
        self.danmu_list = QListWidget()
        self.danmu_list.setSelectionMode(QListWidget.SingleSelection)  # 设置为单选模式
        self.danmu_list.itemClicked.connect(self.on_item_clicked)
        danmu_list_layout.addWidget(self.danmu_list)
        
        main_layout.addWidget(danmu_list_widget)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 清空按钮
        self.clear_button = QPushButton("清空")
        self.clear_button.clicked.connect(self.clear_danmu)
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                border: none;
                color: white;
                padding: 8px 16px;
                text-align: center;
                font-size: 14px;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
        """)
        
        # 关闭按钮
        self.close_button = QPushButton("关闭")
        self.close_button.clicked.connect(self.close)
        
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()  # 添加弹性空间
        button_layout.addWidget(self.close_button)
        main_layout.addLayout(button_layout)



    # def ttsPlayerConfigGui(self,qtw):
    #     """设置TTS参数播放"""
    #     win = QWidget()
    #     layout = QVBoxLayout()
    #     # qtw.ad(layout)
    #     qtw.addTab(win,'配置')
    #     win.setLayout(layout)

    #     # TTS总开关
    #     self.tts_enabled = QCheckBox("启用TTS语音播报")
    #     layout.addWidget(self.tts_enabled)
        

    #     # 进场消息TTS
    #     enter_group = QGroupBox("用户进场TTS")
    #     enter_layout = QVBoxLayout()
    #     self.enter_tts_enabled = QCheckBox("启用进场TTS播报")
    #     enter_layout.addWidget(self.enter_tts_enabled)
    #     enter_group.setLayout(enter_layout)
    #     layout.addWidget(enter_group)
        


    def ttsPlayerConfigGui(self, qtw):
        """设置TTS参数播放"""
        win = QWidget()
        layout = QVBoxLayout()
        qtw.addTab(win, '配置')
        win.setLayout(layout)

        # 主标题
        title_label = QLabel("TTS语音播报配置")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin: 10px 0px;")
        layout.addWidget(title_label)

        # TTS总开关
        self.tts_enabled = QCheckBox("启用TTS语音播报")
        self.tts_enabled.setChecked(False)  # 默认关闭
        self.tts_enabled.setStyleSheet("""
            QCheckBox {
                font-size: 12px;
                padding: 8px;
                spacing: 10px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #cccccc;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #3498db;
                border-radius: 3px;
                background-color: #3498db;
            }
        """)
        layout.addWidget(self.tts_enabled)

        # 消息类型配置组
        msg_config_group = QGroupBox("消息类型语音播报配置")
        msg_config_layout = QVBoxLayout()
        msg_config_group.setLayout(msg_config_layout)
        layout.addWidget(msg_config_group)

        # 各种消息类型的TTS开关
        self.chat_tts_enabled = QCheckBox("聊天消息TTS播报")
        self.gift_tts_enabled = QCheckBox("礼物消息TTS播报")
        self.like_tts_enabled = QCheckBox("点赞消息TTS播报")
        self.member_tts_enabled = QCheckBox("用户进场TTS播报")
        self.social_tts_enabled = QCheckBox("关注消息TTS播报")
        self.fansclub_tts_enabled = QCheckBox("粉丝团消息TTS播报")
        self.emojichat_tts_enabled = QCheckBox("聊天表情包消息TTS播报")

        # 设置样式
        for checkbox in [self.chat_tts_enabled, self.gift_tts_enabled, self.like_tts_enabled,
                         self.member_tts_enabled, self.social_tts_enabled, self.fansclub_tts_enabled,
                         self.emojichat_tts_enabled]:
            checkbox.setStyleSheet("""
                QCheckBox {
                    font-size: 11px;
                    padding: 6px;
                    spacing: 8px;
                }
            """)
            checkbox.setChecked(False)  # 默认关闭
            msg_config_layout.addWidget(checkbox)

        # 音量控制
        volume_group = QGroupBox("音量设置")
        volume_layout = QVBoxLayout()
        volume_group.setLayout(volume_layout)
        layout.addWidget(volume_group)

        # 使用滑块控制音量
        from PyQt5.QtWidgets import QSlider, QHBoxLayout
        volume_label = QLabel("音量: 70%")
        volume_slider = QSlider(Qt.Horizontal)
        volume_slider.setMinimum(0)
        volume_slider.setMaximum(100)
        volume_slider.setValue(70)
        volume_slider.valueChanged.connect(lambda value: volume_label.setText(f"音量: {value}%"))

        volume_control_layout = QHBoxLayout()
        volume_control_layout.addWidget(volume_label)
        volume_control_layout.addWidget(volume_slider)
        volume_layout.addLayout(volume_control_layout)

        # 语音选择
        voice_group = QGroupBox("语音选择")
        voice_layout = QVBoxLayout()
        voice_group.setLayout(voice_layout)
        layout.addWidget(voice_group)

        from PyQt5.QtWidgets import QComboBox
        voice_label = QLabel("选择语音:")
        self.voice_combo = QComboBox()
        self.voice_combo.addItems(["普通话-女声", "普通话-男声", "粤语-女声", "粤语-男声", "英语-女声", "英语-男声"])
        self.voice_combo.setCurrentIndex(0)

        voice_layout.addWidget(voice_label)
        voice_layout.addWidget(self.voice_combo)

        # 语速设置
        speed_group = QGroupBox("语速设置")
        speed_layout = QVBoxLayout()
        speed_group.setLayout(speed_layout)
        layout.addWidget(speed_group)

        speed_label = QLabel("语速: 1.0x")
        speed_slider = QSlider(Qt.Horizontal)
        speed_slider.setMinimum(5)
        speed_slider.setMaximum(20)
        speed_slider.setValue(10)  # 对应1.0x
        speed_slider.valueChanged.connect(lambda value: speed_label.setText(f"语速: {value/10.0}x"))

        speed_control_layout = QHBoxLayout()
        speed_control_layout.addWidget(speed_label)
        speed_control_layout.addWidget(speed_slider)
        speed_layout.addLayout(speed_control_layout)

        # 添加弹性空间
        layout.addStretch()
    def setup_timers(self):
        """设置所有定时器"""
        self.add_danmu_timer = QTimer(self)
        self.add_danmu_timer.timeout.connect(self.add_danmu)
        self.add_danmu_timer.start(500)
        
        # 设置清理弹幕的定时器，每5分钟清理一半旧数据
        self.clean_danmu_timer = QTimer(self)
        self.clean_danmu_timer.timeout.connect(self.clean_old_danmu)
        self.clean_danmu_timer.start(5 * 1000 * 60)  # 每5分钟触发一次 (5 * 60 * 1000 毫秒)

        self.add_danmuSign.connect(self.add_danmu)

    def add_danmu(self):
        """添加一条随机弹幕"""
    
        if not uiq.empty():
            for i in range(uiq.size()):
                d = uiq.queue.get()
                # self.checkboxes.get(d['type'])
                if self.checkboxes.get(d['type']) and self.checkboxes[d['type']].isChecked():   
                    self.danmu_list.addItem(str(d))
                    self.danmu_counter += 1
            #判断当前是否在最底部
            if self.danmu_list.verticalScrollBar().value() == self.danmu_list.verticalScrollBar().maximum():
               # 自动滚动到底部
                self.danmu_list.scrollToBottom()
        
    def clean_old_danmu(self):
        """清理一半的旧数据"""
        num_items = self.danmu_list.count()
        for i in range(num_items // 2):
            item = self.danmu_list.takeItem(0)
            del item
        self.danmu_counter = self.danmu_list.count()
    def on_item_clicked(self, item):
        """当列表项被点击时显示详细信息"""
        row = self.danmu_list.row(item)
        # 取消注释以下代码可以在控制台打印点击的项目信息
        # print(f"点击了第{row}行项目: {item.text()}")
        
    def clear_danmu(self):
        """清空弹幕列表"""
        self.danmu_list.clear()
        self.danmu_counter = 0  # 重置计数器
        
    def closeEvent(self, event):
        # self.clear_danmu()
        uiq.clear()
        """窗口关闭事件"""
        # 停止所有定时器
        if hasattr(self, 'add_danmu_timer'):
            self.add_danmu_timer.stop()
        if hasattr(self, 'clean_danmu_timer'):
            self.clean_danmu_timer.stop()
            
        # 清理列表中的所有项目
        self.danmu_list.clear()
        
        # 发射窗口关闭信号
        self.window_closed.emit()
        event.accept()


def main():
    """主函数 - 演示UI使用"""
    app = QApplication(sys.argv)
    window = RoomDanmuWindow("123456789")
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()