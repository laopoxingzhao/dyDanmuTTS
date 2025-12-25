from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel,QMessageBox
from PyQt5.QtCore import pyqtSignal

class RoomInputWindow(QWidget):
    room_selected = pyqtSignal(str)  # 定义信号，传递房间ID
    room_closed = pyqtSignal()  # 关闭此ui的信号
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('输入直播间ID')

        self.setGeometry(300, 300, 300, 100)
        
        layout = QVBoxLayout()
        
        # 创建标签
        label = QLabel('请输入直播间ID:')
        layout.addWidget(label)
        
        # 创建输入框
        self.room_input = QLineEdit()
        self.room_input.setPlaceholderText('输入直播间ID...')
        layout.addWidget(self.room_input)
        
        # 创建按钮
        self.submit_button = QPushButton('确定')
        self.submit_button.clicked.connect(self.on_submit)
        layout.addWidget(self.submit_button)
        
        # 回车键也可以触发提交
        self.room_input.returnPressed.connect(self.on_submit)
        
        
        self.setLayout(layout)
        
    def on_submit(self):
        room_id = self.room_input.text().strip()
        if room_id != '' and room_id.isdigit():
            self.room_selected.emit(room_id)  # 发送信号
            self.hide()
        else:
            # 提示框
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle('输入错误')
            msg_box.setText('直播间ID格式不正确！')
            msg_box.setInformativeText('请输入正确的直播间ID（数字）')
            msg_box.exec_()

    def closeEvent(self, event):
        self.room_closed.emit()  # 使用修正后的信号名称
        event.accept()