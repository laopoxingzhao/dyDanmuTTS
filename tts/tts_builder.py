import asyncio
import edge_tts

async def tts_generation(text, voice="zh-CN-XiaoxiaoNeural", rate="+0%", volume="+0%"):
    """
    使用Edge TTS生成语音
    
    参数:
    text: 要转换的文本
    voice: 语音类型 (例如: zh-CN-XiaoxiaoNeural, zh-CN-YunyangNeural)
    rate: 语速 (+0%, -10%, +20%等)
    volume: 音量 (+0%, -10%, +20%等)
    """
    # 创建TTS实例
    communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
    
    # 生成音频文件
    await communicate.save("output/output.mp3")

async def list_voices():
    """列出所有可用的中文语音"""
    voices = await edge_tts.list_voices()
    chinese_voices = [voice for voice in voices if voice["Locale"].startswith("zh")]
    for voice in chinese_voices:
        print(f"{voice['ShortName']}: {voice['FriendlyName']}")
    # print(chinese_voices)


# asyncio.run(tts_generation("你好，欢迎使用抖音直播弹幕抓取工具"))

asyncio.run(list_voices())