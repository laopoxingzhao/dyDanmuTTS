import sys
import random
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QListWidget, QPushButton, 
                             QSplitter, QTextEdit, QCheckBox, QTabWidget, QGroupBox, 
                             QLineEdit, QSlider, QComboBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor
import datetime
from ui.danmu_controller import DanmuController, checkbox_labels
from ui.tts_controller import TTSController

class RoomDanmuWindow(QMainWindow):
    # 定义信号，用于关闭窗口事件
    window_closed = pyqtSignal()
    
    def __init__(self, room_id):
        super().__init__()
        self.room_id = room_id
        self.danmu_controller = DanmuController(room_id)
        self.tts_controller = TTSController()
        self.init_ui()
        
    def init_ui(self):
        # 设置窗口属性
        self.setWindowTitle(f"直播间 {self.room_id} 弹幕")
        self.setGeometry(100, 100, 900, 700)

        qtw = QTabWidget()
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
        
        # 添加第一排复选按钮
        checkbox_layout = QHBoxLayout()
        checkbox_layout.setSpacing(15)
        self.checkboxes = {}
     
        for key, label in checkbox_labels.items():
            checkbox = QCheckBox(label)
            # 从配置中加载弹幕显示设置
            checked = self.danmu_controller.config_manager.get_config("danmu_settings", key, True)
            checkbox.setChecked(checked)
            # 连接状态改变事件，保存设置
            checkbox.stateChanged.connect(lambda state, k=key: self.on_checkbox_state_changed(k, state))
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
        
        # 设置danmu_controller的弹幕列表控件引用
        self.danmu_controller.set_danmu_list_widget(self.danmu_list)
        
    def on_checkbox_state_changed(self, key, state):
        """当复选框状态改变时保存设置"""
        self.danmu_controller.on_checkbox_state_changed(key, state)

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
        # 从配置中加载TTS总开关状态
        tts_enabled = self.tts_controller.config_manager.get_config("tts_settings", "tts_enabled", False)
        self.tts_enabled.setChecked(tts_enabled)
        self.tts_enabled.stateChanged.connect(lambda state: self.tts_controller.config_manager.set_config("tts_settings", "tts_enabled", state == Qt.Checked))
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

        # 用户进入消息TTS配置
        enter_group = QGroupBox("用户进入消息TTS")
        enter_layout = QVBoxLayout()
        enter_group.setLayout(enter_layout)
        layout.addWidget(enter_group)

        self.enter_tts_enabled = QCheckBox("启用用户进入消息TTS")
        enter_enabled = self.tts_controller.config_manager.get_config("tts_settings", "enter_tts_enabled", False)
        self.enter_tts_enabled.setChecked(enter_enabled)
        self.enter_tts_enabled.stateChanged.connect(lambda state: self.tts_controller.config_manager.set_config("tts_settings", "enter_tts_enabled", state == Qt.Checked))
        enter_layout.addWidget(self.enter_tts_enabled)

        enter_template_label = QLabel("进入消息模板:")
        enter_layout.addWidget(enter_template_label)

        self.enter_template_text = QTextEdit()
        enter_templates = self.tts_controller.config_manager.get_config("tts_settings", "enter_tts_templates", ["欢迎{user_name}进入直播间"])
        self.enter_template_text.setPlainText("\n".join(enter_templates))
        self.enter_template_text.textChanged.connect(self.save_enter_templates)
        enter_layout.addWidget(self.enter_template_text)

        # 关注消息TTS配置
        follow_group = QGroupBox("关注消息TTS")
        follow_layout = QVBoxLayout()
        follow_group.setLayout(follow_layout)
        layout.addWidget(follow_group)

        self.follow_tts_enabled = QCheckBox("启用关注消息TTS")
        follow_enabled = self.tts_controller.config_manager.get_config("tts_settings", "follow_tts_enabled", False)
        self.follow_tts_enabled.setChecked(follow_enabled)
        self.follow_tts_enabled.stateChanged.connect(lambda state: self.tts_controller.config_manager.set_config("tts_settings", "follow_tts_enabled", state == Qt.Checked))
        follow_layout.addWidget(self.follow_tts_enabled)

        follow_template_label = QLabel("关注消息模板:")
        follow_layout.addWidget(follow_template_label)

        self.follow_template_text = QTextEdit()
        follow_templates = self.tts_controller.config_manager.get_config("tts_settings", "follow_tts_templates", ["感谢{user_name}的关注"])
        self.follow_template_text.setPlainText("\n".join(follow_templates))
        self.follow_template_text.textChanged.connect(self.save_follow_templates)
        follow_layout.addWidget(self.follow_template_text)

        # 礼物消息TTS配置
        gift_group = QGroupBox("礼物消息TTS")
        gift_layout = QVBoxLayout()
        gift_group.setLayout(gift_layout)
        layout.addWidget(gift_group)

        self.gift_tts_enabled = QCheckBox("启用礼物消息TTS")
        gift_enabled = self.tts_controller.config_manager.get_config("tts_settings", "gift_tts_enabled", False)
        self.gift_tts_enabled.setChecked(gift_enabled)
        self.gift_tts_enabled.stateChanged.connect(lambda state: self.tts_controller.config_manager.set_config("tts_settings", "gift_tts_enabled", state == Qt.Checked))
        gift_layout.addWidget(self.gift_tts_enabled)

        gift_template_label = QLabel("礼物消息模板:")
        gift_layout.addWidget(gift_template_label)

        self.gift_template_text = QTextEdit()
        gift_templates = self.tts_controller.config_manager.get_config("tts_settings", "gift_tts_templates", [
            "感谢{user_name}送出的{gift_name}",
            "{user_name}送出了礼物，感谢支持"
        ])
        self.gift_template_text.setPlainText("\n".join(gift_templates))
        self.gift_template_text.textChanged.connect(self.save_gift_templates)
        gift_layout.addWidget(self.gift_template_text)

        # 关键字回复TTS配置
        keyword_group = QGroupBox("关键字回复TTS")
        keyword_layout = QVBoxLayout()
        keyword_group.setLayout(keyword_layout)
        layout.addWidget(keyword_group)

        self.keyword_tts_enabled = QCheckBox("启用关键字回复TTS")
        keyword_enabled = self.tts_controller.config_manager.get_config("tts_settings", "keyword_tts_enabled", False)
        self.keyword_tts_enabled.setChecked(keyword_enabled)
        self.keyword_tts_enabled.stateChanged.connect(lambda state: self.tts_controller.config_manager.set_config("tts_settings", "keyword_tts_enabled", state == Qt.Checked))
        keyword_layout.addWidget(self.keyword_tts_enabled)

        keyword_template_label = QLabel("关键字回复模板 (格式: 关键字=模板1|模板2):")
        keyword_layout.addWidget(keyword_template_label)

        self.keyword_template_text = QTextEdit()
        keyword_templates = self.tts_controller.config_manager.get_config("tts_settings", "keyword_reply_templates", {
            "1": [
                "你好啊{user_name}",
                "欢迎来到直播间{user_name}"
            ],
            "问题": [
                "这是一个好问题",
                "让我想想怎么回答{user_name}"
            ],
            "帮助": [
                "有什么可以帮助你的吗"
            ]
        })
        
        # 格式化关键字模板为文本格式
        formatted_keywords = []
        for keyword, templates in keyword_templates.items():
            if isinstance(templates, list):
                formatted_keywords.append(f"{keyword}=" + "|".join(templates))
            else:
                formatted_keywords.append(f"{keyword}={templates}")
        self.keyword_template_text.setPlainText("\n".join(formatted_keywords))
        self.keyword_template_text.textChanged.connect(self.save_keyword_templates)
        keyword_layout.addWidget(self.keyword_template_text)

        # TTS队列设置
        tts_queue_group = QGroupBox("TTS队列设置")
        tts_queue_layout = QVBoxLayout()
        tts_queue_group.setLayout(tts_queue_layout)
        layout.addWidget(tts_queue_group)

        # 去重时间窗口设置
        dedup_layout = QHBoxLayout()
        dedup_label = QLabel("去重时间窗口(秒):")
        self.dedup_time_window = QLineEdit()
        dedup_time_value = self.tts_controller.config_manager.get_config("tts_settings", "tts_queue_settings.dedup_time_window", 30)
        self.dedup_time_window.setText(str(dedup_time_value))
        self.dedup_time_window.textChanged.connect(lambda text: self.update_tts_queue_config("dedup_time_window", int(text) if text.isdigit() else 30))
        dedup_layout.addWidget(dedup_label)
        dedup_layout.addWidget(self.dedup_time_window)
        tts_queue_layout.addLayout(dedup_layout)

        # 最小间隔设置
        interval_layout = QHBoxLayout()
        interval_label = QLabel("同类型消息最小间隔(秒):")
        self.min_interval = QLineEdit()
        interval_value = self.tts_controller.config_manager.get_config("tts_settings", "tts_queue_settings.min_interval", 5)
        self.min_interval.setText(str(interval_value))
        self.min_interval.textChanged.connect(lambda text: self.update_tts_queue_config("min_interval", int(text) if text.isdigit() else 5))
        interval_layout.addWidget(interval_label)
        interval_layout.addWidget(self.min_interval)
        tts_queue_layout.addLayout(interval_layout)

        # 最大队列长度设置
        queue_size_layout = QHBoxLayout()
        queue_size_label = QLabel("最大队列长度:")
        self.max_queue_size = QLineEdit()
        queue_size_value = self.tts_controller.config_manager.get_config("tts_settings", "tts_queue_settings.max_queue_size", 20)
        self.max_queue_size.setText(str(queue_size_value))
        self.max_queue_size.textChanged.connect(lambda text: self.update_tts_queue_config("max_queue_size", int(text) if text.isdigit() else 20))
        queue_size_layout.addWidget(queue_size_label)
        queue_size_layout.addWidget(self.max_queue_size)
        tts_queue_layout.addLayout(queue_size_layout)

        # 音量控制
        volume_group = QGroupBox("音量设置")
        volume_layout = QVBoxLayout()
        volume_group.setLayout(volume_layout)
        layout.addWidget(volume_group)

        # 使用滑块控制音量
        volume_label = QLabel(f"音量: {self.tts_controller.config_manager.get_config('tts_settings', 'volume', 70)}%")
        volume_slider = QSlider(Qt.Horizontal)
        volume_slider.setMinimum(0)
        volume_slider.setMaximum(100)
        # 从配置中加载音量值
        volume_value = self.tts_controller.config_manager.get_config("tts_settings", "volume", 70)
        volume_slider.setValue(volume_value)
        volume_slider.valueChanged.connect(lambda value: [volume_label.setText(f"音量: {value}%"), self.tts_controller.config_manager.set_config("tts_settings", "volume", value)])

        volume_control_layout = QHBoxLayout()
        volume_control_layout.addWidget(volume_label)
        volume_control_layout.addWidget(volume_slider)
        volume_layout.addLayout(volume_control_layout)

        # 语音选择
        voice_group = QGroupBox("语音选择")
        voice_layout = QVBoxLayout()
        voice_group.setLayout(voice_layout)
        layout.addWidget(voice_group)

        voice_label = QLabel("选择语音:")
        self.voice_combo = QComboBox()
        self.voice_combo.addItems(["普通话-女声", "普通话-男声", "粤语-女声", "粤语-男声", "英语-女声", "英语-男声"])
        # 从配置中加载语音选择
        voice_index = self.tts_controller.config_manager.get_config("tts_settings", "voice", 0)
        self.voice_combo.setCurrentIndex(voice_index)
        self.voice_combo.currentTextChanged.connect(lambda text: self.tts_controller.config_manager.set_config("tts_settings", "voice", self.voice_combo.currentIndex()))

        voice_layout.addWidget(voice_label)
        voice_layout.addWidget(self.voice_combo)

        # 语速设置
        speed_group = QGroupBox("语速设置")
        speed_layout = QVBoxLayout()
        speed_group.setLayout(speed_layout)
        layout.addWidget(speed_group)

        speed_value = self.tts_controller.config_manager.get_config("tts_settings", "speed", 10)
        speed_label = QLabel(f"语速: {speed_value/10.0}x")
        speed_slider = QSlider(Qt.Horizontal)
        speed_slider.setMinimum(5)
        speed_slider.setMaximum(20)
        speed_slider.setValue(speed_value)  # 对应1.0x
        speed_slider.valueChanged.connect(lambda value: [speed_label.setText(f"语速: {value/10.0}x"), self.tts_controller.config_manager.set_config("tts_settings", "speed", value)])

        speed_control_layout = QHBoxLayout()
        speed_control_layout.addWidget(speed_label)
        speed_control_layout.addWidget(speed_slider)
        speed_layout.addLayout(speed_control_layout)

        # 添加弹性空间
        layout.addStretch()

    def save_enter_templates(self):
        """保存进入消息模板"""
        self.tts_controller.save_enter_templates(self.enter_template_text)

    def save_follow_templates(self):
        """保存关注消息模板"""
        self.tts_controller.save_follow_templates(self.follow_template_text)

    def save_gift_templates(self):
        """保存礼物消息模板"""
        self.tts_controller.save_gift_templates(self.gift_template_text)

    def save_keyword_templates(self):
        """保存关键字回复模板"""
        self.tts_controller.save_keyword_templates(self.keyword_template_text)

    def update_tts_queue_config(self, key, value):
        """更新TTS队列配置"""
        self.tts_controller.update_tts_queue_config(key, value)

    def add_danmu(self):
        """添加弹幕到UI"""
        from tool.myqueue import uiq  # 导入队列
        
        if not uiq.empty():
            for i in range(uiq.size()):
                d = uiq.queue.get()
                
                # 检查是否应该显示此类型的消息
                msg_type = d.get('type', 'Unknown') if isinstance(d, dict) else 'Unknown'
                checkbox = self.checkboxes.get(msg_type)
                
                if checkbox and checkbox.isChecked():
                    # 根据Qt组件使用与类型安全规范，只添加字符串到列表
                    # 提取消息内容，而不是直接添加整个字典
                    if isinstance(d, dict):
                        # 从字典中提取内容，格式为 {'type': ..., 'content': ...}
                        content = d.get('content', str(d))
                        display_text = content
                    else:
                        display_text = str(d)
                    
                    self.danmu_list.addItem(display_text)
        
        # 判断当前是否在最底部
        if self.danmu_list.verticalScrollBar().value() == self.danmu_list.verticalScrollBar().maximum():
            # 自动滚动到底部
            self.danmu_list.scrollToBottom()

    def clean_old_danmu(self):
        """清理一半的旧数据"""
        self.danmu_controller.clean_old_danmu(self.danmu_list)

    def on_item_clicked(self, item):
        """当列表项被点击时显示详细信息"""
        pass
    def clear_danmu(self):
        """清空弹幕列表"""
        self.danmu_controller.clear_danmu(self.danmu_list)
        
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.danmu_controller.cleanup()
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