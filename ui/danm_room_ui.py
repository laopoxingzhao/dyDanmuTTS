from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QRect
import sys

class Room(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.show()
        

    def init_ui(self):
        self.setWindowTitle("Douyin Live Danmu")
        # 设置窗口尺寸并居中显示
        self.setGeometry(self.calculate_center_rect(800, 600))

        
    def calculate_center_rect(self, width, height):
        """计算居中矩形"""
        # 获取屏幕尺寸
        screen_geometry = self.screen().availableGeometry()
        # 计算居中位置
        x = (screen_geometry.width() - width) // 2
        y = (screen_geometry.height() - height) // 2
        return QRect(x, y, width, height)

    