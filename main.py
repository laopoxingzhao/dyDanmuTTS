#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
抖音直播弹幕抓取工具主入口

本项目支持多种使用方式:
1. 命令行直接运行: python main.py <room_id>
2. GUI界面运行: python main.py gui
3. TTS模式运行: python live_tts_main.py
"""

import sys
import os
from threading import Thread
from config.log import g_logger
from ui.danm_room_ui import Room  # 导入新创建的弹幕界面

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dy_danmu.liveMan import DouyinLiveWebFetcher

def run_command_line_mode(live_id):
    """运行命令行模式"""
   

    live_id = '209868919402'
    room = DouyinLiveWebFetcher(live_id)
    # room.get_room_status() # 失效
    room.start()

class GuiRunner:
    def __init__(self):
        g_logger.info("正在启动GUI界面...")
        
    def run(self):
        from PyQt5.QtWidgets import QApplication
        import sys              
        app = QApplication(sys.argv)
        
        # 直接启动弹幕控制台界面
        self.room_window = Room()  # 使用新的弹幕控制台界面
        
        self.room_window.show()
        sys.exit(app.exec_())

if __name__ == '__main__':
    runer = GuiRunner()
    runer.run()