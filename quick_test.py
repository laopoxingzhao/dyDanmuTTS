#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
快速测试音频播放器核心功能
"""

import sys
import os
import time
from PyQt5.QtCore import QCoreApplication

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tool.qt_audio_player import QtAudioPlayer
from config.log import g_logger

def quick_test():
    """快速测试音频播放器核心功能"""
    g_logger.info("=== 音频播放器快速测试 ===")
    
    # 创建Qt应用
    app = QCoreApplication(sys.argv)
    
    # 创建音频播放器
    player = QtAudioPlayer()
    
    if not player.initialize():
        g_logger.error("❌ 音频播放器初始化失败")
        return False
    
    g_logger.info("✅ 音频播放器初始化成功")
    
    # 测试设备信息
    device_info = player.get_device_info()
    g_logger.info(f"✅ 设备信息: {device_info}")
    
    # 创建测试音频文件
    test_file = "quick_test.wav"
    try:
        import wave
        import struct
        import math
        
        with wave.open(test_file, 'wb') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(22050)
            
            for i in range(22050):  # 1秒
                value = int(32767 * math.sin(2 * math.pi * 440 * i / 22050))
                f.writeframes(struct.pack('<h', value))
        
        g_logger.info(f"✅ 测试音频文件创建成功: {test_file}")
    except Exception as e:
        g_logger.error(f"❌ 创建测试文件失败: {e}")
        return False
    
    # 测试基本播放（不等待完成）
    g_logger.info("🎵 测试音频播放...")
    success = player.play_file(test_file, wait_for_completion=False)
    
    if success:
        g_logger.info("✅ 音频播放启动成功")
        
        # 等待一小段时间让音频播放
        time.sleep(2)
        
        # 获取统计信息
        stats = player.get_stats()
        g_logger.info(f"📊 播放统计: {stats}")
        
        # 测试音量控制
        player.set_volume(0.5)
        g_logger.info(f"🔊 音量设置为: {player.get_volume()}")
        
        # 测试播放间隔控制
        player.set_min_play_interval(0.5)
        g_logger.info(f"⏱️ 最小播放间隔: {player.get_min_play_interval()}秒")
        
        g_logger.info("✅ 所有测试通过！")
        
        # 清理资源
        player.shutdown()
        if os.path.exists(test_file):
            os.remove(test_file)
        g_logger.info("🧹 清理完成")
        return True
    else:
        g_logger.error("❌ 音频播放启动失败")
        return False

if __name__ == '__main__':
    try:
        result = quick_test()
        sys.exit(0 if result else 1)
    except Exception as e:
        g_logger.error(f"测试过程中出现异常: {e}")
        sys.exit(1)