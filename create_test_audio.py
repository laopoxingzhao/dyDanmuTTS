#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
创建测试音频文件
"""

import asyncio
import edge_tts
import sys
import os

async def create_test_audio():
    """创建测试音频文件"""
    try:
        print("正在创建测试音频文件...")
        communicate = edge_tts.Communicate('这是一个测试音频文件，用于验证Qt音频播放器功能', voice='zh-CN-XiaoxiaoNeural')
        await communicate.save('output/test.mp3')
        print('测试音频文件已创建: output/test.mp3')
        
        # 验证文件是否存在
        if os.path.exists('output/test.mp3'):
            file_size = os.path.getsize('output/test.mp3')
            print(f'文件大小: {file_size} 字节')
            return True
        else:
            print('文件创建失败')
            return False
            
    except Exception as e:
        print(f'创建测试音频文件失败: {e}')
        return False

if __name__ == '__main__':
    success = asyncio.run(create_test_audio())
    sys.exit(0 if success else 1)