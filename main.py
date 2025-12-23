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
from threading import Thread
from config.log import g_logger

from ui.room_danmu_ui import RoomDanmuWindow

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
        from ui.room_input_ui import RoomInputWindow
        from dy_danmu.liveMan import DouyinLiveWebFetcher
        import sys              
        app = QApplication(sys.argv)
        self.room_window = RoomInputWindow()
        self.room_window.room_selected.connect(self.danm)
        self.room_window.show()
        sys.exit(app.exec_())

        
    def danm(self, room_id):
        self.danmugui = RoomDanmuWindow(room_id)
        self.danmugui.show()
        self.danmugui.window_closed.connect(self.closeDanmu)
        self.room = DouyinLiveWebFetcher(room_id)
        self.this_thread = Thread(target=self.room.start)
        # this_thread.setDaemon(True)
        self.this_thread.start()
        self.room_window.hide()
    
    def closeDanmu(self):
        self.room_window.show()
        self.room.stop()

if __name__ == '__main__':
    if len(sys.argv) < 2:
      pass
    elif sys.argv[1] == 'gui':
        runer = GuiRunner()
        runer.run()
    else:
        live_id = sys.argv[1]
        run_command_line_mode(live_id)

