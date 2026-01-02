"""
新TTS系统测试脚本
测试TTS引擎、音频播放器、关键词匹配等核心功能
"""
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from tts.tts_engine import TTSEngine
from tts.audio_player import AudioPlayer
from tts.keyword_matcher import KeywordMatcher, KeywordRule
from tts.message_queue import MessageQueue, TTSMessage, MessageType
from tts.cache_manager import CacheManager
from tts.tts_controller import TTSController
from config.config import config_manager


def test_tts_engine():
    """测试TTS引擎"""
    print("=" * 50)
    print("测试TTS引擎")
    print("=" * 50)
    
    engine = TTSEngine()
    
    # 测试语音列表
    print(f"可用语音: {list(engine.AVAILABLE_VOICES.keys())}")
    
    # 测试文本转语音
    test_text = "你好，这是一条测试语音。"
    output_file = "test_output.mp3"
    
    print(f"正在生成语音: {test_text}")
    success = engine.text_to_speech(test_text, output_file)
    
    if success:
        print(f"✓ 语音生成成功: {output_file}")
        # 检查文件是否存在
        if Path(output_file).exists():
            print(f"✓ 文件大小: {Path(output_file).stat().st_size / 1024:.2f} KB")
        else:
            print("✗ 文件不存在")
    else:
        print("✗ 语音生成失败")
    
    # 清理测试文件
    if Path(output_file).exists():
        Path(output_file).unlink()
        print("✓ 测试文件已清理")
    
    print()


def test_audio_player():
    """测试音频播放器"""
    print("=" * 50)
    print("测试音频播放器")
    print("=" * 50)
    
    # 先生成测试音频
    engine = TTSEngine()
    test_file = "test_audio.mp3"
    engine.text_to_speech("这是音频播放器测试", test_file)
    
    if not Path(test_file).exists():
        print("✗ 测试音频生成失败")
        return
    
    player = AudioPlayer()
    
    print("播放测试音频...")
    success = player.play(test_file, wait=True)
    
    if success:
        print("✓ 音频播放成功")
    else:
        print("✗ 音频播放失败")
    
    # 清理测试文件
    if Path(test_file).exists():
        Path(test_file).unlink()
        print("✓ 测试文件已清理")
    
    print()


