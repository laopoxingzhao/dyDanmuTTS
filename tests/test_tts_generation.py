#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TTS音频生成测试脚本
测试从弹幕消息到音频播放的完整流程
"""

import sys
import os
import time
import asyncio
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QCoreApplication

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tts.optimized_tts_handler import OptimizedTTSHandler
from config.config import config_manager
from config.log import g_logger
import edge_tts

def test_edge_tts_direct():
    """直接测试edge-tts生成音频"""
    g_logger.info("=== 直接测试edge-tts音频生成 ===")
    
    try:
        # 测试文本
        test_text = "这是一个TTS音频生成测试"
        
        # 创建通信对象
        communicate = edge_tts.Communicate(
            test_text,
            voice="zh-CN-XiaoxiaoNeural",
            rate="+0%",
            volume="+0%"
        )
        
        # 生成音频文件
        output_file = "direct_test.mp3"
        
        # 使用asyncio运行
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            g_logger.info(f"开始生成TTS音频: {test_text}")
            loop.run_until_complete(communicate.save(output_file))
            
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                g_logger.info(f"✅ TTS音频生成成功: {output_file} ({file_size} bytes)")
                return True
            else:
                g_logger.error("❌ TTS音频文件未生成")
                return False
                
        finally:
            loop.close()
            
    except Exception as e:
        g_logger.error(f"❌ edge-tts生成失败: {e}")
        return False

def test_tts_handler():
    """测试完整的TTS处理器"""
    g_logger.info("=== 测试TTS处理器音频生成 ===")
    
    # 创建Qt应用
    app = QCoreApplication(sys.argv)
    
    try:
        # 创建TTS处理器
        tts_handler = OptimizedTTSHandler(config_manager)
        
        g_logger.info("✅ TTS处理器初始化成功")
        
        # 启动TTS处理器
        tts_handler.start()
        g_logger.info("✅ TTS处理器已启动")
        
        # 测试消息
        test_messages = [
            "欢迎来到直播间",
            "感谢关注",
            "主播好棒",
            "666"
        ]
        
        g_logger.info(f"📝 添加 {len(test_messages)} 条测试消息...")
        
        # 添加测试消息
        for i, msg in enumerate(test_messages):
            success = tts_handler.add_tts_item(msg, priority=i+1)
            if success:
                g_logger.info(f"✅ 添加消息 {i+1}: {msg}")
            else:
                g_logger.error(f"❌ 添加消息失败 {i+1}: {msg}")
        
        # 等待处理完成
        g_logger.info("⏳ 等待TTS处理完成...")
        
        # 等待更长时间让所有处理完成
        for i in range(30):  # 最多等待30秒
            time.sleep(1)
            stats = tts_handler.get_stats()
            
            g_logger.debug(f"进度统计: 播放={stats['total_played']}, "
                         f"队列大小={stats['queue_size']}, "
                         f"缓存命中={stats['cache_hits']}, "
                         f"缓存未命中={stats['cache_misses']}")
            
            # 如果队列为空且有一些播放完成，认为处理完成
            if stats['queue_size'] == 0 and stats['total_played'] > 0:
                g_logger.info("✅ TTS处理完成")
                break
        
        # 获取最终统计
        final_stats = tts_handler.get_stats()
        g_logger.info(f"📊 最终统计: {final_stats}")
        
        # 检查是否有生成的音频文件
        cache_dir = "output/cache"
        if os.path.exists(cache_dir):
            cache_files = [f for f in os.listdir(cache_dir) if f.endswith('.mp3')]
            g_logger.info(f"📁 缓存目录中有 {len(cache_files)} 个音频文件")
            for file in cache_files[:5]:  # 只显示前5个
                g_logger.info(f"   - {file}")
        
        # 停止TTS处理器
        tts_handler.stop()
        g_logger.info("✅ TTS处理器已停止")
        
        return final_stats['total_played'] > 0
        
    except Exception as e:
        g_logger.error(f"❌ TTS处理器测试失败: {e}")
        return False

def test_audio_generation_only():
    """仅测试音频生成，不播放"""
    g_logger.info("=== 仅测试TTS音频生成 ===")
    
    try:
        # 创建TTS处理器但不启动
        tts_handler = OptimizedTTSHandler(config_manager)
        
        # 手动创建TTS项目
        from tts.optimized_tts_handler import TTSItem
        tts_item = TTSItem(
            priority=1,
            content="这是一个独立的TTS测试",
            voice="zh-CN-XiaoxiaoNeural",
            rate="+0%",
            volume="+0%"
        )
        
        # 直接生成音频
        g_logger.info("🔧 开始生成音频...")
        audio_file = tts_handler._generate_audio_sync(tts_item)
        
        if audio_file and os.path.exists(audio_file):
            file_size = os.path.getsize(audio_file)
            g_logger.info(f"✅ 音频生成成功: {audio_file} ({file_size} bytes)")
            
            # 播放测试
            from tool.qt_audio_player import get_audio_player
            player = get_audio_player()
            
            if player.initialize():
                g_logger.info("🔊 测试播放生成的音频...")
                success = player.play_file(audio_file, wait_for_completion=True)
                if success:
                    g_logger.info("✅ 音频播放成功")
                    return True
                else:
                    g_logger.error("❌ 音频播放失败")
            else:
                g_logger.error("❌ 音频播放器初始化失败")
            
            # 清理文件
            if os.path.exists(audio_file):
                os.remove(audio_file)
                g_logger.info("🧹 清理测试文件")
        else:
            g_logger.error("❌ 音频生成失败")
        
        return False
        
    except Exception as e:
        g_logger.error(f"❌ 音频生成测试失败: {e}")
        return False

if __name__ == '__main__':
    print("TTS音频生成测试脚本")
    print("=" * 50)
    
    # 选择测试模式
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    else:
        mode = "direct"
    
    success = False
    
    if mode == "direct":
        success = test_edge_tts_direct()
    elif mode == "handler":
        success = test_tts_handler()
    elif mode == "generate":
        success = test_audio_generation_only()
    elif mode == "all":
        success1 = test_edge_tts_direct()
        success2 = test_audio_generation_only()
        success3 = test_tts_handler()
        success = success1 and success2 and success3
    else:
        print("用法:")
        print("  python test_tts_generation.py direct   # 直接测试edge-tts")
        print("  python test_tts_generation.py handler  # 测试TTS处理器")
        print("  python test_tts_generation.py generate # 仅测试音频生成")
        print("  python test_tts_generation.py all      # 测试所有功能")
        sys.exit(1)
    
    if success:
        print("\n[SUCCESS] TTS测试通过")
        sys.exit(0)
    else:
        print("\n[FAILED] TTS测试失败")
        sys.exit(1)