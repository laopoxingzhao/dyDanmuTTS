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

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from liveMan import DouyinLiveWebFetcher


def show_usage():
    """显示使用说明"""
    usage = """
抖音直播弹幕抓取工具

使用方式:
1. 命令行模式: python main.py <room_id>
   示例: python main.py 50828500437

2. GUI模式: python main.py gui

3. TTS模式: python live_tts_main.py

注意: 
- 使用前请确保已安装所需依赖: pip install -r requirements.txt
- 需要安装Node.js环境以执行JavaScript签名计算
- 更多信息请查看 README.MD 和 PROJECT_STRUCTURE.md
    """
    print(usage)


def run_command_line_mode(live_id):
    """运行命令行模式"""
    try:
        print(f"正在连接直播间: {live_id}")
        room = DouyinLiveWebFetcher(live_id)
        room.start()
    except KeyboardInterrupt:
        print("\n程序已退出")
    except Exception as e:
        print(f"发生错误: {e}")


def run_gui_mode():
    """运行GUI模式"""
    try:
        from gui.main_gui import main as gui_main
        gui_main()
    except ImportError as e:
        print(f"无法启动GUI界面: {e}")
        print("请确保已安装PyQt5: pip install PyQt5")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        show_usage()
    elif sys.argv[1] == 'gui':
        run_gui_mode()
    else:
        live_id = sys.argv[1]
        run_command_line_mode(live_id)