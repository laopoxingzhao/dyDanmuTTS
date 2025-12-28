#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.danmu_controller import DanmuController

def test_tts_methods():
    """测试TTS相关方法是否存在"""
    controller = DanmuController()
    
    # 检查方法是否存在
    methods_to_check = [
        '_should_add_to_tts_queue',
        '_add_to_tts_queue',
        '_generate_tts_text'
    ]
    
    for method_name in methods_to_check:
        if hasattr(controller, method_name):
            print(f"[OK] 方法 {method_name} 存在")
        else:
            print(f"[ERROR] 方法 {method_name} 不存在")
            
    # 测试 _should_add_to_tts_queue 方法
    if hasattr(controller, '_should_add_to_tts_queue'):
        try:
            # 模拟参数调用
            result = controller._should_add_to_tts_queue('WebcastChatMessage', None)
            print(f"[OK] _should_add_to_tts_queue 方法可调用，返回值: {result}")
        except Exception as e:
            print(f"[ERROR] _should_add_to_tts_queue 方法调用失败: {e}")

if __name__ == "__main__":
    test_tts_methods()