import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 设置窗口标题和大小
        self.setWindowTitle("我的第一个PyQt应用")
        self.setGeometry(100, 100, 400, 300)  # x, y, width, height
        
        # 创建按钮
        self.button = QPushButton("点击我", self)
        self.button.setGeometry(150, 150, 100, 30)
        self.button.clicked.connect(self.button_clicked)
        
    def button_clicked(self):
        print("按钮被点击了!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())