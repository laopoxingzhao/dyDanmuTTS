#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Qt音频播放器集成测试
"""

import sys
import os
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QCoreApplication

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_qt_audio_player():
    """测试Qt音频播放器"""
    print("=== Qt音频播放器集成测试 ===")
    
    # 创建Qt应用（必需）
    app = QCoreApplication(sys.argv)
    
    try:
        from tool.qt_audio_player import get_qt_audio_player
        
        # 获取音频播放器实例
        audio_player = get_qt_audio_player()
        
        # 测试初始化
        print("1. 测试初始化...")
        success = audio_player.initialize()
        print(f"   初始化结果: {success}")
        
        if not success:
            print("   初始化失败，测试终止")
            return False
        
        # 测试设备信息
        print("2. 获取设备信息...")
        device_info = audio_player.get_device_info()
        print(f"   设备信息: {device_info}")
        
        # 测试预加载
        if os.path.exists('output/test.mp3'):
            print("3. 测试预加载...")
            success = audio_player.preload_audio('output/test.mp3', 'test')
            print(f"   预加载结果: {success}")
            
            # 测试播放（非阻塞）
            print("4. 测试播放...")
            success = audio_player.play_file('output/test.mp3', 'test')
            print(f"   播放开始: {success}")
            
            # 等待播放完成
            print("   等待播放完成...")
            for i in range(50):  # 最多等待5秒
                if not audio_player.is_playing():
                    break
                time.sleep(0.1)
            
            print(f"   播放状态: {'完成' if not audio_player.is_playing() else '仍在播放'}")
        else:
            print("3. 跳过播放测试（没有测试音频文件）")
        
        # 测试音量控制
        print("5. 测试音量控制...")
        audio_player.set_volume(0.5)
        volume = audio_player.get_volume()
        print(f"   设置音量50%，当前音量: {volume}")
        
        # 测试统计信息
        print("6. 获取统计信息...")
        stats = audio_player.get_stats()
        print(f"   统计信息: {stats}")
        
        # 测试清理
        print("7. 测试清理...")
        audio_player.clear_preloaded_cache()
        print("   缓存已清理")
        
        # 关闭播放器
        print("8. 关闭音频播放器...")
        audio_player.shutdown()
        print("   音频播放器已关闭")
        
        print("=== Qt音频播放器测试完成 ===")
        return True
        
    except Exception as e:
        print(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tts_integration():
    """测试TTS集成"""
    print("\n=== TTS处理器集成测试 ===")
    
    try:
        from config.config import config_manager
        
        # 创建Qt应用
        app = QCoreApplication(sys.argv)
        
        # 初始化TTS处理器
        print("1. 初始化TTS处理器...")
        from tts.optimized_tts_handler import init_optimized_tts_handler
        tts_handler = init_optimized_tts_handler(config_manager)
        
        # 启动TTS处理器
        print("2. 启动TTS处理器...")
        tts_handler.start()
        
        # 添加测试消息
        print("3. 添加测试消息...")
        success = tts_handler.add_tts_item("Qt音频播放器集成测试消息", priority=1)
        print(f"   添加消息结果: {success}")
        
        # 等待处理
        print("4. 等待TTS处理...")
        time.sleep(5)
        
        # 获取统计信息
        print("5. 获取TTS统计信息...")
        stats = tts_handler.get_stats()
        print(f"   TTS统计: {stats}")
        
        # 停止TTS处理器
        print("6. 停止TTS处理器...")
        tts_handler.stop()
        
        print("=== TTS处理器集成测试完成 ===")
        return True
        
    except Exception as e:
        print(f"TTS集成测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("开始Qt音频播放器集成测试...")
    
    # 测试Qt音频播放器
    player_test = test_qt_audio_player()
    
    # 测试TTS集成
    tts_test = test_tts_integration()
    
    # 输出测试结果
    print(f"\n=== 测试结果 ===")
    print(f"Qt音频播放器测试: {'通过' if player_test else '失败'}")
    print(f"TTS集成测试: {'通过' if tts_test else '失败'}")
    print(f"总体测试: {'通过' if player_test and tts_test else '失败'}")
    
    return player_test and tts_test

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)