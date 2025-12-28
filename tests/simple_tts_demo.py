#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的TTS音频生成演示脚本（无emoji，适合Windows终端）
"""

import sys
import time
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.config import LiveConfig
from tts.optimized_tts_handler import OptimizedTTSHandler
from config.log import g_logger as logger


async def demo_tts_generation():
    """演示TTS音频生成功能"""
    print("dyDanmuTTS 音频生成演示")
    print("=" * 50)
    
    try:
        # 初始化配置
        config = LiveConfig()
        
        print(f"\n当前配置:")
        print(f"   语音索引: {config.tts_settings.voice}")
        print(f"   音量设置: {config.tts_settings.volume}")
        print(f"   语速设置: {config.tts_settings.speed}")
        
        # 语音选项映射
        voice_map = {
            0: {"name": "zh-CN-XiaoxiaoNeural", "desc": "中文女声 - 晓晓"},
            1: {"name": "zh-CN-YunxiNeural", "desc": "中文男声 - 云希"},
            2: {"name": "zh-HK-HiuGaaiNeural", "desc": "粤语女声 - 曉儀"},
            3: {"name": "zh-HK-HiuMaanNeural", "desc": "粤语男声 - 曉文"},
            4: {"name": "en-US-JennyNeural", "desc": "英文女声 - Jenny"},
            5: {"name": "en-US-GuyNeural", "desc": "英文男声 - Guy"}
        }
        
        current_voice_info = voice_map.get(config.tts_settings.voice, {})
        if current_voice_info:
            print(f"   当前语音: {current_voice_info['desc']}")
            print(f"   Edge TTS: {current_voice_info['name']}")
        
        # 初始化TTS处理器
        tts_handler = OptimizedTTSHandler(config)
        
        print(f"\nTTS处理器初始化中...")
        tts_handler.start()
        print(f"TTS处理器初始化完成")
        
        # 测试消息
        test_messages = [
            "欢迎使用dyDanmuTTS语音合成系统",
            "当前正在使用配置文件中设置的语音",
            "系统会根据您的配置自动生成对应语言和音色的音频",
            "支持中文、粤语、英文等多种语言",
            "音量和语速都可以根据配置进行调整"
        ]
        
        print(f"\n开始生成 {len(test_messages)} 条音频...")
        print("-" * 50)
        
        generated_files = []
        total_start_time = time.time()
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n[{i}/{len(test_messages)}] 生成音频: {message[:20]}...")
            
            start_time = time.time()
            
            try:
                # 生成音频
                audio_file = await tts_handler.generate_audio(message)
                
                generation_time = time.time() - start_time
                file_size = audio_file.stat().st_size if audio_file.exists() else 0
                
                print(f"   [成功] 生成完成")
                print(f"   文件路径: {audio_file}")
                print(f"   文件大小: {file_size:,} bytes")
                print(f"   生成时间: {generation_time:.2f}s")
                
                generated_files.append(audio_file)
                
            except Exception as e:
                print(f"   [失败] 生成错误: {e}")
                logger.error(f"音频生成失败: {message} - {e}")
        
        total_time = time.time() - total_start_time
        
        print(f"\n音频生成完成！")
        print("=" * 50)
        print(f"统计信息:")
        print(f"   总消息数: {len(test_messages)}")
        print(f"   成功生成: {len(generated_files)}")
        print(f"   总耗时: {total_time:.2f}s")
        print(f"   平均耗时: {total_time/len(test_messages):.2f}s")
        
        if generated_files:
            print(f"\n生成的音频文件:")
            for i, audio_file in enumerate(generated_files, 1):
                print(f"   {i}. {audio_file}")
        
        print(f"\n提示:")
        print(f"   - 生成的音频文件保存在 output/cache/ 目录")
        print(f"   - 可以使用任何音频播放器播放这些文件")
        print(f"   - 配置文件位置: config/app_config.json")
        print(f"   - 修改配置后重新运行此脚本测试不同语音")
        
        # 停止TTS处理器
        tts_handler.stop()
        print(f"\nTTS处理器已停止")
        
    except Exception as e:
        logger.error(f"演示过程中发生错误: {e}")
        print(f"错误: {e}")
        return False
    
    return True


async def demo_voice_comparison():
    """演示不同语音的对比"""
    print("\n不同语音对比演示")
    print("=" * 50)
    
    # 语音选项映射
    voice_map = {
        0: {"name": "zh-CN-XiaoxiaoNeural", "desc": "中文女声 - 晓晓", "language": "中文", "gender": "女"},
        1: {"name": "zh-CN-YunxiNeural", "desc": "中文男声 - 云希", "language": "中文", "gender": "男"},
        2: {"name": "zh-HK-HiuGaaiNeural", "desc": "粤语女声 - 曉儀", "language": "粤语", "gender": "女"},
        3: {"name": "zh-HK-HiuMaanNeural", "desc": "粤语男声 - 曉文", "language": "粤语", "gender": "男"},
        4: {"name": "en-US-JennyNeural", "desc": "英文女声 - Jenny", "language": "英文", "gender": "女"},
        5: {"name": "en-US-GuyNeural", "desc": "英文男声 - Guy", "language": "英文", "gender": "男"}
    }
    
    config = LiveConfig()
    
    test_message = "这是一个语音测试，用于对比不同音色的效果"
    
    for voice_index, voice_info in voice_map.items():
        print(f"\n[{voice_index}] {voice_info['desc']}")
        print(f"   Edge TTS: {voice_info['name']}")
        print(f"   语言: {voice_info['language']}, 性别: {voice_info['gender']}")
        
        # 临时修改配置
        config.tts_settings.voice = voice_index
        
        # 创建临时TTS处理器
        tts_handler = OptimizedTTSHandler(config)
        tts_handler.start()
        
        try:
            start_time = time.time()
            audio_file = await tts_handler.generate_audio(test_message)
            generation_time = time.time() - start_time
            file_size = audio_file.stat().st_size if audio_file.exists() else 0
            
            print(f"   [成功] 生成完成 - {file_size:,} bytes, {generation_time:.2f}s")
            print(f"   文件: {audio_file}")
            
        except Exception as e:
            print(f"   [失败] 生成错误: {e}")
        
        tts_handler.stop()
        
        # 短暂延迟避免API限制
        await asyncio.sleep(0.5)


def print_voice_info():
    """打印语音信息"""
    print("可用语音选项")
    print("=" * 50)
    
    # 语音选项映射
    voice_map = {
        0: {"name": "zh-CN-XiaoxiaoNeural", "desc": "中文女声 - 晓晓", "language": "中文", "gender": "女"},
        1: {"name": "zh-CN-YunxiNeural", "desc": "中文男声 - 云希", "language": "中文", "gender": "男"},
        2: {"name": "zh-HK-HiuGaaiNeural", "desc": "粤语女声 - 曉儀", "language": "粤语", "gender": "女"},
        3: {"name": "zh-HK-HiuMaanNeural", "desc": "粤语男声 - 曉文", "language": "粤语", "gender": "男"},
        4: {"name": "en-US-JennyNeural", "desc": "英文女声 - Jenny", "language": "英文", "gender": "女"},
        5: {"name": "en-US-GuyNeural", "desc": "英文男声 - Guy", "language": "英文", "gender": "男"}
    }
    
    config = LiveConfig()
    current_voice = config.tts_settings.voice
    
    for voice_index, voice_info in voice_map.items():
        current_marker = "[当前]" if voice_index == current_voice else ""
        print(f"{voice_index}: {voice_info['desc']} - {voice_info['name']} {current_marker}")
        print(f"   语言: {voice_info['language']}, 性别: {voice_info['gender']}")


def print_usage():
    """打印使用说明"""
    print("dyDanmuTTS 音频生成演示工具")
    print("=" * 50)
    print("\n用法:")
    print("  python simple_tts_demo.py [命令]")
    print("\n命令:")
    print("  demo     - 演示当前配置的语音生成")
    print("  compare  - 对比所有语音效果")
    print("  info     - 显示语音选项信息")
    print("  help     - 显示此帮助信息")


async def main():
    """主函数"""
    if len(sys.argv) < 2:
        print_usage()
        return
    
    command = sys.argv[1].lower()
    
    if command == "demo":
        await demo_tts_generation()
    elif command == "compare":
        await demo_voice_comparison()
    elif command == "info":
        print_voice_info()
    elif command == "help":
        print_usage()
    else:
        print(f"未知命令: {command}")
        print_usage()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n用户中断，程序退出")
    except Exception as e:
        logger.error(f"程序异常退出: {e}")
        print(f"程序异常退出: {e}")