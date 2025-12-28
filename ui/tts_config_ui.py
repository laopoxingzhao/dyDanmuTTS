from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QCheckBox, QLabel, QSlider, QSpinBox, QTextEdit,
                             QPushButton, QFormLayout, QGridLayout, QScrollArea)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from config.config import config_manager
from config.log import g_logger
from tts.tts_handler import init_tts_handler

class TTSConfigPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.config_manager = config_manager
        self.tts_handler = None
        self.init_ui()
        self._init_tts_handler()
        
    def init_ui(self):
        """初始化TTS配置界面"""
        main_layout = QVBoxLayout()
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        # TTS总开关
        self.create_tts_master_switch(scroll_layout)
        
        # 消息类型TTS开关
        self.create_message_tts_switches(scroll_layout)
        
        # TTS音量、语速、声音设置
        self.create_tts_audio_settings(scroll_layout)
        
        # TTS模板设置
        self.create_tts_template_settings(scroll_layout)
        
        scroll_layout.addStretch()
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)
        
        # 加载当前配置
        self.load_config()
        
    def _init_tts_handler(self):
        """初始化TTS处理器引用"""
        try:
            self.tts_handler = init_tts_handler(self.config_manager)
        except Exception as e:
            g_logger.error(f"初始化TTS处理器引用失败: {e}")
        
    def create_tts_master_switch(self, parent_layout):
        """创建TTS总开关"""
        group = QGroupBox("TTS总开关")
        layout = QHBoxLayout()
        
        self.tts_enabled_checkbox = QCheckBox("启用TTS语音播报")
        self.tts_enabled_checkbox.stateChanged.connect(self.on_tts_master_changed)
        
        layout.addWidget(self.tts_enabled_checkbox)
        layout.addStretch()
        group.setLayout(layout)
        parent_layout.addWidget(group)
        
    def create_message_tts_switches(self, parent_layout):
        """创建消息类型TTS开关"""
        group = QGroupBox("消息类型TTS设置")
        layout = QGridLayout()
        
        # 消息类型TTS开关
        self.message_tts_checkboxes = {}
        message_types = [
            ('chat_tts', '聊天消息TTS'),
            ('gift_tts', '礼物消息TTS'),
            ('like_tts', '点赞消息TTS'),
            ('member_tts', '进入消息TTS'),
            ('social_tts', '关注消息TTS'),
            ('fansclub_tts', '粉丝团消息TTS'),
        ]
        
        for i, (key, label) in enumerate(message_types):
            checkbox = QCheckBox(label)
            checkbox.stateChanged.connect(lambda state, k=key: self.on_message_tts_changed(k, state))
            self.message_tts_checkboxes[key] = checkbox
            layout.addWidget(checkbox, i // 2, i % 2)
            
        group.setLayout(layout)
        parent_layout.addWidget(group)
        
    def create_tts_audio_settings(self, parent_layout):
        """创建TTS音频设置"""
        group = QGroupBox("TTS音频设置")
        layout = QFormLayout()
        
        # 音量设置
        volume_layout = QHBoxLayout()
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.valueChanged.connect(self.on_volume_changed)
        self.volume_label = QLabel("70")
        volume_layout.addWidget(self.volume_slider)
        volume_layout.addWidget(self.volume_label)
        layout.addRow("音量:", volume_layout)
        
        # 语速设置
        speed_layout = QHBoxLayout()
        self.speed_spinbox = QSpinBox()
        self.speed_spinbox.setRange(1, 20)
        self.speed_spinbox.valueChanged.connect(self.on_speed_changed)
        speed_layout.addWidget(self.speed_spinbox)
        layout.addRow("语速:", speed_layout)
        
        # 声音类型
        voice_layout = QHBoxLayout()
        self.voice_spinbox = QSpinBox()
        self.voice_spinbox.setRange(0, 10)
        self.voice_spinbox.valueChanged.connect(self.on_voice_changed)
        voice_layout.addWidget(self.voice_spinbox)
        layout.addRow("声音类型:", voice_layout)
        
        group.setLayout(layout)
        parent_layout.addWidget(group)
        
    def create_tts_template_settings(self, parent_layout):
        """创建TTS模板设置"""
        group = QGroupBox("TTS模板设置")
        layout = QVBoxLayout()
        
        # 进入消息模板
        enter_group = QGroupBox("进入消息模板")
        enter_layout = QVBoxLayout()
        self.enter_template_text = QTextEdit()
        self.enter_template_text.setMaximumHeight(80)
        self.enter_template_text.setPlaceholderText("每行一个模板，可用变量: {user_name}")
        enter_layout.addWidget(self.enter_template_text)
        
        enter_save_btn = QPushButton("保存进入模板")
        enter_save_btn.clicked.connect(self.save_enter_templates)
        enter_layout.addWidget(enter_save_btn)
        enter_group.setLayout(enter_layout)
        layout.addWidget(enter_group)
        
        # 关注消息模板
        follow_group = QGroupBox("关注消息模板")
        follow_layout = QVBoxLayout()
        self.follow_template_text = QTextEdit()
        self.follow_template_text.setMaximumHeight(80)
        self.follow_template_text.setPlaceholderText("每行一个模板，可用变量: {user_name}")
        follow_layout.addWidget(self.follow_template_text)
        
        follow_save_btn = QPushButton("保存关注模板")
        follow_save_btn.clicked.connect(self.save_follow_templates)
        follow_layout.addWidget(follow_save_btn)
        follow_group.setLayout(follow_layout)
        layout.addWidget(follow_group)
        
        # 礼物消息模板
        gift_group = QGroupBox("礼物消息模板")
        gift_layout = QVBoxLayout()
        self.gift_template_text = QTextEdit()
        self.gift_template_text.setMaximumHeight(80)
        self.gift_template_text.setPlaceholderText("每行一个模板，可用变量: {user_name}, {gift_name}")
        gift_layout.addWidget(self.gift_template_text)
        
        gift_save_btn = QPushButton("保存礼物模板")
        gift_save_btn.clicked.connect(self.save_gift_templates)
        gift_layout.addWidget(gift_save_btn)
        gift_group.setLayout(gift_layout)
        layout.addWidget(gift_group)
        
        # 关键词回复模板
        keyword_group = QGroupBox("关键词回复模板")
        keyword_layout = QVBoxLayout()
        self.keyword_template_text = QTextEdit()
        self.keyword_template_text.setMaximumHeight(100)
        self.keyword_template_text.setPlaceholderText("格式: 关键词=回复1|回复2\\n例如: 1=你好{user_name}|欢迎{user_name}")
        keyword_layout.addWidget(self.keyword_template_text)
        
        keyword_save_btn = QPushButton("保存关键词模板")
        keyword_save_btn.clicked.connect(self.save_keyword_templates)
        keyword_layout.addWidget(keyword_save_btn)
        keyword_group.setLayout(keyword_layout)
        layout.addWidget(keyword_group)
        
        group.setLayout(layout)
        parent_layout.addWidget(group)
        
    def load_config(self):
        """加载配置到界面"""
        try:
            tts_settings = self.config_manager.tts_settings
            
            # 加载TTS总开关
            self.tts_enabled_checkbox.setChecked(tts_settings.tts_enabled)
            
            # 加载消息类型TTS开关
            for key, checkbox in self.message_tts_checkboxes.items():
                if hasattr(tts_settings, key):
                    checkbox.setChecked(getattr(tts_settings, key))
            
            # 加载音频设置
            self.volume_slider.setValue(tts_settings.volume)
            self.volume_label.setText(str(tts_settings.volume))
            self.speed_spinbox.setValue(tts_settings.speed)
            self.voice_spinbox.setValue(tts_settings.voice)
            
            # 加载模板
            if hasattr(tts_settings, 'enter_tts_templates'):
                self.enter_template_text.setPlainText('\n'.join(tts_settings.enter_tts_templates))
            
            if hasattr(tts_settings, 'follow_tts_templates'):
                self.follow_template_text.setPlainText('\n'.join(tts_settings.follow_tts_templates))
                
            if hasattr(tts_settings, 'gift_tts_templates'):
                self.gift_template_text.setPlainText('\n'.join(tts_settings.gift_tts_templates))
                
            if hasattr(tts_settings, 'keyword_reply_templates'):
                keyword_text = []
                for keyword, templates in tts_settings.keyword_reply_templates.items():
                    keyword_text.append(f"{keyword}={'|'.join(templates)}")
                self.keyword_template_text.setPlainText('\n'.join(keyword_text))
                
        except Exception as e:
            g_logger.error(f"加载TTS配置失败: {e}")
            
    def on_tts_master_changed(self, state):
        """TTS总开关改变"""
        enabled = state == Qt.Checked
        self.config_manager.update_tts_setting('tts_enabled', enabled)
        self._notify_tts_handler_config_changed()
        
    def on_message_tts_changed(self, key, state):
        """消息类型TTS开关改变"""
        enabled = state == Qt.Checked
        self.config_manager.update_tts_setting(key, enabled)
        self._notify_tts_handler_config_changed()
        
    def on_volume_changed(self, value):
        """音量改变"""
        self.volume_label.setText(str(value))
        self.config_manager.update_tts_setting('volume', value)
        self._notify_tts_handler_config_changed()
        
    def on_speed_changed(self, value):
        """语速改变"""
        self.config_manager.update_tts_setting('speed', value)
        self._notify_tts_handler_config_changed()
        
    def on_voice_changed(self, value):
        """声音类型改变"""
        self.config_manager.update_tts_setting('voice', value)
        self._notify_tts_handler_config_changed()
        
    def save_enter_templates(self):
        """保存进入消息模板"""
        templates = [line.strip() for line in self.enter_template_text.toPlainText().split('\n') if line.strip()]
        if templates:
            self.config_manager.update_tts_setting('enter_tts_templates', templates)
            g_logger.info("进入消息模板已保存")
            self._notify_tts_handler_config_changed()
            
    def save_follow_templates(self):
        """保存关注消息模板"""
        templates = [line.strip() for line in self.follow_template_text.toPlainText().split('\n') if line.strip()]
        if templates:
            self.config_manager.update_tts_setting('follow_tts_templates', templates)
            g_logger.info("关注消息模板已保存")
            self._notify_tts_handler_config_changed()
            
    def save_gift_templates(self):
        """保存礼物消息模板"""
        templates = [line.strip() for line in self.gift_template_text.toPlainText().split('\n') if line.strip()]
        if templates:
            self.config_manager.update_tts_setting('gift_tts_templates', templates)
            g_logger.info("礼物消息模板已保存")
            self._notify_tts_handler_config_changed()
            
    def save_keyword_templates(self):
        """保存关键词回复模板"""
        lines = self.keyword_template_text.toPlainText().split('\n')
        keyword_templates = {}
        for line in lines:
            line = line.strip()
            if line and '=' in line:
                parts = line.split('=', 1)
                keyword = parts[0].strip()
                templates_str = parts[1].strip()
                templates = [t.strip() for t in templates_str.split('|') if t.strip()]
                if keyword and templates:
                    keyword_templates[keyword] = templates
        
        if keyword_templates:
            self.config_manager.update_tts_setting('keyword_reply_templates', keyword_templates)
            g_logger.info("关键词回复模板已保存")
            self._notify_tts_handler_config_changed()
            
    def _notify_tts_handler_config_changed(self):
        """通知TTS处理器配置已变更"""
        try:
            if self.tts_handler:
                self.tts_handler.update_config()
                g_logger.debug("已通知TTS处理器配置变更")
            else:
                # 尝试重新获取TTS处理器
                self.tts_handler = init_tts_handler(self.config_manager)
                if self.tts_handler:
                    self.tts_handler.update_config()
                    g_logger.debug("重新获取TTS处理器并通知配置变更")
        except Exception as e:
            g_logger.error(f"通知TTS处理器配置变更失败: {e}")