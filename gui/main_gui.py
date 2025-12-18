import sys
import random
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QLineEdit, QPushButton, QListWidget, QLabel, QGroupBox
)
from PyQt5.QtCore import QTimer, Qt


class DataGeneratorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.data_list = []
        self.init_ui()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.add_data_to_list)
        
    def init_ui(self):
        # 设置窗口标题和大小
        self.setWindowTitle('数据生成器')
        self.setGeometry(300, 300, 400, 300)
        
        # 创建主布局
        main_layout = QVBoxLayout()
        
        # 创建输入区域
        input_group = QGroupBox("输入设置")
        input_layout = QHBoxLayout()
        
        self.input_label = QLabel("请输入数字:")
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("输入一个数字...")
        
        self.confirm_button = QPushButton("确认")
        self.confirm_button.clicked.connect(self.start_generation)
        
        input_layout.addWidget(self.input_label)
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.confirm_button)
        
        input_group.setLayout(input_layout)
        
        # 创建数据显示区域
        display_group = QGroupBox("数据列表")
        display_layout = QVBoxLayout()
        
        self.data_list_widget = QListWidget()
        
        display_layout.addWidget(self.data_list_widget)
        display_group.setLayout(display_layout)
        
        # 添加组件到主布局
        main_layout.addWidget(input_group)
        main_layout.addWidget(display_group)
        
        self.setLayout(main_layout)
    
    def start_generation(self):
        # 获取输入的数字
        input_text = self.input_field.text()
        try:
            number = float(input_text)
            # 清空之前的数据
            self.data_list.clear()
            self.data_list_widget.clear()
            
            # 添加初始数据
            self.data_list.append(number)
            self.data_list_widget.addItem(str(number))
            
            # 启动定时器，每秒添加一次数据
            self.timer.start(1000)
            
            # 禁用输入和按钮，防止重复点击
            self.input_field.setEnabled(False)
            self.confirm_button.setEnabled(False)
            self.confirm_button.setText("生成中...")
            
        except ValueError:
            self.data_list_widget.addItem("请输入有效的数字!")
    
    def add_data_to_list(self):
        # 如果列表为空则停止定时器
        if len(self.data_list) == 0:
            return
            
        # 生成新数据（这里我们简单地在前一个数字基础上加一个随机数）
        last_number = self.data_list[-1]
        new_number = last_number + random.uniform(-10, 10)  # 添加-10到10之间的随机数
        
        # 添加到数据列表和UI列表
        self.data_list.append(new_number)
        self.data_list_widget.addItem(f"{new_number:.2f}")
        
        # 限制数据列表长度为100，超过则删除最旧的数据
        if len(self.data_list) > 100:
            self.data_list.pop(0)  # 删除最旧的数据
            self.data_list_widget.takeItem(0)  # 删除对应的UI项
        
        # 自动滚动到底部
        self.data_list_widget.scrollToBottom()


def main():
    app = QApplication(sys.argv)
    window = DataGeneratorApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()