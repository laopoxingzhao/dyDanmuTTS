#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试弹幕界面功能
"""

import sys
from PyQt5.QtWidgets import QApplication
from ui.danm_room_ui import Room

def test_ui():
    """测试UI界面"""
    app = QApplication(sys.argv)
    
    # 创建界面
    window = Room()
    
    # 显示界面
    window.show()
    
    print("UI界面启动成功")
    print("可以测试以下功能：")
    print("  1. 输入直播间ID并连接")
    print("  2. 勾选/取消勾选消息类型筛选")
    print("  3. 查看弹幕列表显示")
    print("  4. 清空弹幕列表")
    
    return app.exec_()

if __name__ == '__main__':
    test_ui()