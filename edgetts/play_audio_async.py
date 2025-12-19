#!/usr/bin/env python3

"""异步方式在内存中直接播放音频"""

import asyncio
import io
import pygame
import edge_tts
import threading
import sys

TEXT1 = ["君不见，黄河之水天上来，奔流到海不复回。",
"君不见，高堂明镜悲白发，朝如青丝暮成雪。"
"人生得意须尽欢，莫使金樽空对月。",
"天生我材必有用，千金散尽还复来。",
"烹羊宰牛且为乐，会须一饮三百杯。",
"岑夫子，丹丘生，将进酒，杯莫停。",
"与君歌一曲，请君为我倾耳听。",
"钟鼓馔玉不足贵，但愿长醉不复醒。",
"古来圣贤皆寂寞，惟有饮者留其名。",
"陈王昔时宴平乐，斗酒十千恣欢谑",
"岑夫子，丹丘生，将进酒，杯莫停。",
"与君歌一曲，请君为我倾耳听。",
"钟鼓馔玉不足贵，但愿长醉不复醒。",
"古来圣贤皆寂寞，惟有饮者留其名。",
"陈王昔时宴平乐，斗酒十千恣欢谑。"
]
VOICE = "zh-CN-YunjianNeural"

# 全局锁，确保同一时间只有一个音频播放
_audio_lock = threading.Lock()


def _run_async(coro):
    """安全地运行异步函数"""
    try:
        # 尝试获取当前事件循环
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # 如果没有正在运行的事件循环，则创建一个新的
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
    else:
        # 如果已有事件循环，则创建任务
        return loop.create_task(coro)


async def play_audio(audio_bytes):
    """异步播放音频"""
    # 如果锁已被占用，直接返回
    if not _audio_lock.acquire(blocking=False):
        print("警告: 上一个音频仍在播放中，跳过本次播放")
        return
    
    pygame_mixer_initialized = False
    try:
        # 初始化pygame mixer
        pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
        pygame.mixer.init()
        pygame_mixer_initialized = True
        
        # 将音频数据放入内存缓冲区
        audio_buffer = io.BytesIO(bytes(audio_bytes))
        
        # 加载并播放音频
        pygame.mixer.music.load(audio_buffer)
        pygame.mixer.music.play()
        
        # 等待播放完成
        while pygame.mixer.music.get_busy():
            await asyncio.sleep(0.1)
    except pygame.error as e:
        print(f"播放音频时出错: {e}")
    except Exception as e:
        print(f"播放音频时出现未知错误: {e}")
    finally:
        # 确保总是清理资源
        try:
            if pygame_mixer_initialized:
                pygame.mixer.music.unload()
                pygame.mixer.quit()
        except:
            pass
        finally:
            _audio_lock.release()


async def main(TEXT) -> None:
    """Main function"""
    try:
        communicate = edge_tts.Communicate(TEXT, VOICE, boundary="SentenceBoundary")
        audio_bytes = bytearray()
        
        print("正在生成音频...")
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_bytes.extend(chunk["data"])
        
        if audio_bytes:
            print("正在播放音频...")
            await play_audio(audio_bytes)
            print("播放完成!")
        else:
            print("未生成音频数据!")
    except Exception as e:
        print(f"生成或播放音频时出错: {e}")


def play_text(text):
    """播放文本"""
    try:
        _run_async(main(text))
    except Exception as e:
        print(f"TTS播放文本时出错: {e}")


if __name__ == "__main__":
    for text in TEXT1:
        try:
            _run_async(main(text))
        except KeyboardInterrupt:
            print("\n用户中断播放")
            break
        except Exception as e:
            print(f"播放出错: {e}")