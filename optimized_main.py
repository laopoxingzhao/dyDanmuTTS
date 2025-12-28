#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
优化版抖音直播弹幕抓取工具主入口

本版本集成了以下优化功能:
1. 智能TTS队列管理和优先级处理
2. 音频缓存机制避免重复生成
3. 异步音频生成和播放
4. 智能消息去重和过滤
5. 性能监控和统计
6. 优化的内存使用和临时文件管理
"""

import sys
import os
from threading import Thread
from config.log import g_logger

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui.optimized_danmu_ui import OptimizedRoom

class OptimizedGuiRunner:
    def __init__(self):
        g_logger.info("正在启动优化版GUI界面...")
        
    def run(self):
        from PyQt5.QtWidgets import QApplication
        import sys              
        app = QApplication(sys.argv)
        
        # 启动优化版弹幕控制台界面
        self.room_window = OptimizedRoom()
        
        self.room_window.show()
        sys.exit(app.exec_())

def run_command_line_mode(live_id):
    """运行命令行模式（使用优化版本）"""
    from ui.optimized_danmu_controller import OptimizedDanmuController
    
    # 创建优化的弹幕控制器
    controller = OptimizedDanmuController()
    
    try:
        # 启动弹幕控制器
        controller.start(live_id)
        g_logger.info(f"已启动优化版弹幕控制器，房间ID: {live_id}")
        
        # 保持运行
        while True:
            import time
            time.sleep(1)
            
            # 打印统计信息
            stats = controller.get_performance_stats()
            if stats['total_messages'] % 10 == 0:  # 每10条消息打印一次
                g_logger.info(f"统计: 总消息={stats['total_messages']}, "
                            f"TTS={stats['tts_messages']}, "
                            f"过滤={stats['filtered_messages']}, "
                            f"速率={stats['messages_per_second']:.1f} msg/s")
    
    except KeyboardInterrupt:
        g_logger.info("收到中断信号，正在停止...")
    except Exception as e:
        g_logger.error(f"运行时出错: {e}")
    finally:
        controller.cleanup()
        g_logger.info("程序已退出")

if __name__ == '__main__':
    # 检查命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == "gui":
            # GUI模式
            runner = OptimizedGuiRunner()
            runner.run()
        elif sys.argv[1].isdigit():
            # 命令行模式，使用提供的房间ID
            room_id = sys.argv[1]
            run_command_line_mode(room_id)
        else:
            print("用法:")
            print("  python optimized_main.py gui                    # 启动GUI界面")
            print("  python optimized_main.py <room_id>              # 命令行模式")
            print("  python optimized_main.py                        # 默认启动GUI")
            sys.exit(1)
    else:
        # 默认启动GUI
        runner = OptimizedGuiRunner()
        runner.run()