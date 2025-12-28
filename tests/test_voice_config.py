#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试不同语音配置的TTS生成
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

def test_all_voices():
    """测试所有可用的语音"""
    g_logger.info("=== 测试所有语音配置 ===")
    
    # 语音映射
    voice_map = {
        0: "zh-CN-XiaoxiaoNeural",  # 女声
        1: "zh-CN-YunxiNeural",    # 男声
        2: "zh-HK-HiuGaaiNeural",  # 粤语女声
        3: "zh-HK-HiuMaanNeural",  # 粤语男声
        4: "en-US-JennyNeural",     # 英文女声
        5: "en-US-GuyNeural"        # 英文男声
    }
    
    test_text = "这是一个语音测试，欢迎使用dyDanmuTTS系统"
    
    for voice_index, voice_name in voice_map.items():
        g_logger.info(f"\n🎤 测试语音 {voice_index}: {voice_name}")
        
        try:
            # 创建通信对象
            communicate = edge_tts.Communicate(
                test_text,
                voice=voice_name,
                rate="+0%",
                volume="+0%"
            )
            
            # 生成音频文件
            output_file = f"voice_test_{voice_index}_{voice_name.split('-')[-1]}.mp3"
            
            # 使用asyncio运行
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                start_time = time.time()
                loop.run_until_complete(communicate.save(output_file))
                generation_time = time.time() - start_time
                
                if os.path.exists(output_file):
                    file_size = os.path.getsize(output_file)
                    g_logger.info(f"✅ 语音 {voice_index} 生成成功: {file_size} bytes, 耗时: {generation_time:.2f}s")
                else:
                    g_logger.error(f"❌ 语音 {voice_index} 生成失败: 文件不存在")
                    
            finally:
                loop.close()
                
        except Exception as e:
            g_logger.error(f"❌ 语音 {voice_index} 测试失败: {e}")

def test_config_based_voice():
    """根据配置文件测试语音"""
    g_logger.info("\n=== 根据配置文件测试语音 ===")
    
    try:
        # 创建TTS处理器
        tts_handler = OptimizedTTSHandler(config_manager)
        
        # 获取当前配置
        current_voice_index = config_manager.tts_settings.voice
        current_voice_name = tts_handler._get_voice_name(current_voice_index)
        
        g_logger.info(f"📋 当前配置语音: {current_voice_index} ({current_voice_name})")
        g_logger.info(f"🔊 当前音量: {config_manager.tts_settings.volume}")
        g_logger.info(f"⚡ 当前语速: {config_manager.tts_settings.speed}")
        
        # 测试当前配置的语音
        test_text = "这是根据配置文件设置的语音测试"
        
        # 手动创建TTS项目
        from tts.optimized_tts_handler import TTSItem
        tts_item = TTSItem(
            priority=1,
            content=test_text,
            voice=current_voice_name,
            rate=tts_handler.rate,
            volume=tts_handler.volume
        )
        
        g_logger.info(f"🎵 使用配置语音生成音频...")
        g_logger.info(f"   - 语音: {current_voice_name}")
        g_logger.info(f"   - 语速: {tts_handler.rate}")
        g_logger.info(f"   - 音量: {tts_handler.volume}")
        
        # 生成音频
        audio_file = tts_handler._generate_audio_sync(tts_item)
        
        if audio_file and os.path.exists(audio_file):
            file_size = os.path.getsize(audio_file)
            g_logger.info(f"✅ 配置语音生成成功: {file_size} bytes")
            
            # 播放测试
            from tool.qt_audio_player import get_audio_player
            player = get_audio_player()
            
            if player.initialize():
                g_logger.info("🔊 测试播放配置语音生成的音频...")
                success = player.play_file(audio_file, wait_for_completion=True)
                if success:
                    g_logger.info("✅ 配置语音播放成功")
                    return True
                else:
                    g_logger.error("❌ 配置语音播放失败")
            else:
                g_logger.error("❌ 音频播放器初始化失败")
            
            # 清理文件
            if os.path.exists(audio_file):
                os.remove(audio_file)
                g_logger.info("🧹 清理测试文件")
        else:
            g_logger.error("❌ 配置语音生成失败")
        
        return False
        
    except Exception as e:
        g_logger.error(f"❌ 配置语音测试失败: {e}")
        return False

def test_voice_switching():
    """测试语音切换功能"""
    g_logger.info("\n=== 测试语音切换功能 ===")
    
    try:
        # 创建TTS处理器
        tts_handler = OptimizedTTSHandler(config_manager)
        
        # 保存原始配置
        original_voice = config_manager.tts_settings.voice
        
        test_voices = [0, 1, 4]  # 测试女声、男声、英文
        test_text = "这是语音切换测试"
        
        for voice_index in test_voices:
            g_logger.info(f"🔄 切换到语音 {voice_index}")
            
            # 更新配置
            config_manager.update_tts_setting("voice", voice_index)
            
            # 重新加载设置
            tts_handler._load_tts_settings()
            
            # 生成并播放
            from tts.optimized_tts_handler import TTSItem
            tts_item = TTSItem(
                priority=1,
                content=f"{test_text}，当前使用语音{voice_index}",
                voice=tts_handler.voice,
                rate=tts_handler.rate,
                volume=tts_handler.volume
            )
            
            audio_file = tts_handler._generate_audio_sync(tts_item)
            if audio_file and os.path.exists(audio_file):
                from tool.qt_audio_player import get_audio_player
                player = get_audio_player()
                if player.initialize():
                    player.play_file(audio_file, wait_for_completion=True)
                    g_logger.info(f"✅ 语音 {voice_index} 测试完成")
                
                # 清理文件
                if os.path.exists(audio_file):
                    os.remove(audio_file)
            
            time.sleep(1)  # 间隔1秒
        
        # 恢复原始配置
        config_manager.update_tts_setting("voice", original_voice)
        tts_handler._load_tts_settings()
        
        g_logger.info(f"🔄 已恢复原始语音配置: {original_voice}")
        return True
        
    except Exception as e:
        g_logger.error(f"❌ 语音切换测试失败: {e}")
        return False

if __name__ == '__main__':
    print("语音配置测试脚本")
    print("=" * 50)
    
    # 选择测试模式
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    else:
        mode = "config"
    
    success = False
    
    if mode == "all":
        success = test_all_voices()
    elif mode == "config":
        success = test_config_based_voice()
    elif mode == "switch":
        success = test_voice_switching()
    elif mode == "all_test":
        success1 = test_all_voices()
        success2 = test_config_based_voice()
        success3 = test_voice_switching()
        success = success1 and success2 and success3
    else:
        print("用法:")
        print("  python test_voice_config.py all      # 测试所有语音")
        print("  python test_voice_config.py config   # 测试配置文件语音")
        print("  python test_voice_config.py switch   # 测试语音切换")
        print("  python test_voice_config.py all_test # 测试所有功能")
        sys.exit(1)
    
    if success:
        print("\n[SUCCESS] 语音配置测试通过")
        sys.exit(0)
    else:
        print("\n[FAILED] 语音配置测试失败")
        sys.exit(1)