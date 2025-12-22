import sys
import random
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QListWidget, QPushButton, 
                             QSplitter, QTextEdit, QCheckBox)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor
import datetime


class RoomDanmuWindow(QMainWindow):
    # 定义信号，用于关闭窗口事件
    window_closed = pyqtSignal()
    
    def __init__(self, room_id):
        super().__init__()
        self.room_id = room_id
        self.danmu_counter = 0  # 弹幕计数器
        self.user_names = ["用户A", "用户B", "用户C", "用户D", "用户E", "小明", "小红", "小刚", "小李", "小王"]  # 用户名列表
        self.messages = ["这直播不错！", "主播好帅", "关注了关注了", "666666", "礼物刷起来", "学到了", "支持支持", 
                        "讲得真好", "收藏了", "下次还来", "给力", "点赞", "投币", "分享了", "很棒的内容"]  # 消息列表
        self.init_ui()
        self.setup_timers()  # 设置定时器
        
    def init_ui(self):
        # 设置窗口属性
        self.setWindowTitle(f"直播间 {self.room_id} 弹幕")
        self.setGeometry(100, 100, 900, 700)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
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
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #eeeeee;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
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
        self.checkboxes = []
        checkbox_labels = ["显示聊天", "显示礼物", "显示关注", "显示点赞", "显示统计"]
        for i in range(5):
            checkbox = QCheckBox(checkbox_labels[i])
            checkbox.setChecked(True)  # 默认选中
            self.checkboxes.append(checkbox)
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
        
    def setup_timers(self):
        """设置所有定时器"""
        # 设置添加弹幕的定时器，每秒添加一条随机弹幕
        self.add_danmu_timer = QTimer(self)
        self.add_danmu_timer.timeout.connect(self.add_random_danmu)
        self.add_danmu_timer.start(1000)  # 每1000毫秒(1秒)触发一次
        
        # 设置清理弹幕的定时器，每5分钟清理一半旧数据
        self.clean_danmu_timer = QTimer(self)
        self.clean_danmu_timer.timeout.connect(self.clean_old_danmu)
        self.clean_danmu_timer.start(5 * 60 * 1000)  # 每5分钟触发一次 (5 * 60 * 1000 毫秒)
        
    def add_random_danmu(self):
        """添加一条随机弹幕"""
        # 生成随机数据
        user = random.choice(self.user_names)
        message = random.choice(self.messages)
        time_str = datetime.datetime.now().strftime("%H:%M:%S")
        
        # 创建弹幕数据
        danmu_data = {
            "user": user,
            "message": message,
            "time": time_str,
            "id": self.danmu_counter
        }
        
        # 增加计数器
        self.danmu_counter += 1
        
        # 添加到列表
        display_text = f"[{danmu_data['time']}] {danmu_data['user']}: {danmu_data['message']}"
        self.danmu_list.addItem(display_text)
        
        # 自动滚动到底部
        self.danmu_list.scrollToBottom()
        
        # 为最新的弹幕项设置样式
        last_item = self.danmu_list.item(self.danmu_list.count() - 1)
        last_item.setBackground(QColor(240, 248, 255))  # 淡蓝色背景
        
    def clean_old_danmu(self):
        """清理一半的旧数据"""
        total_count = self.danmu_list.count()
        if total_count > 0:
            # 计算需要删除的数量（一半）
            remove_count = total_count // 2
            
            # 从顶部开始删除旧数据
            for i in range(remove_count):
                # 每次都删除第一项（索引0）
                self.danmu_list.takeItem(0)
                
    def on_item_clicked(self, item):
        """当列表项被点击时显示详细信息"""
        # 在实际应用中，这里会显示真实的详细信息
        row = self.danmu_list.row(item)
      
        
    def clear_danmu(self):
        """清空弹幕列表"""
        self.danmu_list.clear()
        self.danmu_counter = 0  # 重置计数器
        
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 停止所有定时器
        if hasattr(self, 'add_danmu_timer'):
            self.add_danmu_timer.stop()
        if hasattr(self, 'clean_danmu_timer'):
            self.clean_danmu_timer.stop()
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