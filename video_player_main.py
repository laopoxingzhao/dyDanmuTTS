#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
视频播放器主程序
用于播放video目录下的视频文件
"""

from videoplayer.player import VideoPlayer


def main():
    print("抖音直播视频播放器")
    print("=" * 30)
    
    # 创建视频播放器实例
    player = VideoPlayer()
    
    # 获取视频文件列表
    video_files = player.get_video_files()
    
    if not video_files:
        print("在video目录中未找到视频文件")
        print("请将视频文件放入video目录后再运行此程序")
        return
    
    print(f"发现 {len(video_files)} 个视频文件:")
    for i, video_file in enumerate(video_files, 1):
        print(f"{i}. {video_file}")
    
    # 自动开始循环播放所有视频
    print("\n开始循环播放所有视频，按 'q' 键退出...")
    player.play_all_videos_loop()


if __name__ == "__main__":
    main()