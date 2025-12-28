#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
音频播放器测试脚本
用于测试优化后的音频播放功能
"""

import sys
import os
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QCoreApplication

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tool.qt_audio_player import QtAudioPlayer
from config.log import g_logger

def test_audio_player():
    """测试音频播放器功能"""
    g_logger.info("开始测试音频播放器...")
    
    # 创建Qt应用（必需的）
    app = QCoreApplication(sys.argv)
    
    # 创建音频播放器
    player = QtAudioPlayer()
    
    if not player.initialize():
        g_logger.error("音频播放器初始化失败")
        return False
    
    # 测试设备信息
    device_info = player.get_device_info()
    g_logger.info(f"音频设备信息: {device_info}")
    
    # 创建测试音频文件（如果不存在）
    test_audio_file = "test.wav"
    if not os.path.exists(test_audio_file):
        g_logger.info("创建测试音频文件...")
        try:
            import wave
            import struct
            import math
            
            # 创建1秒的440Hz正弦波
            sample_rate = 22050
            duration = 1
            frequency = 440
            
            with wave.open(test_audio_file, 'wb') as f:
                f.setnchannels(1)
                f.setsampwidth(2)
                f.setframerate(sample_rate)
                
                for i in range(sample_rate * duration):
                    value = int(32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
                    f.writeframes(struct.pack('<h', value))
            
            g_logger.info(f"测试音频文件创建成功: {test_audio_file}")
        except Exception as e:
            g_logger.error(f"创建测试音频文件失败: {e}")
            return False
    
    try:
        # 测试基本播放
        g_logger.info("测试1: 基本播放功能")
        success = player.play_file(test_audio_file, wait_for_completion=True)
        g_logger.info(f"播放结果: {'成功' if success else '失败'}")
        
        # 测试预加载
        g_logger.info("测试2: 预加载功能")
        preload_success = player.preload_audio(test_audio_file, "test_cache")
        g_logger.info(f"预加载结果: {'成功' if preload_success else '失败'}")
        
        # 测试使用缓存的播放
        g_logger.info("测试3: 使用缓存的播放")
        success = player.play_file(test_audio_file, "test_cache", wait_for_completion=True)
        g_logger.info(f"缓存播放结果: {'成功' if success else '失败'}")
        
        # 测试音量控制
        g_logger.info("测试4: 音量控制")
        player.set_volume(0.5)
        g_logger.info(f"当前音量: {player.get_volume()}")
        
        # 测试播放间隔
        g_logger.info("测试5: 播放间隔控制")
        player.set_min_play_interval(1.0)
        g_logger.info(f"最小播放间隔: {player.get_min_play_interval()}秒")
        
        # 连续播放测试
        start_time = time.time()
        for i in range(3):
            g_logger.info(f"连续播放测试 {i+1}/3")
            success = player.play_file(test_audio_file, f"test_{i}", wait_for_completion=True)
            if not success:
                g_logger.error(f"第{i+1}次播放失败")
        
        total_time = time.time() - start_time
        g_logger.info(f"连续播放完成，总耗时: {total_time:.2f}秒")
        
        # 获取统计信息
        stats = player.get_stats()
        g_logger.info(f"播放统计: {stats}")
        
        g_logger.info("音频播放器测试完成")
        return True
        
    except Exception as e:
        g_logger.error(f"测试过程中出错: {e}")
        return False
    
    finally:
        # 清理资源
        player.shutdown()
        g_logger.info("音频播放器已关闭")

def test_tts_integration():
    """测试TTS集成"""
    g_logger.info("测试TTS集成功能...")
    
    try:
        from tts.optimized_tts_handler import OptimizedTTSHandler
        from config.config import config_manager
        
        # 创建TTS处理器
        tts_handler = OptimizedTTSHandler(config_manager)
        
        # 测试添加TTS项目
        test_messages = [
            "这是第一条测试消息",
            "欢迎来到直播间",
            "感谢关注",
            "666"
        ]
        
        for msg in test_messages:
            success = tts_handler.add_tts_item(msg)
            g_logger.info(f"添加TTS项目 '{msg}': {'成功' if success else '失败'}")
        
        # 启动TTS处理器
        tts_handler.start()
        
        # 等待处理完成
        g_logger.info("等待TTS处理完成...")
        time.sleep(10)
        
        # 获取统计信息
        stats = tts_handler.get_stats()
        g_logger.info(f"TTS统计: {stats}")
        
        # 停止TTS处理器
        tts_handler.stop()
        
        g_logger.info("TTS集成测试完成")
        return True
        
    except Exception as e:
        g_logger.error(f"TTS集成测试失败: {e}")
        return False

if __name__ == '__main__':
    print("音频播放器测试脚本")
    print("=" * 50)
    
    # 选择测试模式
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    else:
        mode = "player"
    
    if mode == "player":
        success = test_audio_player()
    elif mode == "tts":
        success = test_tts_integration()
    elif mode == "both":
        success1 = test_audio_player()
        success2 = test_tts_integration()
        success = success1 and success2
    else:
        print("用法:")
        print("  python test_audio_player.py player    # 测试音频播放器")
        print("  python test_audio_player.py tts       # 测试TTS集成")
        print("  python test_audio_player.py both      # 测试所有功能")
        sys.exit(1)
    
    if success:
        print("\n[SUCCESS] 测试通过")
        sys.exit(0)
    else:
        print("\n[FAILED] 测试失败")
        sys.exit(1)