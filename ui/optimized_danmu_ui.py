from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QPushButton, QListWidget, QListWidgetItem, QCheckBox,
                             QLabel, QScrollArea, QFrame, QSplitter, QTextEdit,
                             QGroupBox, QSpinBox, QTabWidget, QLineEdit)
from PyQt5.QtCore import QRect, Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QColor, QTextCursor
import sys
from datetime import datetime
from config.config import config_manager
from ui.optimized_danmu_controller import OptimizedDanmuController, checkbox_labels
from ui.tts_config_ui import TTSConfigUI
from ui.keyword_ui import KeywordManagerUI
from config.log import g_logger


class OptimizedRoom(QWidget):
    """优化的弹幕控制台界面"""
    
    def __init__(self):
        super().__init__()
        self.danmu_controller = None
        self.config_manager = config_manager
        
        self.init_ui()
        self.show()
        
    def init_ui(self):
        """初始化UI界面"""
        self.setWindowTitle("Douyin Live Danmu - 优化版弹幕控制台")
        # 设置窗口尺寸并居中显示
        self.setGeometry(self.calculate_center_rect(1400, 900))
        
        # 创建主布局
        main_layout = QVBoxLayout()
        
        # 创建顶部控制区域
        self.create_control_panel(main_layout)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 弹幕监控标签页
        monitor_widget = QWidget()
        monitor_layout = QVBoxLayout()
        
        # 创建主要内容区域（分割器）
        splitter = QSplitter(Qt.Horizontal)
        self.create_filter_panel(splitter)
        self.create_danmu_panel(splitter)
        monitor_layout.addWidget(splitter)
        
        # 创建底部状态栏
        self.create_status_panel(monitor_layout)
        
        monitor_widget.setLayout(monitor_layout)
        self.tab_widget.addTab(monitor_widget, "弹幕监控")
        
        # TTS配置标签页
        tts_config_widget = QWidget()
        tts_config_layout = QVBoxLayout()
        self.tts_config_panel = TTSConfigUI(config_manager)
        # 连接配置变更信号到更新方法
        self.tts_config_panel.config_changed.connect(self.on_tts_config_changed)
        tts_config_layout.addWidget(self.tts_config_panel)
        tts_config_widget.setLayout(tts_config_layout)
        self.tab_widget.addTab(tts_config_widget, "TTS配置")
        
        # 关键词管理标签页
        keyword_widget = QWidget()
        keyword_layout = QVBoxLayout()
        self.keyword_panel = KeywordManagerUI(config_manager)
        keyword_layout.addWidget(self.keyword_panel)
        keyword_widget.setLayout(keyword_layout)
        self.tab_widget.addTab(keyword_widget, "关键词管理")
        
        # 高级设置标签页
        advanced_widget = self.create_advanced_tab()
        self.tab_widget.addTab(advanced_widget, "高级设置")
        
        main_layout.addWidget(self.tab_widget)
        
        self.setLayout(main_layout)
        
        # 初始化优化的弹幕控制器
        self.init_optimized_danmu_controller()
        
        # 启动定时器更新弹幕列表
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_danmu_list)
        self.update_timer.start(100)  # 每100ms更新一次
        
        
    def create_control_panel(self, parent_layout):
        """创建顶部控制面板"""
        control_frame = QFrame()
        control_frame.setFrameStyle(QFrame.Box)
        control_frame.setMaximumHeight(80)
        control_layout = QHBoxLayout()
        
        # 房间ID输入和连接按钮
        self.room_id_input = QLineEdit()
        self.room_id_input.setPlaceholderText("请输入抖音直播间ID")
        self.room_id_input.setFixedHeight(35)
        self.room_id_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #ddd;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
        """)
        
        self.connect_btn = QPushButton("连接直播间")
        self.connect_btn.clicked.connect(self.toggle_connection)
        self.connect_btn.setFixedHeight(35)
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        # 性能状态显示
        self.performance_label = QLabel("性能: 正常")
        self.performance_label.setStyleSheet("color: #4CAF50; font-weight: bold; font-size: 12px;")
        
        # TTS状态显示
        self.tts_status_label = QLabel("TTS: 未启用")
        self.tts_status_label.setStyleSheet("color: #9E9E9E; font-weight: bold; font-size: 12px;")
        
        control_layout.addWidget(QLabel("直播间ID:"))
        control_layout.addWidget(self.room_id_input)
        control_layout.addWidget(self.connect_btn)
        control_layout.addStretch()
        control_layout.addWidget(self.tts_status_label)
        control_layout.addWidget(self.performance_label)
        
        control_frame.setLayout(control_layout)
        parent_layout.addWidget(control_frame)
        
    def create_filter_panel(self, parent_splitter):
        """创建左侧筛选面板"""
        filter_frame = QFrame()
        filter_frame.setFrameStyle(QFrame.Box)
        filter_frame.setMaximumWidth(350)
        filter_layout = QVBoxLayout()
        
        # 筛选标题
        filter_title = QLabel("消息类型筛选")
        filter_title.setFont(QFont("Arial", 12, QFont.Bold))
        filter_layout.addWidget(filter_title)
        
        # 消息类型复选框
        self.message_checkboxes = {}
        for msg_type, label in checkbox_labels.items():
            checkbox = QCheckBox(label)
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(lambda state, mt=msg_type: self.on_filter_changed(mt, state))
            self.message_checkboxes[msg_type] = checkbox
            filter_layout.addWidget(checkbox)
        
        # 快速过滤设置
        quick_filter_group = QGroupBox("快速过滤设置")
        quick_filter_layout = QVBoxLayout()
        
        self.enable_smart_filter_cb = QCheckBox("启用智能过滤")
        self.enable_smart_filter_cb.setChecked(True)
        self.enable_smart_filter_cb.stateChanged.connect(self.on_smart_filter_changed)
        quick_filter_layout.addWidget(self.enable_smart_filter_cb)
        
        self.enable_priority_cb = QCheckBox("启用优先级处理")
        self.enable_priority_cb.setChecked(True)
        self.enable_priority_cb.stateChanged.connect(self.on_priority_changed)
        quick_filter_layout.addWidget(self.enable_priority_cb)
        
        quick_filter_group.setLayout(quick_filter_layout)
        filter_layout.addWidget(quick_filter_group)
        
        # 队列设置
        queue_group = QGroupBox("队列设置")
        queue_layout = QGridLayout()
        
        queue_layout.addWidget(QLabel("队列大小:"), 0, 0)
        self.queue_size_spin = QSpinBox()
        self.queue_size_spin.setRange(5, 100)
        self.queue_size_spin.setValue(30)
        self.queue_size_spin.valueChanged.connect(self.on_queue_size_changed)
        queue_layout.addWidget(self.queue_size_spin, 0, 1)
        
        queue_layout.addWidget(QLabel("去重窗口(秒):"), 1, 0)
        self.dedup_window_spin = QSpinBox()
        self.dedup_window_spin.setRange(5, 300)
        self.dedup_window_spin.setValue(30)
        self.dedup_window_spin.valueChanged.connect(self.on_dedup_window_changed)
        queue_layout.addWidget(self.dedup_window_spin, 1, 1)
        
        queue_group.setLayout(queue_layout)
        filter_layout.addWidget(queue_group)
        
        # 清空列表按钮
        self.clear_btn = QPushButton("清空弹幕列表")
        self.clear_btn.clicked.connect(self.clear_danmu_list)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        filter_layout.addWidget(self.clear_btn)
        
        filter_layout.addStretch()
        filter_frame.setLayout(filter_layout)
        parent_splitter.addWidget(filter_frame)
        
    def create_danmu_panel(self, parent_splitter):
        """创建右侧弹幕显示面板"""
        danmu_frame = QFrame()
        danmu_layout = QVBoxLayout()
        
        # 弹幕列表标题和统计
        header_layout = QHBoxLayout()
        danmu_title = QLabel("弹幕列表")
        danmu_title.setFont(QFont("Arial", 12, QFont.Bold))
        
        self.danmu_count_label = QLabel("总计: 0 条")
        self.filter_count_label = QLabel("过滤: 0 条")
        
        header_layout.addWidget(danmu_title)
        header_layout.addStretch()
        header_layout.addWidget(self.danmu_count_label)
        header_layout.addWidget(self.filter_count_label)
        danmu_layout.addLayout(header_layout)
        
        # 弹幕列表
        self.danmu_list = QListWidget()
        self.danmu_list.setFont(QFont("Consolas", 9))
        self.danmu_list.setStyleSheet("""
            QListWidget {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
            }
            QListWidget::item {
                padding: 4px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
            }
        """)
        danmu_layout.addWidget(self.danmu_list)
        
        danmu_frame.setLayout(danmu_layout)
        parent_splitter.addWidget(danmu_frame)
        
    def create_status_panel(self, parent_layout):
        """创建底部状态面板"""
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.Box)
        status_frame.setMaximumHeight(60)
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("状态: 未连接")
        self.status_label.setStyleSheet("color: #f44336; font-weight: bold;")
        
        self.received_count_label = QLabel("已接收: 0 条")
        self.tts_count_label = QLabel("TTS: 0 条")
        
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.tts_count_label)
        status_layout.addWidget(self.received_count_label)
        
        status_frame.setLayout(status_layout)
        parent_layout.addWidget(status_frame)
        
    def create_advanced_tab(self):
        """创建高级设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 统计信息
        stats_group = QGroupBox("系统统计")
        stats_layout = QVBoxLayout()
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(200)
        stats_layout.addWidget(self.stats_text)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        
        return widget
    
    def quick_pause_tts(self):
        """快速暂停TTS"""
        if self.danmu_controller and self.danmu_controller.tts_controller:
            self.danmu_controller.tts_controller.toggle_pause()
    
    def quick_clear_cache(self):
        """快速清空TTS缓存"""
        if self.danmu_controller and self.danmu_controller.tts_controller:
            self.danmu_controller.tts_controller.clear_cache()
    
    def test_tts(self):
        """测试TTS功能"""
        if self.danmu_controller and self.danmu_controller.tts_controller:
            self.danmu_controller.tts_controller.test_tts("这是一条测试语音")
    
    def init_optimized_danmu_controller(self):
        """初始化优化的弹幕控制器"""
        self.danmu_controller = OptimizedDanmuController()
        self.total_received = 0
        self.total_filtered = 0
        
        # 从配置文件加载筛选状态
        self.load_filter_settings()
        
    def load_filter_settings(self):
        """从配置加载筛选设置"""
        danmu_settings = self.config_manager.danmu_settings
        for msg_type, checkbox in self.message_checkboxes.items():
            if hasattr(danmu_settings, msg_type):
                checkbox.setChecked(getattr(danmu_settings, msg_type))
                
    def toggle_connection(self):
        """切换连接状态"""
        if self.connect_btn.text() == "连接直播间":
            room_id = self.room_id_input.text().strip()
            if room_id:
                self.connect_to_room(room_id)
            else:
                self.status_label.setText("状态: 请输入房间ID")
        else:
            self.disconnect_room()
            
    def connect_to_room(self, room_id):
        """连接到直播间"""
        try:
            self.danmu_controller.start(room_id)
            self.connect_btn.setText("断开连接")
            self.connect_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #da190b;
                }
            """)
            self.status_label.setText(f"状态: 已连接到房间 {room_id}")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            self.clear_danmu_list()
        except Exception as e:
            self.status_label.setText(f"状态: 连接失败 - {str(e)}")
            self.status_label.setStyleSheet("color: #f44336; font-weight: bold;")
            
    def disconnect_room(self):
        """断开直播间连接"""
        if self.danmu_controller:
            self.danmu_controller.cleanup()
        self.connect_btn.setText("连接直播间")
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.status_label.setText("状态: 未连接")
        self.status_label.setStyleSheet("color: #f44336; font-weight: bold;")
        
    def on_filter_changed(self, msg_type, state):
        """筛选条件改变时的处理"""
        is_checked = state == Qt.Checked
        # 更新配置
        self.config_manager.update_danmu_setting(msg_type, is_checked)
        
    def on_smart_filter_changed(self, state):
        """智能过滤设置变更（已移除TTS功能）"""
        pass
    
    def on_priority_changed(self, state):
        """优先级处理设置变更（已移除TTS功能）"""
        pass
    
    def on_queue_size_changed(self, value):
        """队列大小变更（已移除TTS功能）"""
        pass
    
    def on_dedup_window_changed(self, value):
        """去重窗口变更（已移除TTS功能）"""
        pass
    
    def on_tts_config_changed(self):
        """TTS配置变更时的处理"""
        if self.danmu_controller and self.danmu_controller.tts_controller:
            # 读取当前配置并传递给TTS控制器
            tts_config = {
                'voice': self.config_manager.tts_settings.voice,
                'rate': self.config_manager.tts_settings.rate,
                'volume': self.config_manager.tts_settings.volume,
                'playback_volume': self.config_manager.tts_settings.playback_volume,
                'play_interval': self.config_manager.tts_settings.play_interval,
                'max_queue_size': self.config_manager.tts_settings.max_queue_size
            }
            self.danmu_controller.update_tts_config(tts_config)
            g_logger.debug("TTS配置已更新到控制器")
    
    def update_danmu_list(self):
        """更新弹幕列表"""
        if self.danmu_controller:
            # 获取新的弹幕
            while True:
                method, danmu = self.danmu_controller.get_danmu()
                if method is None:
                    break
                    
                self.total_received += 1
                
                # 添加到列表
                self.add_danmu_to_list(method, danmu)
            
            # 更新统计
            self.update_statistics()
            
    def add_danmu_to_list(self, method, danmu):
        """添加弹幕到列表显示"""
        # 这里复用原来的弹幕显示逻辑，但添加TTS标识
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            def get_username(data):
                if not data:
                    return "未知用户"
                name = data.get('user_name', '未知用户')
                return name
            
            # 根据消息类型格式化显示
            if method == 'WebcastChatMessage':
                user_name = get_username(danmu)
                content = danmu.get('content', '').strip()
                if not content:
                    content = "[空消息]"
                display_text = f"[{timestamp}] 💬 {user_name}: {content}"
                color = QColor("#2196F3")
                
            elif method == 'WebcastGiftMessage':
                user_name = get_username(danmu)
                gift_name = danmu.get('gift_name', danmu.get('gift', {}).get('name', '未知礼物'))
                gift_count = danmu.get('gift_count', danmu.get('combo_count', danmu.get('count', 1)))
                if gift_count > 1:
                    display_text = f"[{timestamp}] 🎁 {user_name} 送出 {gift_name} x{gift_count}"
                else:
                    display_text = f"[{timestamp}] 🎁 {user_name} 送出 {gift_name}"
                color = QColor("#FF9800")
                
            elif method == 'WebcastLikeMessage':
                user_name = get_username(danmu)
                count = danmu.get('count', 1)
                if count > 1:
                    display_text = f"[{timestamp}] 👍 {user_name} 点赞了 {count} 次"
                else:
                    display_text = f"[{timestamp}] 👍 {user_name} 点赞了"
                color = QColor("#4CAF50")
                
            elif method == 'WebcastMemberMessage':
                user_name = get_username(danmu)
                display_text = f"[{timestamp}] 👋 {user_name} 进入直播间"
                color = QColor("#9C27B0")
                
            elif method == 'WebcastSocialMessage':
                user_name = get_username(danmu)
                display_text = f"[{timestamp}] ⭐ {user_name} 关注了主播"
                color = QColor("#E91E63")
                
            else:
                display_text = f"[{timestamp}] 📢 {method}: {str(danmu)[:50]}..."
                color = QColor("#607D8B")
            
            # 创建列表项
            item = QListWidgetItem(display_text)
            item.setForeground(color)
            
            # 添加到列表底部
            self.danmu_list.addItem(item)
            
            # 限制列表长度
            max_items = 1000
            if self.danmu_list.count() > max_items:
                self.danmu_list.takeItem(0)
            
            # 自动滚动到底部
            if self.danmu_list.verticalScrollBar().value() == self.danmu_list.verticalScrollBar().maximum():
                self.danmu_list.scrollToBottom()
                
        except Exception as e:
            error_text = f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 消息格式化错误: {str(e)[:50]}..."
            error_item = QListWidgetItem(error_text)
            error_item.setForeground(QColor("#F44336"))
            self.danmu_list.addItem(error_item)
            self.danmu_list.scrollToBottom()
            g_logger.error(f"添加弹幕到列表失败: {e}")
    
    def update_statistics(self):
        """更新统计信息"""
        self.danmu_count_label.setText(f"总计: {self.danmu_list.count()} 条")
        self.received_count_label.setText(f"已接收: {self.total_received} 条")
        
        # 获取性能统计
        if self.danmu_controller:
            stats = self.danmu_controller.get_performance_stats()
            self.total_filtered = stats.get('filtered_messages', 0)
            
            self.filter_count_label.setText(f"过滤: {self.total_filtered} 条")
            
            # 更新TTS统计
            if self.danmu_controller.tts_controller:
                tts_stats = self.danmu_controller.tts_controller.get_stats()
                self.tts_count_label.setText(f"TTS: {tts_stats.get('total_played', 0)} 条")
                
                # 更新TTS状态标签
                if self.config_manager.tts_settings.enabled:
                    if tts_stats.get('is_paused', False):
                        self.tts_status_label.setText("TTS: 已暂停")
                        self.tts_status_label.setStyleSheet("color: #FF9800; font-weight: bold; font-size: 12px;")
                    else:
                        self.tts_status_label.setText("TTS: 运行中")
                        self.tts_status_label.setStyleSheet("color: #4CAF50; font-weight: bold; font-size: 12px;")
                else:
                    self.tts_status_label.setText("TTS: 未启用")
                    self.tts_status_label.setStyleSheet("color: #9E9E9E; font-weight: bold; font-size: 12px;")
            
            # 更新高级设置的统计信息
            self.update_advanced_stats(stats)
    
    def update_advanced_stats(self, stats):
        """更新高级设置的统计信息"""
        try:
            stats_text = f"=== 系统性能统计 ===\n"
            stats_text += f"运行时间: {stats.get('runtime_seconds', 0):.1f} 秒\n"
            stats_text += f"总消息数: {stats.get('total_messages', 0)}\n"
            stats_text += f"过滤消息数: {stats.get('filtered_messages', 0)}\n"
            stats_text += f"消息速率: {stats.get('messages_per_second', 0):.1f} msg/s\n\n"
            
            # 添加TTS统计
            if self.danmu_controller and self.danmu_controller.tts_controller:
                tts_stats = self.danmu_controller.tts_controller.get_stats()
                stats_text += f"=== TTS统计 ===\n"
                stats_text += f"已生成: {tts_stats.get('total_generated', 0)} 条\n"
                stats_text += f"已播放: {tts_stats.get('total_played', 0)} 条\n"
                stats_text += f"队列长度: {tts_stats.get('queue_size', 0)}\n"
                stats_text += f"缓存命中: {tts_stats.get('cache_hits', 0)} 次\n"
                stats_text += f"缓存大小: {tts_stats.get('cache_size_mb', 0):.2f} MB\n\n"
            
            self.stats_text.setText(stats_text)
            
        except Exception as e:
            g_logger.error(f"更新高级统计失败: {e}")
    
    def clear_danmu_list(self):
        """清空弹幕列表"""
        self.danmu_list.clear()
        self.total_received = 0
        self.total_filtered = 0
        self.update_statistics()
    
    def refresh_keyword_list(self):
        """刷新关键词列表"""
        if self.keyword_panel:
            self.keyword_panel.load_keywords()
    
    def refresh_tts_config(self):
        """刷新TTS配置"""
        if self.tts_config_panel:
            self.tts_config_panel.load_config()
        
    def calculate_center_rect(self, width, height):
        """计算居中矩形"""
        screen_geometry = self.screen().availableGeometry()
        x = (screen_geometry.width() - width) // 2
        y = (screen_geometry.height() - height) // 2
        return QRect(x, y, width, height)
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.danmu_controller:
            self.danmu_controller.cleanup()
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        event.accept()