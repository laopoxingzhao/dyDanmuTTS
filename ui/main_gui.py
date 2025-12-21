#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
抖音直播弹幕抓取工具 GUI 入口
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QGroupBox
)
from PyQt5.QtCore import Qt
from ui.douyin_gui import DouyinLiveGUI


class MainGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.douyin_gui = None
        self.init_ui()

    def init_ui(self):
        # 设置窗口标题和大小
        self.setWindowTitle('抖音直播弹幕抓取工具')
        self.setGeometry(300, 300, 400, 200)

        # 创建主布局
        main_layout = QVBoxLayout()

        # 创建说明区域
        info_group = QGroupBox("功能说明")
        info_layout = QVBoxLayout()

        info_label = QLabel("请选择您要使用的功能:")
        info_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(info_label)

        info_group.setLayout(info_layout)
        main_layout.addWidget(info_group)

        # 创建按钮区域
        button_layout = QHBoxLayout()

        # 抖音直播弹幕抓取按钮
        douyin_btn = QPushButton("抖音直播弹幕抓取")
        douyin_btn.clicked.connect(self.open_douyin_gui)
        button_layout.addWidget(douyin_btn)

        # 退出按钮
        exit_btn = QPushButton("退出")
        exit_btn.clicked.connect(self.close)
        button_layout.addWidget(exit_btn)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def open_douyin_gui(self):
        """打开抖音直播弹幕抓取GUI"""
        if self.douyin_gui is None or not self.douyin_gui.isVisible():
            self.douyin_gui = DouyinLiveGUI()
            self.douyin_gui.show()
        else:
            self.douyin_gui.raise_()
            self.douyin_gui.activateWindow()


def main():
    app = QApplication(sys.argv)
    window = MainGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()