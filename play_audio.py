import pygame
import time
import os

def play_audio(file_path):
    """
    播放音频文件
    :param file_path: 音频文件路径
    """
    # 初始化pygame mixer
    pygame.mixer.init()
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"错误：找不到文件 {file_path}")
        return
    
    # 加载并播放音频文件
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    
    # 等待音频播放完成
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)
    
    print(f"播放完成: {file_path}")

def play_audio_file():
    # 使用tts.py生成的test.mp3文件
    audio_file = "test.mp3"
    
    # 检查是否存在音频文件
    if os.path.exists(audio_file):
        print(f"正在播放: {audio_file}")
        play_audio(audio_file)
    else:
        print(f"未找到音频文件: {audio_file}")
        print("请先运行 tts.py 生成音频文件")

# if __name__ == "__main__":
#     main()