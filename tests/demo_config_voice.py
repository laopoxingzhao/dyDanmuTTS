#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
演示根据配置文件生成对应语言的TTS音频
"""

import sys
import os
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QCoreApplication

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tts.optimized_tts_handler import OptimizedTTSHandler
from config.config import config_manager
from config.log import g_logger

def demo_config_voice():
    """演示配置文件中的语音设置"""
    g_logger.info("=== 演示配置文件语音设置 ===")
    
    # 创建Qt应用
    app = QCoreApplication(sys.argv)
    
    try:
        # 创建TTS处理器
        tts_handler = OptimizedTTSHandler(config_manager)
        
        # 显示当前配置
        g_logger.info("📋 当前TTS配置:")
        g_logger.info(f"   语音索引: {config_manager.tts_settings.voice}")
        g_logger.info(f"   语音名称: {tts_handler.voice}")
        g_logger.info(f"   音量设置: {config_manager.tts_settings.volume}")
        g_logger.info(f"   语速设置: {config_manager.tts_settings.speed}")
        g_logger.info(f"   TTS启用: {config_manager.tts_settings.tts_enabled}")
        
        # 启动TTS处理器
        tts_handler.start()
        g_logger.info("✅ TTS处理器已启动")
        
        # 演示消息
        demo_messages = [
            "欢迎使用dyDanmuTTS系统",
            "当前使用的是配置文件中设置的语音",
            "系统会根据您的配置自动选择对应的语言和音色"
        ]
        
        g_logger.info(f"\n🎵 开始演示播放 {len(demo_messages)} 条消息...")
        
        # 添加演示消息
        for i, msg in enumerate(demo_messages):
            g_logger.info(f"📝 添加消息 {i+1}: {msg}")
            success = tts_handler.add_tts_item(msg, priority=i+1)
            
            if success:
                g_logger.info(f"✅ 消息 {i+1} 添加成功")
            else:
                g_logger.error(f"❌ 消息 {i+1} 添加失败")
            
            time.sleep(0.5)  # 短暂间隔
        
        # 等待所有消息处理完成
        g_logger.info("\n⏳ 等待所有TTS消息处理完成...")
        
        start_time = time.time()
        max_wait_time = 30  # 最多等待30秒
        
        while time.time() - start_time < max_wait_time:
            time.sleep(1)
            stats = tts_handler.get_stats()
            
            if stats['queue_size'] == 0 and stats['total_played'] >= len(demo_messages):
                g_logger.info("✅ 所有消息处理完成")
                break
            
            g_logger.debug(f"处理进度: 播放={stats['total_played']}/{len(demo_messages)}, "
                         f"队列={stats['queue_size']}, "
                         f"缓存命中={stats['cache_hits']}")
        
        # 显示最终统计
        final_stats = tts_handler.get_stats()
        g_logger.info(f"\n📊 最终统计:")
        g_logger.info(f"   总播放数: {final_stats['total_played']}")
        g_logger.info(f"   缓存命中率: {final_stats.get('cache_hit_rate', 0):.2%}")
        g_logger.info(f"   平均生成时间: {final_stats.get('avg_generation_time', 0):.2f}s")
        g_logger.info(f"   平均播放时间: {final_stats.get('avg_playback_time', 0):.2f}s")
        
        # 停止TTS处理器
        tts_handler.stop()
        g_logger.info("✅ TTS处理器已停止")
        
        return final_stats['total_played'] > 0
        
    except Exception as e:
        g_logger.error(f"❌ 演示失败: {e}")
        return False

def show_voice_options():
    """显示所有可用的语音选项"""
    g_logger.info("=== 可用语音选项 ===")
    
    voice_map = {
        0: {"name": "zh-CN-XiaoxiaoNeural", "desc": "中文女声 - 晓晓"},
        1: {"name": "zh-CN-YunxiNeural", "desc": "中文男声 - 云希"},
        2: {"name": "zh-HK-HiuGaaiNeural", "desc": "粤语女声 - 曉儀"},
        3: {"name": "zh-HK-HiuMaanNeural", "desc": "粤语男声 - 曉文"},
        4: {"name": "en-US-JennyNeural", "desc": "英文女声 - Jenny"},
        5: {"name": "en-US-GuyNeural", "desc": "英文男声 - Guy"}
    }
    
    g_logger.info("语音选项列表:")
    for index, info in voice_map.items():
        current = "✅ [当前]" if index == config_manager.tts_settings.voice else "   "
        g_logger.info(f"{current} {index}: {info['desc']}")
        g_logger.info(f"       Edge TTS名称: {info['name']}")
    
    current_voice = voice_map.get(config_manager.tts_settings.voice, {})
    if current_voice:
        g_logger.info(f"\n🎯 当前配置: {current_voice['desc']}")
        g_logger.info(f"   对应配置文件: voice = {config_manager.tts_settings.voice}")

if __name__ == '__main__':
    print("dyDanmuTTS 配置语音演示")
    print("=" * 50)
    
    # 选择演示模式
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    else:
        mode = "demo"
    
    if mode == "options":
        show_voice_options()
    elif mode == "demo":
        success = demo_config_voice()
        
        if success:
            print("\n[SUCCESS] 配置语音演示成功")
            print("✅ TTS系统已根据配置文件正确生成和播放对应语言的音频")
        else:
            print("\n[FAILED] 配置语音演示失败")
        sys.exit(0 if success else 1)
    else:
        print("用法:")
        print("  python demo_config_voice.py options  # 显示所有语音选项")
        print("  python demo_config_voice.py demo     # 演示配置文件语音")
        print("  python demo_config_voice.py          # 默认演示模式")
        sys.exit(1)