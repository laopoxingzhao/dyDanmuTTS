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
import logging
import atexit
import signal

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.live_manager import DouyinLiveWebFetcher
from tts.play_audio_async import stop_audio_player

logger = logging.getLogger(__name__)

# 配置全局日志（可根据需要在其他入口处调整）
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')

# 在程序退出时确保音频播放器被停止
try:
    atexit.register(stop_audio_player)
except Exception:
    logging.exception("注册退出钩子 stop_audio_player 失败")

def _signal_handler(signum, frame):
    stop_audio_player()
    sys.exit(0)

for sig in (signal.SIGINT, signal.SIGTERM):
    try:
        signal.signal(sig, _signal_handler)
    except Exception:
        # Windows 下对某些信号的支持有限，忽略注册失败
        pass


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
    logger.info(usage)


def run_command_line_mode(live_id):
    """运行命令行模式"""
    try:
        logger.info("正在连接直播间: %s", live_id)
        room = DouyinLiveWebFetcher(live_id)
        room.start()
    except KeyboardInterrupt:
        logger.info("程序已退出")
    except Exception as e:
        logger.exception("发生错误: %s", e)


def run_gui_mode():
    """运行GUI模式"""
    try:
        from ui.main_gui import main as gui_main
        gui_main()
    except ImportError as e:
        logger.exception("无法启动GUI界面: %s", e)
        logger.error("请确保已安装PyQt5: pip install PyQt5")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        show_usage()
    elif sys.argv[1] == 'gui':
        run_gui_mode()
    else:
        live_id = sys.argv[1]
        run_command_line_mode(live_id)