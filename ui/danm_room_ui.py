from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QPushButton, QListWidget, QListWidgetItem, QCheckBox,
                             QLabel, QScrollArea, QFrame, QSplitter, QTextEdit,
                             QGroupBox, QSpinBox, QTabWidget)
from PyQt5.QtCore import QRect, Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QColor, QTextCursor
import sys
from datetime import datetime
from config.config import config_manager
from ui.danmu_controller import DanmuController, checkbox_labels
from ui.tts_config_ui import TTSConfigPanel
from config.log import g_logger

class Room(QWidget):
    def __init__(self):
        super().__init__()
        self.danmu_controller = None
        self.config_manager = config_manager
        self.init_ui()
        self.show()
        
    def init_ui(self):
        self.setWindowTitle("Douyin Live Danmu - 弹幕控制台")
        # 设置窗口尺寸并居中显示
        self.setGeometry(self.calculate_center_rect(1200, 800))
        
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
        self.tts_config_panel = TTSConfigPanel()
        self.tab_widget.addTab(self.tts_config_panel, "TTS配置")
        
        main_layout.addWidget(self.tab_widget)
        
        self.setLayout(main_layout)
        
        # 初始化弹幕控制器
        self.init_danmu_controller()
        
        # 启动定时器更新弹幕列表
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_danmu_list)
        self.update_timer.start(100)  # 每100ms更新一次
        
    def create_control_panel(self, parent_layout):
        """创建顶部控制面板"""
        control_frame = QFrame()
        control_frame.setFrameStyle(QFrame.Box)
        control_frame.setMaximumHeight(80)  # 限制控制面板最大高度
        control_layout = QHBoxLayout()
        
        # 房间ID输入和连接按钮
        from PyQt5.QtWidgets import QLineEdit
        self.room_id_input = QLineEdit()
        self.room_id_input.setPlaceholderText("请输入抖音直播间ID")
        self.room_id_input.setFixedHeight(35)
        # self.room_id_input.setFixedWidth(150)
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
        
        control_layout.addWidget(QLabel("直播间ID:"))
        control_layout.addWidget(self.room_id_input)
        control_layout.addWidget(self.connect_btn)
        control_layout.addStretch()
        
        control_frame.setLayout(control_layout)
        parent_layout.addWidget(control_frame)
        
    def create_filter_panel(self, parent_splitter):
        """创建左侧筛选面板"""
        filter_frame = QFrame()
        filter_frame.setFrameStyle(QFrame.Box)
        filter_frame.setMaximumWidth(300)
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
        header_layout.addWidget(danmu_title)
        header_layout.addStretch()
        header_layout.addWidget(self.danmu_count_label)
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
        status_frame.setMaximumHeight(50)  # 减少状态面板高度
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("状态: 未连接")
        self.status_label.setStyleSheet("color: #f44336; font-weight: bold;")
        
        self.received_count_label = QLabel("已接收: 0 条")
        self.filtered_count_label = QLabel("已过滤: 0 条")
        
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.received_count_label)
        status_layout.addWidget(self.filtered_count_label)
        
        status_frame.setLayout(status_layout)
        parent_layout.addWidget(status_frame)
        
    def init_danmu_controller(self):
        """初始化弹幕控制器"""
        self.danmu_controller = DanmuController()
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
            # self.danmu_controller.dy_fetcher
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
        
    def update_danmu_list(self):
        """更新弹幕列表"""

        if self.danmu_controller:
            # 获取新的弹幕
            while True:
                method, danmu = self.danmu_controller.get_danmu()
                # g_logger.debug(f"添加弹幕: {method} - {danmu}")
                if method is None:
                    break
                    
                self.total_received += 1
                
                # 添加到列表
                self.add_danmu_to_list(method, danmu)
           
                
            # 更新统计
            self.update_statistics()
            
    def add_danmu_to_list(self, method, danmu):
        """添加弹幕到列表显示"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # 安全获取用户名的辅助函数
            def get_username(data):
                """安全获取用户名"""
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
                # 格式化礼物数量显示
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
                gender = danmu.get('gender', '')
                if gender:
                    display_text = f"[{timestamp}] 👋 [{gender}] {user_name} 进入直播间"
                else:
                    display_text = f"[{timestamp}] 👋 {user_name} 进入直播间"
                color = QColor("#9C27B0")
                
            elif method == 'WebcastSocialMessage':
                user_name = get_username(danmu)
                display_text = f"[{timestamp}] ⭐ {user_name} 关注了主播"
                color = QColor("#E91E63")
                
            elif method == 'WebcastFansclubMessage':
                user_name = get_username(danmu)
                content = danmu.get('content', '').strip()
                if content:
                    display_text = f"[{timestamp}] 🎭 {user_name}: {content}"
                else:
                    display_text = f"[{timestamp}] 🎭 {user_name} 加入了粉丝团"
                color = QColor("#795548")
                
            elif method == 'WebcastEmojiChatMessage':
                user_name = get_username(danmu)
                default_content = danmu.get('default_content', '').strip()
                emoji_id = danmu.get('emoji_id', '')
                if default_content:
                    display_text = f"[{timestamp}] 😊 {user_name}: {default_content}"
                else:
                    display_text = f"[{timestamp}] 😊 {user_name} 发送了表情包"
                color = QColor("#FF5722")
                
            elif method == 'WebcastRoomUserSeqMessage':
                current = danmu.get('current', 0)
                total = danmu.get('total', 0)
                display_text = f"[{timestamp}] 📊 观看统计: 当前 {current} 人, 累计 {total} 人"
                color = QColor("#009688")
                
            elif method == 'WebcastRoomStatsMessage':
                display_long = danmu.get('display_long', '')
                if display_long:
                    display_text = f"[{timestamp}] 📈 直播间统计: {display_long}"
                else:
                    display_text = f"[{timestamp}] 📈 直播间统计信息更新"
                color = QColor("#00BCD4")
                
            elif method == 'WebcastControlMessage':
                status = danmu.get('status', 0)
                if status == 3:
                    display_text = f"[{timestamp}] ⚠️ 直播间已结束"
                    color = QColor("#F44336")
                else:
                    display_text = f"[{timestamp}] 🎮 直播间状态变化 (状态码: {status})"
                    color = QColor("#FFC107")
                    
            elif method == 'WebcastRoomMessage':
                room_id = danmu.get('room_id', '')
                display_text = f"[{timestamp}] 🏠 直播间ID: {room_id}"
                color = QColor("#3F51B5")
                
            elif method == 'WebcastRoomRankMessage':
                ranks_list = danmu.get('ranks_list', [])
                if ranks_list:
                    display_text = f"[{timestamp}] 🏆 排行榜更新: {len(ranks_list)} 个数据"
                else:
                    display_text = f"[{timestamp}] 🏆 排行榜更新"
                color = QColor("#CDDC39")
                
            elif method == 'WebcastRoomStreamAdaptationMessage':
                adaptation_type = danmu.get('adaptation_type', '')
                display_text = f"[{timestamp}] 📹 流配置更新: {adaptation_type}"
                color = QColor("#795548")
                    
            else:
                # 未知消息类型的安全处理
                display_text = f"[{timestamp}] 📢 {method}: {str(danmu)[:100]}..."
                color = QColor("#607D8B")
                
            # 创建列表项
            item = QListWidgetItem(display_text)
            item.setForeground(color)
            
            # 添加到列表底部
            self.danmu_list.addItem(item)
            
            # 限制列表长度，从顶部删除旧消息
            max_items = 1000
            if self.danmu_list.count() > max_items:
                self.danmu_list.takeItem(0)
            
            # 如果在底部，自动滚动
            if self.danmu_list.verticalScrollBar().value() == self.danmu_list.verticalScrollBar().maximum():
                self.danmu_list.scrollToBottom()
                
        except Exception as e:
            # 错误处理：显示错误信息而不是崩溃
            error_text = f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 消息格式化错误: {str(e)[:50]}..."
            error_item = QListWidgetItem(error_text)
            error_item.setForeground(QColor("#F44336"))
            self.danmu_list.addItem(error_item)
            self.danmu_list.scrollToBottom()
            g_logger.error(f"添加弹幕到列表失败: {e}")
            
    def clear_danmu_list(self):
        """清空弹幕列表"""
        self.danmu_list.clear()
        self.total_received = 0
        self.total_filtered = 0
        self.update_statistics()
        
    def update_statistics(self):
        """更新统计信息"""
        self.danmu_count_label.setText(f"总计: {self.danmu_list.count()} 条")
        self.received_count_label.setText(f"已接收: {self.total_received} 条")
        self.filtered_count_label.setText(f"已过滤: {self.total_filtered} 条")
        
    def calculate_center_rect(self, width, height):
        """计算居中矩形"""
        # 获取屏幕尺寸
        screen_geometry = self.screen().availableGeometry()
        # 计算居中位置
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