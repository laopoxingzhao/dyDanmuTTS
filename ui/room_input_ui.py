import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTextEdit, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QCloseEvent


class RoomInputWindow(QMainWindow):
    # 定义信号，用于传递房间ID
    room_selected = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        # 设置窗口属性
        self.setWindowTitle("抖音直播间弹幕抓取工具")
        self.setGeometry(100, 100, 500, 400)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # 标题标签
        title_label = QLabel("抖音直播间弹幕抓取工具")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 20px;")
        main_layout.addWidget(title_label)
        
        # 房间ID输入区域
        room_id_layout = QHBoxLayout()
        room_id_label = QLabel("直播间ID:")
        self.room_id_input = QLineEdit()
        self.room_id_input.setPlaceholderText("请输入抖音直播间ID")
        self.room_id_input.setMinimumWidth(200)
        
        room_id_layout.addWidget(room_id_label)
        room_id_layout.addWidget(self.room_id_input)
        main_layout.addLayout(room_id_layout)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 开始抓取按钮
        self.start_button = QPushButton("开始抓取")
        self.start_button.clicked.connect(self.start_capture)
        
        # 退出按钮
        self.exit_button = QPushButton("退出")
        self.exit_button.clicked.connect(self.close)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.exit_button)
        main_layout.addLayout(button_layout)
        
        # 说明文本区域
        instruction_text = QTextEdit()
        instruction_text.setReadOnly(True)
        instruction_text.setMaximumHeight(150)
        instruction_text.setHtml("""
        <h3>使用说明:</h3>
        <ol>
            <li>在上方输入框中输入抖音直播间ID</li>
            <li>点击"开始抓取"按钮启动弹幕监听</li>
            <li>程序将在新窗口中显示实时弹幕信息</li>
        </ol>
        <p><b>注意:</b> 直播间ID是URL中的数字部分，例如: https://live.douyin.com/<span style="color:red">123456789</span></p>
        """)
        main_layout.addWidget(instruction_text)
        
        # 设置焦点到输入框
        self.room_id_input.setFocus()
        
        # 支持回车键启动
        self.room_id_input.returnPressed.connect(self.start_capture)
        
    def start_capture(self):
        """开始抓取按钮的槽函数"""
        room_id = self.room_id_input.text().strip()
        
        # 验证输入
        if not room_id:
            QMessageBox.warning(self, "输入错误", "请输入直播间ID")
            return
            
        if not room_id.isdigit():
            QMessageBox.warning(self, "输入错误", "直播间ID应该是纯数字")
            return
        
        # 显示确认对话框
        reply = QMessageBox.question(
            self, 
            "确认", 
            f"确认要抓取直播间 {room_id} 的弹幕吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 发送房间ID信号
            self.room_selected.emit(room_id)
            # 关闭当前窗口
            self.close()

    def closeEvent(self, event: QCloseEvent):
        """窗口关闭事件"""
        # 确保应用程序正常退出
        event.accept()


def main():
    """主函数 - 演示UI使用"""
    app = QApplication(sys.argv)
    window = RoomInputWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()