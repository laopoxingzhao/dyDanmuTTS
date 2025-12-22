#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
抖音直播弹幕抓取工具主入口

本项目支持多种使用方式:
1. 呑令行直接运行: python main.py <room_id>
2. GUI界面运行: python main.py gui
3. TTS模式运行: python live_tts_main.py
"""

import sys
import os

from ui.room_danmu_ui import RoomDanmuWindow

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))



def run_command_line_mode(live_id):
    """运行命令行模式"""


def run_gui_mode():
    """运行GUI模式"""
    try:
        from PyQt5.QtWidgets import QApplication
        from ui.room_input_ui import RoomInputWindow
      
        import sys
        from threading import Thread
              
        app = QApplication(sys.argv)
        room_window = RoomInputWindow()
        
        # 定义处理房间选择的函数
        def handle_room_selected(room_id):
            # 隐藏房间选择窗口
            room_window.hide()
            
            # 保存对room_danmu_window的引用，防止被垃圾回收导致窗口闪退
            room_window.room_danmu_window = RoomDanmuWindow(room_id.strip())
            room_window.room_danmu_window.show()
            # 连接窗口关闭信号，确保窗口关闭后重新显示输入窗口
            room_window.room_danmu_window.window_closed.connect(room_window.show)
            
        # 连接房间选择信号
        room_window.room_selected.connect(handle_room_selected)
        
        # 显示房间选择窗口
        room_window.show()
        sys.exit(app.exec_())
            
    except ImportError as e:
        print(f"无法启动GUI界面: {e}")
        print("请确保已安装PyQt5: pip install PyQt5")


if __name__ == '__main__':
    if len(sys.argv) < 2:
      pass
    elif sys.argv[1] == 'gui':
        run_gui_mode()
    else:
        live_id = sys.argv[1]
        run_command_line_mode(live_id)