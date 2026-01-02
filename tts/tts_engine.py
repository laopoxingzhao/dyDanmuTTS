"""
TTS引擎模块 - 使用edge-tts生成语音
"""
import asyncio
import edge_tts
import os
from typing import Optional
from config.log import g_logger


class TTSEngine:
    """TTS引擎封装类"""
    
    # 可用语音列表
    AVAILABLE_VOICES = {
        '晓晓': 'zh-CN-XiaoxiaoNeural',
        '云希': 'zh-CN-YunxiNeural',
        '晓语': 'zh-CN-XiaoyiNeural',
        '云健': 'zh-CN-YunjianNeural',
        '晓墨': 'zh-CN-XiaomengNeural',
        '云阳': 'zh-CN-YunyangNeural',
        '晓颜': 'zh-CN-XiaoyanNeural',
        '晓悠': 'zh-CN-XiaoyouNeural',
        '晓梦': 'zh-CN-XiaomengNeural',
        '晓萱': 'zh-CN-XiaoxuanNeural',
        '晓涵': 'zh-CN-XiaohanNeural',
        '晓甄': 'zh-CN-XiaozhenNeural',
    }
    
    def __init__(self, voice: str = '晓晓', rate: str = '+0%', volume: str = '+0%'):
        """
        初始化TTS引擎
        
        Args:
            voice: 语音名称（如'晓晓'）
            rate: 语速（如'+20%', '-10%'）
            volume: 音量（如'+50%', '-20%'）
        """
        self.voice_name = voice
        self.voice_id = self.AVAILABLE_VOICES.get(voice, 'zh-CN-XiaoxiaoNeural')
        self.rate = rate
        self.volume = volume
        
        g_logger.info(f"TTS引擎初始化 - 语音: {voice}({self.voice_id}), 语速: {rate}, 音量: {volume}")
    
    def set_voice(self, voice: str):
        """设置语音"""
        self.voice_name = voice
        self.voice_id = self.AVAILABLE_VOICES.get(voice, 'zh-CN-XiaoxiaoNeural')
        g_logger.info(f"TTS语音已更新: {voice}({self.voice_id})")
    
    def set_rate(self, rate: str):
        """设置语速"""
        self.rate = rate
        g_logger.info(f"TTS语速已更新: {rate}")
    
    def set_volume(self, volume: str):
        """设置音量"""
        self.volume = volume
        g_logger.info(f"TTS音量已更新: {volume}")
    
    async def text_to_speech_async(self, text: str, output_file: str) -> bool:
        """
        异步将文本转换为语音
        
        Args:
            text: 要转换的文本
            output_file: 输出音频文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            # 创建Communicate对象
            communicate = edge_tts.Communicate(
                text=text,
                voice=self.voice_id,
                rate=self.rate,
                volume=self.volume
            )
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # 生成语音文件
            await communicate.save(output_file)
            
            g_logger.debug(f"TTS生成成功: {text[:30]}... -> {output_file}")
            return True
            
        except Exception as e:
            g_logger.error(f"TTS生成失败: {text[:30]}... 错误: {e}")
            return False
    
    def text_to_speech(self, text: str, output_file: str) -> bool:
        """
        同步将文本转换为语音（封装异步方法）
        
        Args:
            text: 要转换的文本
            output_file: 输出音频文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            # 在新的事件循环中运行异步任务
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.text_to_speech_async(text, output_file))
            loop.close()
            return result
        except Exception as e:
            g_logger.error(f"TTS同步调用失败: {e}")
            return False
    
    @classmethod
    def get_available_voices(cls) -> dict:
        """获取可用语音列表"""
        return cls.AVAILABLE_VOICES.copy()
    
    @classmethod
    def get_voice_id(cls, voice_name: str) -> str:
        """根据语音名称获取语音ID"""
        return cls.AVAILABLE_VOICES.get(voice_name, 'zh-CN-XiaoxiaoNeural')