def test_keyword_matcher():
    """测试关键词匹配器"""
    print("=" * 50)
    print("测试关键词匹配器")
    print("=" * 50)
    
    matcher = KeywordMatcher()
    
    # 添加测试规则
    rules = [
        KeywordRule(
            keyword="欢迎",
            match_type="contain",
            replies=["欢迎 {user_name} 进入直播间"],
            priority=2,
            cooldown=10,
            reply_probability=1.0
        ),
        KeywordRule(
            keyword="^谢谢",
            match_type="regex",
            replies=["谢谢 {user_name} 的支持"],
            priority=1,
            cooldown=5,
            reply_probability=0.8
        ),
        KeywordRule(
            keyword="测试",
            match_type="exact",
            replies=["收到测试消息"],
            priority=1,
            cooldown=10,
            reply_probability=1.0
        )
    ]
    
    for rule in rules:
        matcher.add_rule(rule)
        print(f"✓ 添加规则: {rule.keyword} ({rule.match_type})")
    
    print()
    print("测试匹配:")
    
    # 测试用例
    test_cases = [
        {"user_name": "张三", "content": "欢迎来到直播间"},
        {"user_name": "李四", "content": "谢谢主播"},
        {"user_name": "王五", "content": "测试消息"},
        {"user_name": "赵六", "content": "这是一条普通消息"},
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        result = matcher.match(test_case["content"], test_case["user_name"])
        if result:
            print(f"  测试 {i}: '{test_case['content']}' -> 匹配成功: {result}")
        else:
            print(f"  测试 {i}: '{test_case['content']}' -> 无匹配")
    
    # 测试冷却时间
    print("\n测试冷却时间:")
    user_name = "张三"
    content = "欢迎"
    result1 = matcher.match(content, user_name)
    print(f"  第一次匹配: {result1}")
    result2 = matcher.match(content, user_name)
    print(f"  第二次匹配（冷却中）: {result2}")
    
    print()


def test_message_queue():
    """测试消息队列"""
    print("=" * 50)
    print("测试消息队列")
    print("=" * 50)
    
    queue = MessageQueue(max_size=10)
    
    # 添加不同优先级的消息
    messages = [
        TTSMessage(
            priority=1,
            message_type=MessageType.KEYWORD,
            text="低优先级消息",
            variables={}
        ),
        TTSMessage(
            priority=3,
            message_type=MessageType.GIFT,
            text="高优先级消息",
            variables={}
        ),
        TTSMessage(
            priority=2,
            message_type=MessageType.CHAT,
            text="中优先级消息",
            variables={}
        ),
    ]
    
    for msg in messages:
        queue.put(msg)
        print(f"✓ 添加消息: {msg.text} (优先级: {msg.priority})")
    
    print(f"\n队列大小: {queue.size()}")
    print(f"队列是否已满: {queue.is_full()}")
    
    print("\n取出消息（应按优先级排序）:")
    while not queue.is_empty():
        msg = queue.get()
        print(f"  {msg.text} (优先级: {msg.priority})")
    
    print()


def test_cache_manager():
    """测试缓存管理器"""
    print("=" * 50)
    print("测试缓存管理器")
    print("=" * 50)
    
    cache_dir = "test_cache"
    cache_mgr = CacheManager(cache_dir=cache_dir)
    
    test_text = "这是缓存测试文本"
    voice = "晓晓"
    
    # 测试缓存查找
    cached_file = cache_mgr.get_cached_file(test_text, voice)
    if cached_file:
        print(f"找到缓存: {cached_file}")
    else:
        print("未找到缓存")
    
    # 生成测试音频
    engine = TTSEngine()
    test_file = "test_cache_audio.mp3"
    engine.text_to_speech(test_text, test_file)
    
    # 保存到缓存
    success = cache_mgr.save_to_cache(test_text, voice, test_file)
    if success:
        print(f"✓ 保存到缓存成功")
    
    # 再次查找缓存
    cached_file = cache_mgr.get_cached_file(test_text, voice)
    if cached_file:
        print(f"✓ 从缓存找到: {cached_file}")
    else:
        print("✗ 从缓存未找到")
    
    # 获取缓存统计
    stats = cache_mgr.get_stats()
    print(f"\n缓存统计:")
    print(f"  缓存文件数: {stats['file_count']}")
    print(f"  缓存大小: {stats['total_size_mb']:.2f} MB")
    
    # 清理缓存
    cache_mgr.clear_cache()
    print(f"✓ 缓存已清理")
    
    # 清理测试文件
    if Path(test_file).exists():
        Path(test_file).unlink()
    if Path(cache_dir).exists():
        import shutil
        shutil.rmtree(cache_dir)
        print("✓ 测试目录已清理")
    
    print()


def test_tts_controller():
    """测试TTS控制器"""
    print("=" * 50)
    print("测试TTS控制器")
    print("=" * 50)
    
    # 确保配置已加载
    config_manager.load()
    
    controller = TTSController(config_manager)
    
    print("启动TTS控制器...")
    controller.start()
    
    # 添加测试弹幕
    test_danmus = [
        {
            "user_name": "张三",
            "content": "欢迎",
            "method": "WebcastChatMessage"
        },
        {
            "user_name": "李四",
            "content": "谢谢主播",
            "method": "WebcastChatMessage"
        }
    ]
    
    for danmu in test_danmus:
        controller.add_danmu(danmu, danmu["method"])
        print(f"✓ 添加弹幕: {danmu['user_name']}: {danmu['content']}")
    
    # 等待处理
    print("\n等待处理...")
    import time
    time.sleep(3)
    
    # 获取统计
    stats = controller.get_stats()
    print(f"\nTTS统计:")
    print(f"  已生成: {stats['total_generated']}")
    print(f"  已播放: {stats['total_played']}")
    print(f"  队列长度: {stats['queue_size']}")
    print(f"  缓存命中: {stats['cache_hits']}")
    
    # 停止控制器
    print("\n停止TTS控制器...")
    controller.stop()
    print("✓ 控制器已停止")
    
    print()


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 50)
    print("开始TTS系统测试")
    print("=" * 50 + "\n")
    
    try:
        test_tts_engine()
        test_audio_player()
        test_keyword_matcher()
        test_message_queue()
        test_cache_manager()
        test_tts_controller()
        
        print("=" * 50)
        print("✓ 所有测试完成")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n✗ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()