#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接使用TTS生成函数的演示脚本
"""

import sys
import time
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.config import LiveConfig
from tts.tts_builder import tts_generation
from config.log import g_logger as logger


def get_voice_parameters(config):
    """根据配置获取语音参数"""
    # 语音选项映射
    voice_map = {
        0: "zh-CN-XiaoxiaoNeural",  # 中文女声 - 晓晓
        1: "zh-CN-YunxiNeural",    # 中文男声 - 云希
        2: "zh-HK-HiuGaaiNeural",  # 粤语女声 - 曉儀
        3: "zh-HK-HiuMaanNeural",  # 粤语男声 - 曉文
        4: "en-US-JennyNeural",    # 英文女声 - Jenny
        5: "en-US-GuyNeural"       # 英文男声 - Guy
    }
    
    # 获取语音名称
    voice_index = config.tts_settings.voice
    voice_name = voice_map.get(voice_index, "zh-CN-XiaoxiaoNeural")
    
    # 计算音量参数 (配置是0-100，转换为+/-百分比)
    volume = config.tts_settings.volume
    if volume == 50:
        volume_param = "+0%"
    elif volume < 50:
        volume_param = f"{volume - 50}%"
    else:
        volume_param = f"+{volume - 50}%"
    
    # 计算语速参数 (配置是0-20，10为正常速度)
    speed = config.tts_settings.speed
    if speed == 10:
        rate_param = "+0%"
    elif speed < 10:
        rate_param = f"{(speed - 10) * 10}%"
    else:
        rate_param = f"+{(speed - 10) * 10}%"
    
    return voice_name, rate_param, volume_param


async def demo_tts_generation():
    """演示TTS音频生成功能"""
    print("dyDanmuTTS 直接TTS生成演示")
    print("=" * 50)
    
    try:
        # 初始化配置
        config = LiveConfig()
        
        print(f"\n当前配置:")
        print(f"   语音索引: {config.tts_settings.voice}")
        print(f"   音量设置: {config.tts_settings.volume}")
        print(f"   语速设置: {config.tts_settings.speed}")
        
        # 获取语音参数
        voice_name, rate_param, volume_param = get_voice_parameters(config)
        
        # 语音选项描述
        voice_desc_map = {
            0: "中文女声 - 晓晓",
            1: "中文男声 - 云希",
            2: "粤语女声 - 曉儀",
            3: "粤语男声 - 曉文",
            4: "英文女声 - Jenny",
            5: "英文男声 - Guy"
        }
        
        current_desc = voice_desc_map.get(config.tts_settings.voice, "未知语音")
        print(f"   当前语音: {current_desc}")
        print(f"   Edge TTS: {voice_name}")
        print(f"   语速参数: {rate_param}")
        print(f"   音量参数: {volume_param}")
        
        # 确保输出目录存在
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # 测试消息
        test_messages = [
            "欢迎使用dyDanmuTTS语音合成系统",
            "当前正在使用配置文件中设置的语音",
            "系统会根据您的配置自动生成对应语言和音色的音频"
        ]
        
        print(f"\n开始生成 {len(test_messages)} 条音频...")
        print("-" * 50)
        
        generated_files = []
        total_start_time = time.time()
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n[{i}/{len(test_messages)}] 生成音频: {message[:20]}...")
            
            start_time = time.time()
            
            try:
                # 生成唯一的输出文件名
                timestamp = int(time.time() * 1000)
                output_file = output_dir / f"tts_demo_{timestamp}_{i}.mp3"
                
                # 临时修改tts_builder中的输出路径
                original_save = None
                
                # 创建一个临时的communicate并保存到指定文件
                import edge_tts
                communicate = edge_tts.Communicate(message, voice_name, rate=rate_param, volume=volume_param)
                await communicate.save(str(output_file))
                
                generation_time = time.time() - start_time
                file_size = output_file.stat().st_size if output_file.exists() else 0
                
                print(f"   [成功] 生成完成")
                print(f"   文件路径: {output_file}")
                print(f"   文件大小: {file_size:,} bytes")
                print(f"   生成时间: {generation_time:.2f}s")
                
                generated_files.append(output_file)
                
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
        print(f"   - 生成的音频文件保存在 output/ 目录")
        print(f"   - 可以使用任何音频播放器播放这些文件")
        print(f"   - 配置文件位置: config/app_config.json")
        print(f"   - 修改配置后重新运行此脚本测试不同语音")
        
        return len(generated_files) > 0
        
    except Exception as e:
        logger.error(f"演示过程中发生错误: {e}")
        print(f"错误: {e}")
        return False


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
    
    # 确保输出目录存在
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    test_message = "这是一个语音测试，用于对比不同音色的效果"
    
    for voice_index, voice_info in voice_map.items():
        print(f"\n[{voice_index}] {voice_info['desc']}")
        print(f"   Edge TTS: {voice_info['name']}")
        print(f"   语言: {voice_info['language']}, 性别: {voice_info['gender']}")
        
        try:
            start_time = time.time()
            
            # 生成唯一的输出文件名
            timestamp = int(time.time() * 1000)
            output_file = output_dir / f"voice_compare_{voice_index}_{timestamp}.mp3"
            
            # 使用默认参数生成音频
            import edge_tts
            communicate = edge_tts.Communicate(test_message, voice_info['name'], rate="+0%", volume="+0%")
            await communicate.save(str(output_file))
            
            generation_time = time.time() - start_time
            file_size = output_file.stat().st_size if output_file.exists() else 0
            
            print(f"   [成功] 生成完成 - {file_size:,} bytes, {generation_time:.2f}s")
            print(f"   文件: {output_file}")
            
        except Exception as e:
            print(f"   [失败] 生成错误: {e}")
        
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
    print("dyDanmuTTS 直接TTS生成演示工具")
    print("=" * 50)
    print("\n用法:")
    print("  python direct_tts_demo.py [命令]")
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
        success = await demo_tts_generation()
        if success:
            print(f"\n[SUCCESS] TTS演示成功完成")
        else:
            print(f"\n[FAILED] TTS演示失败")
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