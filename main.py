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


# def run_command_line_mode(live_id):
#     """运行命令行模式"""
#     try:
#         # 尝试导入DouyinLiveWebFetcher类
#         try:
#             from liveMan import DouyinLiveWebFetcher
#             print(f"正在连接直播间: {live_id}")
#             room = DouyinLiveWebFetcher(live_id)
#             room.start()
#         except ImportError:
#             print("错误：找不到liveMan模块，请确保项目文件完整")
#     except KeyboardInterrupt:
#         print("\n程序已退出")
#     except Exception as e:
#         print(f"发生错误: {e}")


def run_gui_mode():
    """运行GUI模式"""
    try:
        from PyQt5.QtWidgets import QApplication
        from ui.room_input_ui import RoomInputWindow
        from ui.danmu_display_ui import DanmuDisplayWindow
        import sys
        from threading import Thread
        
        # 尝试导入DouyinLiveWebFetcher类
        try:
            from liveMan import DouyinLiveWebFetcher
            has_fetcher = True
        except ImportError:
            print("警告：找不到liveMan模块，将无法获取实际弹幕数据")
            DouyinLiveWebFetcher = None
            has_fetcher = False

            
        app = QApplication(sys.argv)
        room_window = RoomInputWindow()
        
        # 定义处理房间选择的函数
        def handle_room_selected(room_id):
            # 隐藏房间选择窗口
            room_window.hide()
            
            # 创建并显示弹幕窗口
            danmu_window = DanmuDisplayWindow(room_id)
            
            # 如果有DouyinLiveWebFetcher类，则启动弹幕抓取
            if has_fetcher:
                # 创建弹幕抓取器
                fetcher = DouyinLiveWebFetcher(room_id)
                
                # 定义处理消息的函数
                def handle_message(msg):
                    # 将消息发送到UI线程
                    danmu_window.danmu_received.emit(msg)
                    
                def handle_stats(stats):
                    # 将统计数据发送到UI线程
                    danmu_window.stats_updated.emit(stats)
                
                # 注册消息处理器
                fetcher.on_message(handle_message)
                fetcher.on_stats(handle_stats)
                
                # 在独立线程中启动弹幕抓取
                def start_fetching():
                    fetcher.start()
                
                fetch_thread = Thread(target=start_fetching)
                fetch_thread.daemon = True
                fetch_thread.start()
            
            # 显示弹幕窗口
            danmu_window.show()
        
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
        show_usage()
    elif sys.argv[1] == 'gui':
        run_gui_mode()
    else:
        live_id = sys.argv[1]
        run_command_line_mode(live_id)