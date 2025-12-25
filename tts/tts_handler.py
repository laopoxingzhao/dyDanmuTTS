import asyncio
import threading
import edge_tts
from config.config_manager import global_config_manager
from config.log import g_logger
import re
import time
from collections import deque
from queue import Empty


class TTSHandler:
    def __init__(self, config_manager=None):
        # 使用全局配置管理器，如果传入了则使用传入的
        self.config_manager = config_manager or global_config_manager
        # 获取配置实体
        app_config = self.config_manager.get_app_config()
        
        # 用于存储已处理消息的信息，防止重复播报
        self.message_history = {}
        # TTS队列配置
        tts_settings = app_config.tts_settings
        self.queue_settings = getattr(tts_settings, 'tts_queue_settings', {
            "dedup_time_window": 30,  # 去重时间窗口（秒）
            "min_interval": 5,        # 同类型消息最小间隔（秒）
            "max_queue_size": 20      # 队列最大长度
        })
        self.is_running = False
        self.tts_thread = None
        self._lock = threading.Lock()
        
        # 从配置加载TTS参数
        self.volume = f"+{tts_settings.volume - 50}%"  # 转换为edge-tts格式
        self.voice = self._get_voice_name(tts_settings.voice)
        speed_value = tts_settings.speed
        self.rate = f"+{(speed_value - 10) * 10}%"  # 转换为edge-tts格式
        
    def _get_voice_name(self, voice_index):
        """根据索引获取语音名称"""
        voice_map = {
            0: "zh-CN-XiaoxiaoNeural",  # 普通话-女声
            1: "zh-CN-YunxiNeural",    # 普通话-男声
            2: "zh-HK-HiuGaaiNeural",  # 粤语-女声
            3: "zh-HK-HiuMaanNeural",  # 粤语-女声（可能需要调整）
            4: "en-US-JennyNeural",    # 英语-女声
            5: "en-US-GuyNeural"       # 英语-男声
        }
        return voice_map.get(voice_index, "zh-CN-XiaoxiaoNeural")
    
    def update_config(self):
        """更新配置参数"""
        app_config = self.config_manager.get_app_config()
        tts_settings = app_config.tts_settings
        
        with self._lock:
            self.volume = f"+{tts_settings.volume - 50}%"  # 转换为edge-tts格式
            self.voice = self._get_voice_name(tts_settings.voice)
            speed_value = tts_settings.speed
            self.rate = f"+{(speed_value - 10) * 10}%"  # 转换为edge-tts格式
    
    def start(self):
        """启动TTS处理器"""
        if self.is_running:
            return
            
        self.is_running = True
        self.tts_thread = threading.Thread(target=self._process_tts_queue, daemon=True)
        self.tts_thread.start()
    
    def stop(self):
        """停止TTS处理器"""
        self.is_running = False
        if self.tts_thread:
            self.tts_thread.join(timeout=2)  # 等待最多2秒
    
    def _process_tts_queue(self):
        """处理TTS队列的后台线程"""
        # TODO: 这里需要从实际的模块中导入TTS队列
        # 例如: from some_module import tts_queue
        # 由于原代码中ttsq未定义，这里暂时使用一个临时队列作为占位
        # 实际使用时需要替换为正确的队列实例
        pass
                time.sleep(0.1)
    
    def _play_tts(self, text):
        """播放TTS文本"""
        try:
            # 创建临时事件循环来运行async函数
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    self._tts_generation(text, self.voice, self.rate, self.volume)
                )
            finally:
                loop.close()
        except Exception as e:
            print(f"TTS播放失败: {e}")
    
    async def _tts_generation(self, text, voice, rate, volume):
        """生成TTS音频"""
        communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
        await communicate.save("temp_tts.mp3")


# 全局TTS处理器实例
tts_handler = None

def init_tts_handler(config_manager=None):
    """初始化TTS处理器"""
    global tts_handler
    if tts_handler is None:
        tts_handler = TTSHandler(config_manager)
    return tts_handler