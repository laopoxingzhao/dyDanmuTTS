import asyncio
import threading
import time
from queue import Empty
from .tts_builder import tts_generation
from ..tool.myqueue import ttsq
from ..config.config_manager import ConfigManager

class TtsHandler:
    """
    TTS处理器，用于处理TTS队列中的消息并播放
    """
    
    def __init__(self, config_manager: ConfigManager = None):
        self.config_manager = config_manager or ConfigManager()
        self.is_running = False
        self.tts_thread = None
        self._lock = threading.Lock()
        
        # 从配置加载TTS参数
        self.volume = f"+{self.config_manager.get_config('tts_settings', 'volume', 70) - 50}%"  # 转换为edge-tts格式
        self.voice = self._get_voice_name(self.config_manager.get_config('tts_settings', 'voice', 0))
        speed_value = self.config_manager.get_config('tts_settings', 'speed', 10)
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
        with self._lock:
            self.volume = f"+{self.config_manager.get_config('tts_settings', 'volume', 70) - 50}%"  # 转换为edge-tts格式
            self.voice = self._get_voice_name(self.config_manager.get_config('tts_settings', 'voice', 0))
            speed_value = self.config_manager.get_config('tts_settings', 'speed', 10)
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
        while self.is_running:
            try:
                # 尝试从队列获取消息，超时1秒
                item = ttsq.get()
                if item:
                    # 播放TTS
                    self._play_tts(item['content'])
                else:
                    # 如果队列为空，等待一下避免CPU占用过高
                    time.sleep(0.1)
            except Empty:
                # 队列为空，等待一下
                time.sleep(0.1)
            except Exception as e:
                print(f"TTS处理出错: {e}")
                time.sleep(0.1)
    
    def _play_tts(self, text):
        """播放TTS文本"""
        try:
            # 创建临时事件循环来运行async函数
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    tts_generation(text, self.voice, self.rate, self.volume)
                )
            finally:
                loop.close()
        except Exception as e:
            print(f"TTS播放失败: {e}")


# 全局TTS处理器实例
tts_handler = None

def init_tts_handler(config_manager=None):
    """初始化TTS处理器"""
    global tts_handler
    if tts_handler is None:
        tts_handler = TtsHandler(config_manager)
    return tts_handler
