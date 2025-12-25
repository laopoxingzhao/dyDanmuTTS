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
from ui.danmu_controller import DanmuController
from ui.room_input_ui import RoomInputWindow  # 导入新创建的输入界面

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
        self.danmcontroller = DanmuController()
      
       
        
    def run(self):
        from PyQt5.QtWidgets import QApplication
        import sys              
        app = QApplication(sys.argv)
        self.room_window = RoomInputWindow()  # 使用新的输入界面
        self.room_window.room_selected.connect(self.danm)
        self.room_window.room_closed.connect(self.closeDanmu)  # 修正信号名称拼写

       

        
        self.room_window.show()
        sys.exit(app.exec_())
        
    def danm(self, room_id):
        g_logger.info(f"开始获取直播间 {room_id} 的弹幕")
        # 创建直播间弹幕获取器实例
        self.danmcontroller.room_id = room_id
          
    
    def closeDanmu(self):
        # 如果有正在运行的弹幕获取实例，则停止它
        if hasattr(self, 'fetcher'):
            self.fetcher.stop()
            g_logger.info("弹幕获取已停止")
        
        self.room_window.show()

if __name__ == '__main__':


    runer = GuiRunner()
    runer.run()
    if len(sys.argv) < 2:
      pass
    # elif sys.argv[1] == 'gui':
    #     runer = GuiRunner()
    #     runer.run()
    else:
        # live_id = sys.argv[1]
        # run_command_line_mode(live_id)

        pass