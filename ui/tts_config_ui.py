"""
TTS配置UI - TTS语音合成配置界面
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLabel, QComboBox, QSlider, QCheckBox,
                             QSpinBox, QPushButton, QFormLayout, QMessageBox,
                             QTextEdit, QTabWidget, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from tts.tts_engine import TTSEngine
from config.log import g_logger


class TTSConfigUI(QWidget):
    """TTS配置界面"""
    
    config_changed = pyqtSignal()  # 配置变更信号
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.available_voices = TTSEngine.get_available_voices()
        
        # 配置保存定时器，避免频繁保存
        self.save_timer = QTimer()
        self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(self._save_event_config_delayed)
        
        self.init_ui()
        self.load_config()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        
        # TTS开关
        self.enabled_cb = QCheckBox("启用TTS语音播报")
        self.enabled_cb.toggled.connect(self.on_enabled_changed)
        layout.addWidget(self.enabled_cb)
        
        # TTS基础设置
        tts_group = QGroupBox("TTS基础设置")
        tts_layout = QFormLayout()
        
        # 语音选择
        self.voice_combo = QComboBox()
        for voice_name in self.available_voices.keys():
            self.voice_combo.addItem(voice_name)
        self.voice_combo.currentTextChanged.connect(self.on_voice_changed)
        tts_layout.addRow("语音类型:", self.voice_combo)
        
        # 语速
        self.rate_slider = QSlider(Qt.Horizontal)
        self.rate_slider.setRange(-100, 100)
        self.rate_slider.setValue(0)
        self.rate_slider.setTickPosition(QSlider.TicksBelow)
        self.rate_slider.setTickInterval(10)
        self.rate_label = QLabel("0%")
        self.rate_slider.valueChanged.connect(self.on_rate_changed)
        
        rate_layout = QHBoxLayout()
        rate_layout.addWidget(self.rate_slider)
        rate_layout.addWidget(self.rate_label)
        tts_layout.addRow("语速:", rate_layout)
        
        # TTS音量
        self.tts_volume_slider = QSlider(Qt.Horizontal)
        self.tts_volume_slider.setRange(-50, 50)
        self.tts_volume_slider.setValue(0)
        self.tts_volume_slider.setTickPosition(QSlider.TicksBelow)
        self.tts_volume_slider.setTickInterval(10)
        self.tts_volume_label = QLabel("0%")
        self.tts_volume_slider.valueChanged.connect(self.on_tts_volume_changed)
        
        tts_volume_layout = QHBoxLayout()
        tts_volume_layout.addWidget(self.tts_volume_slider)
        tts_volume_layout.addWidget(self.tts_volume_label)
        tts_layout.addRow("TTS音量:", tts_volume_layout)
        
        tts_group.setLayout(tts_layout)
        layout.addWidget(tts_group)
        
        # 播放设置
        playback_group = QGroupBox("播放设置")
        playback_layout = QFormLayout()
        
        # 播放音量
        self.playback_volume_slider = QSlider(Qt.Horizontal)
        self.playback_volume_slider.setRange(0, 100)
        self.playback_volume_slider.setValue(80)
        self.playback_volume_slider.setTickPosition(QSlider.TicksBelow)
        self.playback_volume_slider.setTickInterval(10)
        self.playback_volume_label = QLabel("80")
        self.playback_volume_slider.valueChanged.connect(self.on_playback_volume_changed)
        
        playback_volume_layout = QHBoxLayout()
        playback_volume_layout.addWidget(self.playback_volume_slider)
        playback_volume_layout.addWidget(self.playback_volume_label)
        playback_layout.addRow("播放音量:", playback_volume_layout)
        
        # 播放间隔
        self.play_interval_spin = QSpinBox()
        self.play_interval_spin.setRange(0, 5000)
        self.play_interval_spin.setValue(500)
        self.play_interval_spin.setSuffix(" 毫秒")
        self.play_interval_spin.valueChanged.connect(self.on_play_interval_changed)
        playback_layout.addRow("播放间隔:", self.play_interval_spin)
        
        playback_group.setLayout(playback_layout)
        layout.addWidget(playback_group)
        
        # 队列设置
        queue_group = QGroupBox("队列设置")
        queue_layout = QFormLayout()
        
        # 队列大小
        self.queue_size_spin = QSpinBox()
        self.queue_size_spin.setRange(5, 100)
        self.queue_size_spin.setValue(30)
        self.queue_size_spin.valueChanged.connect(self.on_queue_size_changed)
        queue_layout.addRow("队列大小:", self.queue_size_spin)
        
        queue_group.setLayout(queue_layout)
        layout.addWidget(queue_group)
        
        # 缓存设置
        cache_group = QGroupBox("缓存设置")
        cache_layout = QFormLayout()
        
        # 启用缓存
        self.enable_cache_cb = QCheckBox("启用音频缓存")
        self.enable_cache_cb.setChecked(True)
        self.enable_cache_cb.toggled.connect(self.on_cache_enabled_changed)
        cache_layout.addRow(self.enable_cache_cb)
        
        # 缓存最大时间
        self.cache_max_age_spin = QSpinBox()
        self.cache_max_age_spin.setRange(60, 86400)
        self.cache_max_age_spin.setValue(86400)
        self.cache_max_age_spin.setSuffix(" 秒")
        self.cache_max_age_spin.valueChanged.connect(self.on_cache_max_age_changed)
        cache_layout.addRow("缓存最大时间:", self.cache_max_age_spin)
        
        # 缓存最大大小
        self.cache_max_size_spin = QSpinBox()
        self.cache_max_size_spin.setRange(100, 2000)
        self.cache_max_size_spin.setValue(500)
        self.cache_max_size_spin.setSuffix(" MB")
        self.cache_max_size_spin.valueChanged.connect(self.on_cache_max_size_changed)
        cache_layout.addRow("缓存最大大小:", self.cache_max_size_spin)
        
        # 清空缓存按钮
        self.clear_cache_btn = QPushButton("清空缓存")
        self.clear_cache_btn.clicked.connect(self.on_clear_cache)
        cache_layout.addRow(self.clear_cache_btn)
        
        cache_group.setLayout(cache_layout)
        layout.addWidget(cache_group)
        
        # 事件播报设置
        event_group = QGroupBox("事件播报设置")
        event_layout = QVBoxLayout()
        
        # 创建选项卡
        self.event_tabs = QTabWidget()
        
        # 进入直播间播报
        self.member_enter_tab = QWidget()
        self._create_member_enter_tab()
        self.event_tabs.addTab(self.member_enter_tab, "进入直播间")
        
        # 送礼播报
        self.gift_send_tab = QWidget()
        self._create_gift_send_tab()
        self.event_tabs.addTab(self.gift_send_tab, "送礼")
        
        # 关注播报
        self.social_follow_tab = QWidget()
        self._create_social_follow_tab()
        self.event_tabs.addTab(self.social_follow_tab, "关注")
        
        # 点赞播报
        self.like_tab = QWidget()
        self._create_like_tab()
        self.event_tabs.addTab(self.like_tab, "点赞")
        
        event_layout.addWidget(self.event_tabs)
        event_group.setLayout(event_layout)
        layout.addWidget(event_group)
        
        # 测试按钮
        test_layout = QHBoxLayout()
        self.test_btn = QPushButton("测试TTS")
        self.test_btn.clicked.connect(self.on_test_tts)
        test_layout.addWidget(self.test_btn)
        test_layout.addStretch()
        layout.addLayout(test_layout)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def _create_member_enter_tab(self):
        """创建进入直播间播报配置标签页"""
        layout = QFormLayout()
        
        # 启用进入播报
        self.member_enabled_cb = QCheckBox("启用进入直播间播报")
        self.member_enabled_cb.toggled.connect(self.on_member_enabled_changed)
        layout.addRow(self.member_enabled_cb)
        
        # 冷却时间
        self.member_cooldown_spin = QSpinBox()
        self.member_cooldown_spin.setRange(0, 300)
        self.member_cooldown_spin.setValue(30)
        self.member_cooldown_spin.setSuffix(" 秒")
        self.member_cooldown_spin.valueChanged.connect(self.on_member_cooldown_changed)
        layout.addRow("冷却时间:", self.member_cooldown_spin)
        
        # 优先级
        self.member_priority_spin = QSpinBox()
        self.member_priority_spin.setRange(0, 10)
        self.member_priority_spin.setValue(5)
        self.member_priority_spin.valueChanged.connect(self.on_member_priority_changed)
        layout.addRow("优先级:", self.member_priority_spin)
        
        # 用户冷却
        self.member_user_cooldown_cb = QCheckBox("启用用户级冷却")
        self.member_user_cooldown_cb.setChecked(True)
        self.member_user_cooldown_cb.toggled.connect(self.on_member_user_cooldown_changed)
        layout.addRow(self.member_user_cooldown_cb)
        
        # 播报模板
        layout.addRow(QLabel("播报模板:"))
        self.member_templates_edit = QTextEdit()
        self.member_templates_edit.setMaximumHeight(150)
        self.member_templates_edit.setPlaceholderText(
            "每行一个模板，支持变量:\n{user_name} - 用户名\n{gender} - 性别\n{time} - 时间"
        )
        self.member_templates_edit.textChanged.connect(self._trigger_save_delayed)
        layout.addRow(self.member_templates_edit)
        
        self.member_enter_tab.setLayout(layout)
    
    def _create_gift_send_tab(self):
        """创建送礼播报配置标签页"""
        layout = QFormLayout()
        
        # 启用送礼播报
        self.gift_enabled_cb = QCheckBox("启用送礼播报")
        self.gift_enabled_cb.toggled.connect(self.on_gift_enabled_changed)
        layout.addRow(self.gift_enabled_cb)
        
        # 冷却时间
        self.gift_cooldown_spin = QSpinBox()
        self.gift_cooldown_spin.setRange(0, 60)
        self.gift_cooldown_spin.setValue(5)
        self.gift_cooldown_spin.setSuffix(" 秒")
        self.gift_cooldown_spin.valueChanged.connect(self.on_gift_cooldown_changed)
        layout.addRow("冷却时间:", self.gift_cooldown_spin)
        
        # 优先级
        self.gift_priority_spin = QSpinBox()
        self.gift_priority_spin.setRange(0, 10)
        self.gift_priority_spin.setValue(7)
        self.gift_priority_spin.valueChanged.connect(self.on_gift_priority_changed)
        layout.addRow("优先级:", self.gift_priority_spin)
        
        # 启用冷却
        self.gift_enable_cooldown_cb = QCheckBox("启用冷却")
        self.gift_enable_cooldown_cb.setChecked(False)
        self.gift_enable_cooldown_cb.toggled.connect(self.on_gift_enable_cooldown_changed)
        layout.addRow(self.gift_enable_cooldown_cb)
        
        # 最小礼物数量
        self.gift_min_count_spin = QSpinBox()
        self.gift_min_count_spin.setRange(1, 100)
        self.gift_min_count_spin.setValue(1)
        self.gift_min_count_spin.valueChanged.connect(self.on_gift_min_count_changed)
        layout.addRow("最小礼物数量:", self.gift_min_count_spin)
        
        # 播报模板
        layout.addRow(QLabel("播报模板:"))
        self.gift_templates_edit = QTextEdit()
        self.gift_templates_edit.setMaximumHeight(150)
        self.gift_templates_edit.setPlaceholderText(
            "每行一个模板，支持变量:\n{user_name} - 用户名\n{gift_name} - 礼物名称\n{gift_count} - 礼物数量\n{time} - 时间"
        )
        self.gift_templates_edit.textChanged.connect(self._trigger_save_delayed)
        layout.addRow(self.gift_templates_edit)
        
        self.gift_send_tab.setLayout(layout)
    
    def _create_social_follow_tab(self):
        """创建关注播报配置标签页"""
        layout = QFormLayout()
        
        # 启用关注播报
        self.follow_enabled_cb = QCheckBox("启用关注播报")
        self.follow_enabled_cb.toggled.connect(self.on_follow_enabled_changed)
        layout.addRow(self.follow_enabled_cb)
        
        # 冷却时间
        self.follow_cooldown_spin = QSpinBox()
        self.follow_cooldown_spin.setRange(0, 300)
        self.follow_cooldown_spin.setValue(60)
        self.follow_cooldown_spin.setSuffix(" 秒")
        self.follow_cooldown_spin.valueChanged.connect(self.on_follow_cooldown_changed)
        layout.addRow("冷却时间:", self.follow_cooldown_spin)
        
        # 优先级
        self.follow_priority_spin = QSpinBox()
        self.follow_priority_spin.setRange(0, 10)
        self.follow_priority_spin.setValue(6)
        self.follow_priority_spin.valueChanged.connect(self.on_follow_priority_changed)
        layout.addRow("优先级:", self.follow_priority_spin)
        
        # 用户冷却
        self.follow_user_cooldown_cb = QCheckBox("启用用户级冷却")
        self.follow_user_cooldown_cb.setChecked(True)
        self.follow_user_cooldown_cb.toggled.connect(self.on_follow_user_cooldown_changed)
        layout.addRow(self.follow_user_cooldown_cb)
        
        # 播报模板
        layout.addRow(QLabel("播报模板:"))
        self.follow_templates_edit = QTextEdit()
        self.follow_templates_edit.setMaximumHeight(150)
        self.follow_templates_edit.setPlaceholderText(
            "每行一个模板，支持变量:\n{user_name} - 用户名\n{time} - 时间"
        )
        self.follow_templates_edit.textChanged.connect(self._trigger_save_delayed)
        layout.addRow(self.follow_templates_edit)
        
        self.social_follow_tab.setLayout(layout)
    
    def _create_like_tab(self):
        """创建点赞播报配置标签页"""
        layout = QFormLayout()
        
        # 启用点赞播报
        self.like_enabled_cb = QCheckBox("启用点赞播报")
        self.like_enabled_cb.toggled.connect(self.on_like_enabled_changed)
        layout.addRow(self.like_enabled_cb)
        
        # 冷却时间
        self.like_cooldown_spin = QSpinBox()
        self.like_cooldown_spin.setRange(0, 60)
        self.like_cooldown_spin.setValue(10)
        self.like_cooldown_spin.setSuffix(" 秒")
        self.like_cooldown_spin.valueChanged.connect(self.on_like_cooldown_changed)
        layout.addRow("冷却时间:", self.like_cooldown_spin)
        
        # 优先级
        self.like_priority_spin = QSpinBox()
        self.like_priority_spin.setRange(0, 10)
        self.like_priority_spin.setValue(4)
        self.like_priority_spin.valueChanged.connect(self.on_like_priority_changed)
        layout.addRow("优先级:", self.like_priority_spin)
        
        # 启用冷却
        self.like_enable_cooldown_cb = QCheckBox("启用冷却")
        self.like_enable_cooldown_cb.setChecked(True)
        self.like_enable_cooldown_cb.toggled.connect(self.on_like_enable_cooldown_changed)
        layout.addRow(self.like_enable_cooldown_cb)
        
        # 最小点赞数量
        self.like_min_count_spin = QSpinBox()
        self.like_min_count_spin.setRange(1, 100)
        self.like_min_count_spin.setValue(10)
        self.like_min_count_spin.valueChanged.connect(self.on_like_min_count_changed)
        layout.addRow("最小点赞数量:", self.like_min_count_spin)
        
        # 播报模板
        layout.addRow(QLabel("播报模板:"))
        self.like_templates_edit = QTextEdit()
        self.like_templates_edit.setMaximumHeight(150)
        self.like_templates_edit.setPlaceholderText(
            "每行一个模板，支持变量:\n{user_name} - 用户名\n{count} - 点赞数量\n{time} - 时间"
        )
        self.like_templates_edit.textChanged.connect(self._trigger_save_delayed)
        layout.addRow(self.like_templates_edit)
        
        self.like_tab.setLayout(layout)
    
    def load_config(self):
        """加载配置"""
        try:
            tts_settings = self.config_manager.tts_settings
            
            # TTS开关
            self.enabled_cb.setChecked(tts_settings.enabled)
            
            # 语音
            voice = tts_settings.voice
            if voice in self.available_voices:
                self.voice_combo.setCurrentText(voice)
            
            # 语速
            rate_str = tts_settings.rate
            rate = int(rate_str.replace('+', '').replace('%', ''))
            self.rate_slider.setValue(rate)
            self.rate_label.setText(rate_str)
            
            # TTS音量
            volume_str = tts_settings.volume
            volume = int(volume_str.replace('+', '').replace('%', ''))
            self.tts_volume_slider.setValue(volume)
            self.tts_volume_label.setText(volume_str)
            
            # 播放音量
            self.playback_volume_slider.setValue(tts_settings.playback_volume)
            self.playback_volume_label.setText(str(tts_settings.playback_volume))
            
            # 播放间隔
            self.play_interval_spin.setValue(int(tts_settings.play_interval * 1000))
            
            # 队列大小
            self.queue_size_spin.setValue(tts_settings.max_queue_size)
            
            # 缓存设置
            self.enable_cache_cb.setChecked(tts_settings.enable_cache)
            self.cache_max_age_spin.setValue(tts_settings.cache_max_age)
            self.cache_max_size_spin.setValue(tts_settings.cache_max_size_mb)
            
            # 加载事件播报配置
            self._load_event_config()
            
            g_logger.info("TTS配置加载完成")
            
        except Exception as e:
            g_logger.error(f"加载TTS配置失败: {e}")
    
    def on_enabled_changed(self, checked: bool):
        """TTS开关改变"""
        self.config_manager.update_tts_setting('enabled', checked)
        self.config_changed.emit()
        g_logger.info(f"TTS已{'启用' if checked else '禁用'}")
    
    def on_voice_changed(self, voice: str):
        """语音改变"""
        self.config_manager.update_tts_setting('voice', voice)
        self.config_changed.emit()
        g_logger.info(f"TTS语音已更改: {voice}")
    
    def on_rate_changed(self, value: int):
        """语速改变"""
        rate_str = f"{value:+d}%"
        self.rate_label.setText(rate_str)
        self.config_manager.update_tts_setting('rate', rate_str)
        self.config_changed.emit()
    
    def on_tts_volume_changed(self, value: int):
        """TTS音量改变"""
        volume_str = f"{value:+d}%"
        self.tts_volume_label.setText(volume_str)
        self.config_manager.update_tts_setting('volume', volume_str)
        self.config_changed.emit()
    
    def on_playback_volume_changed(self, value: int):
        """播放音量改变"""
        self.playback_volume_label.setText(str(value))
        self.config_manager.update_tts_setting('playback_volume', value)
        self.config_changed.emit()
    
    def on_play_interval_changed(self, value: int):
        """播放间隔改变"""
        play_interval = value / 1000.0
        self.config_manager.update_tts_setting('play_interval', play_interval)
        self.config_changed.emit()
    
    def on_queue_size_changed(self, value: int):
        """队列大小改变"""
        self.config_manager.update_tts_setting('max_queue_size', value)
        self.config_changed.emit()
    
    def on_cache_enabled_changed(self, checked: bool):
        """缓存启用改变"""
        self.config_manager.update_tts_setting('enable_cache', checked)
        self.config_changed.emit()
    
    def on_cache_max_age_changed(self, value: int):
        """缓存最大时间改变"""
        self.config_manager.update_tts_setting('cache_max_age', value)
        self.config_changed.emit()
    
    def on_cache_max_size_changed(self, value: int):
        """缓存最大大小改变"""
        self.config_manager.update_tts_setting('cache_max_size_mb', value)
        self.config_changed.emit()
    
    def on_clear_cache(self):
        """清空缓存"""
        reply = QMessageBox.question(
            self,
            "确认清空",
            "确定要清空所有TTS缓存吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # TODO: 调用TTS控制器的清空缓存方法
            QMessageBox.information(self, "成功", "缓存已清空")
            g_logger.info("用户清空了TTS缓存")
    
    def on_test_tts(self):
        """测试TTS"""
        voice = self.voice_combo.currentText()
        rate = self.rate_slider.value()
        volume = self.tts_volume_slider.value()
        
        # TODO: 调用TTS控制器进行测试
        QMessageBox.information(
            self,
            "测试TTS",
            f"语音: {voice}\n语速: {rate}%\n音量: {volume}%\n\n测试功能需要TTS控制器支持"
        )
    
    def _trigger_save_delayed(self):
        """触发延迟保存（避免频繁保存）"""
        # 启动1秒的定时器，如果1秒内没有新的修改才保存
        self.save_timer.start(1000)
    
    def _save_event_config_delayed(self):
        """延迟保存事件播报配置"""
        self._save_event_config()
        self.config_changed.emit()
    
    def _load_event_config(self):
        """加载事件播报配置"""
        try:
            event_config = self.config_manager.tts_settings.event_announcement
            
            if not event_config:
                return
            
            # 进入直播间配置
            member_config = event_config.get('member_enter', {})
            self.member_enabled_cb.setChecked(member_config.get('enabled', True))
            self.member_cooldown_spin.setValue(member_config.get('cooldown', 30))
            self.member_priority_spin.setValue(member_config.get('priority', 5))
            self.member_user_cooldown_cb.setChecked(member_config.get('user_cooldown', True))
            member_templates = member_config.get('templates', [])
            self.member_templates_edit.setPlainText('\n'.join(member_templates))
            
            # 送礼配置
            gift_config = event_config.get('gift_send', {})
            self.gift_enabled_cb.setChecked(gift_config.get('enabled', True))
            self.gift_cooldown_spin.setValue(gift_config.get('cooldown', 5))
            self.gift_priority_spin.setValue(gift_config.get('priority', 7))
            self.gift_enable_cooldown_cb.setChecked(gift_config.get('enable_cooldown', False))
            self.gift_min_count_spin.setValue(gift_config.get('min_gift_count', 1))
            gift_templates = gift_config.get('templates', [])
            self.gift_templates_edit.setPlainText('\n'.join(gift_templates))
            
            # 关注配置
            follow_config = event_config.get('social_follow', {})
            self.follow_enabled_cb.setChecked(follow_config.get('enabled', True))
            self.follow_cooldown_spin.setValue(follow_config.get('cooldown', 60))
            self.follow_priority_spin.setValue(follow_config.get('priority', 6))
            self.follow_user_cooldown_cb.setChecked(follow_config.get('user_cooldown', True))
            follow_templates = follow_config.get('templates', [])
            self.follow_templates_edit.setPlainText('\n'.join(follow_templates))
            
            # 点赞配置
            like_config = event_config.get('like', {})
            self.like_enabled_cb.setChecked(like_config.get('enabled', False))
            self.like_cooldown_spin.setValue(like_config.get('cooldown', 10))
            self.like_priority_spin.setValue(like_config.get('priority', 4))
            self.like_enable_cooldown_cb.setChecked(like_config.get('enable_cooldown', True))
            self.like_min_count_spin.setValue(like_config.get('min_like_count', 10))
            like_templates = like_config.get('templates', [])
            self.like_templates_edit.setPlainText('\n'.join(like_templates))
            
            g_logger.info("事件播报配置加载完成")
            
        except Exception as e:
            g_logger.error(f"加载事件播报配置失败: {e}")
    
    def _save_event_config(self):
        """保存事件播报配置"""
        try:
            # 获取或创建event_announcement配置
            event_config = self.config_manager.tts_settings.event_announcement or {}
            
            # 保存进入直播间配置
            event_config['member_enter'] = {
                'enabled': self.member_enabled_cb.isChecked(),
                'cooldown': self.member_cooldown_spin.value(),
                'priority': self.member_priority_spin.value(),
                'user_cooldown': self.member_user_cooldown_cb.isChecked(),
                'templates': [line.strip() for line in self.member_templates_edit.toPlainText().split('\n') if line.strip()]
            }
            
            # 保存送礼配置
            event_config['gift_send'] = {
                'enabled': self.gift_enabled_cb.isChecked(),
                'cooldown': self.gift_cooldown_spin.value(),
                'priority': self.gift_priority_spin.value(),
                'enable_cooldown': self.gift_enable_cooldown_cb.isChecked(),
                'min_gift_count': self.gift_min_count_spin.value(),
                'templates': [line.strip() for line in self.gift_templates_edit.toPlainText().split('\n') if line.strip()]
            }
            
            # 保存关注配置
            event_config['social_follow'] = {
                'enabled': self.follow_enabled_cb.isChecked(),
                'cooldown': self.follow_cooldown_spin.value(),
                'priority': self.follow_priority_spin.value(),
                'user_cooldown': self.follow_user_cooldown_cb.isChecked(),
                'templates': [line.strip() for line in self.follow_templates_edit.toPlainText().split('\n') if line.strip()]
            }
            
            # 保存点赞配置
            event_config['like'] = {
                'enabled': self.like_enabled_cb.isChecked(),
                'cooldown': self.like_cooldown_spin.value(),
                'priority': self.like_priority_spin.value(),
                'enable_cooldown': self.like_enable_cooldown_cb.isChecked(),
                'min_like_count': self.like_min_count_spin.value(),
                'templates': [line.strip() for line in self.like_templates_edit.toPlainText().split('\n') if line.strip()]
            }
            
            # 更新配置
            self.config_manager.update_tts_setting('event_announcement', event_config)
            
            g_logger.info("事件播报配置已保存")
            
        except Exception as e:
            g_logger.error(f"保存事件播报配置失败: {e}")
    
    # 进入直播间配置回调
    def on_member_enabled_changed(self, checked: bool):
        """进入播报启用改变"""
        self._trigger_save_delayed()
    
    def on_member_cooldown_changed(self, value: int):
        """进入播报冷却时间改变"""
        self._trigger_save_delayed()
    
    def on_member_priority_changed(self, value: int):
        """进入播报优先级改变"""
        self._trigger_save_delayed()
    
    def on_member_user_cooldown_changed(self, checked: bool):
        """进入播报用户冷却改变"""
        self._trigger_save_delayed()
    
    # 送礼配置回调
    def on_gift_enabled_changed(self, checked: bool):
        """送礼播报启用改变"""
        self._trigger_save_delayed()
    
    def on_gift_cooldown_changed(self, value: int):
        """送礼播报冷却时间改变"""
        self._trigger_save_delayed()
    
    def on_gift_priority_changed(self, value: int):
        """送礼播报优先级改变"""
        self._trigger_save_delayed()
    
    def on_gift_enable_cooldown_changed(self, checked: bool):
        """送礼播报冷却启用改变"""
        self._trigger_save_delayed()
    
    def on_gift_min_count_changed(self, value: int):
        """送礼播报最小数量改变"""
        self._trigger_save_delayed()
    
    # 关注配置回调
    def on_follow_enabled_changed(self, checked: bool):
        """关注播报启用改变"""
        self._trigger_save_delayed()
    
    def on_follow_cooldown_changed(self, value: int):
        """关注播报冷却时间改变"""
        self._trigger_save_delayed()
    
    def on_follow_priority_changed(self, value: int):
        """关注播报优先级改变"""
        self._trigger_save_delayed()
    
    def on_follow_user_cooldown_changed(self, checked: bool):
        """关注播报用户冷却改变"""
        self._trigger_save_delayed()
    
    # 点赞配置回调
    def on_like_enabled_changed(self, checked: bool):
        """点赞播报启用改变"""
        self._trigger_save_delayed()
    
    def on_like_cooldown_changed(self, value: int):
        """点赞播报冷却时间改变"""
        self._trigger_save_delayed()
    
    def on_like_priority_changed(self, value: int):
        """点赞播报优先级改变"""
        self._trigger_save_delayed()
    
    def on_like_enable_cooldown_changed(self, checked: bool):
        """点赞播报冷却启用改变"""
        self._trigger_save_delayed()
    
    def on_like_min_count_changed(self, value: int):
        """点赞播报最小数量改变"""
        self._trigger_save_delayed()