#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TTS优化功能测试脚本

测试所有优化功能：
1. 智能队列管理
2. 音频缓存
3. 异步处理
4. 内存管理
5. 性能监控
"""

import sys
import time
import threading
from ui.optimized_danmu_controller import OptimizedDanmuController
from config.config import config_manager
from config.log import g_logger


def test_basic_functionality():
    """测试基本功能"""
    print("=== 测试基本功能 ===")
    
    controller = OptimizedDanmuController()
    
    try:
        # 启动控制器
        controller.start("209868919402")  # 测试房间ID
        print("✓ 控制器启动成功")
        
        # 等待一段时间接收消息
        print("等待接收弹幕消息...")
        time.sleep(10)
        
        # 获取性能统计
        stats = controller.get_performance_stats()
        print(f"✓ 性能统计: {stats}")
        
        # 获取内存统计
        memory_stats = controller.get_memory_stats()
        print(f"✓ 内存统计: {memory_stats}")
        
        # 测试强制播放
        test_result = controller.force_play_message("这是一条测试消息", priority=1)
        print(f"✓ 强制播放测试: {'成功' if test_result else '失败'}")
        
        # 测试暂停/恢复
        pause_result = controller.pause_tts()
        print(f"✓ 暂停TTS: {'成功' if pause_result else '失败'}")
        
        time.sleep(2)
        
        resume_result = controller.resume_tts()
        print(f"✓ 恢复TTS: {'成功' if resume_result else '失败'}")
        
        # 测试清空缓存
        cache_result = controller.clear_tts_cache()
        print(f"✓ 清空缓存: {'成功' if cache_result else '失败'}")
        
        # 测试强制内存清理
        cleanup_result = controller.force_memory_cleanup()
        print(f"✓ 强制内存清理: {'成功' if cleanup_result else '失败'}")
        
    except Exception as e:
        print(f"✗ 基本功能测试失败: {e}")
    finally:
        controller.cleanup()
        print("✓ 控制器已清理")


def test_queue_performance():
    """测试队列性能"""
    print("\n=== 测试队列性能 ===")
    
    from tool.optimized_queue import OptimizedTtsQueue
    
    # 创建测试队列
    queue = OptimizedTtsQueue(
        dedup_time_window=5,
        min_interval=1,
        max_queue_size=20,
        enable_smart_filter=True
    )
    
    try:
        # 测试添加消息
        test_messages = [
            ("WebcastChatMessage", "你好", "用户1"),
            ("WebcastChatMessage", "666", "用户2"),
            ("WebcastGiftMessage", "", "用户3", "火箭", 1),
            ("WebcastSocialMessage", "", "用户4"),
            ("WebcastChatMessage", "你好", "用户1"),  # 重复消息
            ("WebcastChatMessage", "主播真厉害", "用户5"),
        ]
        
        start_time = time.time()
        
        for msg_type, content, user_name, *args in test_messages:
            gift_name = args[0] if len(args) > 0 else None
            gift_count = args[1] if len(args) > 1 else None
            
            result = queue.put(msg_type, content, user_name, gift_name, gift_count)
            print(f"添加消息: {content[:20]}... -> {'成功' if result else '被过滤'}")
        
        queue_time = time.time() - start_time
        print(f"✓ 队列添加耗时: {queue_time:.3f}秒")
        
        # 获取队列统计
        stats = queue.get_stats()
        print(f"✓ 队列统计: {stats}")
        
        # 测试消息获取
        print("获取队列中的消息:")
        count = 0
        while not queue.empty() and count < 5:
            item = queue.get()
            if item:
                print(f"  {count+1}. {item['content'][:30]}... (优先级: {item['priority']})")
                count += 1
            else:
                break
        
        print(f"✓ 成功获取 {count} 条消息")
        
    except Exception as e:
        print(f"✗ 队列性能测试失败: {e}")


def test_audio_cache():
    """测试音频缓存"""
    print("\n=== 测试音频缓存 ===")
    
    from tts.optimized_tts_handler import init_optimized_tts_handler
    
    try:
        # 初始化TTS处理器
        tts_handler = init_optimized_tts_handler(config_manager)
        tts_handler.start()
        print("✓ TTS处理器启动成功")
        
        # 测试预加载
        test_phrases = [
            "欢迎来到直播间",
            "感谢关注",
            "666",
            "主播真厉害"
        ]
        
        start_time = time.time()
        
        for phrase in test_phrases:
            result = tts_handler.preload_audio(phrase)
            print(f"预加载: {phrase} -> {'成功' if result else '失败'}")
        
        preload_time = time.time() - start_time
        print(f"✓ 预加载耗时: {preload_time:.3f}秒")
        
        # 测试缓存命中
        print("测试缓存命中:")
        for phrase in test_phrases:
            cached_file = tts_handler.audio_cache.get(
                phrase, tts_handler.voice, tts_handler.rate, tts_handler.volume
            )
            print(f"  {phrase} -> {'命中缓存' if cached_file else '未命中'}")
        
        # 获取TTS统计
        tts_stats = tts_handler.get_stats()
        print(f"✓ TTS统计: {tts_stats}")
        
        tts_handler.stop()
        print("✓ TTS处理器已停止")
        
    except Exception as e:
        print(f"✗ 音频缓存测试失败: {e}")


def test_memory_management():
    """测试内存管理"""
    print("\n=== 测试内存管理 ===")
    
    from tool.memory_manager import MemoryManager
    
    try:
        # 创建内存管理器
        manager = MemoryManager(
            max_memory_mb=100,
            cleanup_interval=5,
            temp_dirs=["test_temp"]
        )
        
        manager.start()
        print("✓ 内存管理器启动成功")
        
        # 创建一些测试文件
        import os
        import tempfile
        
        test_dir = "test_temp"
        os.makedirs(test_dir, exist_ok=True)
        
        test_files = []
        for i in range(10):
            temp_file = os.path.join(test_dir, f"test_{i}.tmp")
            with open(temp_file, 'w') as f:
                f.write("x" * 1024)  # 1KB文件
            test_files.append(temp_file)
        
        print(f"✓ 创建了 {len(test_files)} 个测试文件")
        
        # 等待清理
        print("等待自动清理...")
        time.sleep(8)
        
        # 检查清理结果
        remaining_files = [f for f in test_files if os.path.exists(f)]
        print(f"✓ 清理后剩余文件: {len(remaining_files)}")
        
        # 获取内存统计
        memory_stats = manager.get_cleanup_stats()
        print(f"✓ 内存统计: {memory_stats}")
        
        # 强制清理
        manager.force_cleanup()
        print("✓ 强制清理完成")
        
        manager.stop()
        print("✓ 内存管理器已停止")
        
        # 清理测试目录
        import shutil
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
            print("✓ 测试目录已清理")
        
    except Exception as e:
        print(f"✗ 内存管理测试失败: {e}")


def test_audio_player():
    """测试音频播放器"""
    print("\n=== 测试音频播放器 ===")
    
    from tool.audio_player import get_audio_player
    
    try:
        player = get_audio_player()
        
        # 初始化播放器
        result = player.initialize()
        print(f"✓ 音频播放器初始化: {'成功' if result else '失败'}")
        
        # 获取设备信息
        device_info = player.get_device_info()
        print(f"✓ 音频设备信息: {device_info}")
        
        # 测试音量设置
        player.set_volume(0.5)
        volume = player.get_volume()
        print(f"✓ 音量设置: {volume}")
        
        # 获取播放统计
        stats = player.get_stats()
        print(f"✓ 播放统计: {stats}")
        
        player.shutdown()
        print("✓ 音频播放器已关闭")
        
    except Exception as e:
        print(f"✗ 音频播放器测试失败: {e}")


def main():
    """主测试函数"""
    print("开始TTS优化功能测试...")
    print("=" * 50)
    
    try:
        # 运行各项测试
        test_basic_functionality()
        test_queue_performance()
        test_audio_cache()
        test_memory_management()
        test_audio_player()
        
        print("\n" + "=" * 50)
        print("✓ 所有测试完成！")
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n✗ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()