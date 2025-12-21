#!/usr/bin/env python3

"""TTS 播放管理：在后台线程统一管理 pygame mixer，主线程不阻塞。"""

import asyncio
import tempfile
import os
import pygame
import edge_tts
import threading
import logging
import queue

logger = logging.getLogger(__name__)

VOICE = "zh-CN-YunjianNeural"


class AudioPlayer(threading.Thread):
    """后台音频播放线程，负责初始化和关闭 pygame，并顺序播放音频任务。"""

    def __init__(self):
        super().__init__(daemon=True)
        self._queue = queue.Queue()
        self._stop_event = threading.Event()
        self._ready = threading.Event()

    def run(self):
        try:
            pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
            pygame.mixer.init()
            logger.info("AudioPlayer: pygame mixer 初始化完成")
            self._ready.set()
        except Exception:
            logger.exception("AudioPlayer: 初始化 pygame 失败")
            return

        while not self._stop_event.is_set():
            try:
                item = self._queue.get(timeout=0.5)
            except queue.Empty:
                continue

            if item is None:
                break

            try:
                # 控制命令类型为 dict，例如 {'cmd': 'pause'} 或 {'cmd': 'set_volume', 'value': 0.5}
                if isinstance(item, dict):
                    cmd = item.get('cmd')
                    try:
                        if cmd == 'pause':
                            pygame.mixer.music.pause()
                        elif cmd == 'resume':
                            pygame.mixer.music.unpause()
                        elif cmd == 'stop':
                            pygame.mixer.music.stop()
                        elif cmd == 'set_volume':
                            v = float(item.get('value', 1.0))
                            pygame.mixer.music.set_volume(max(0.0, min(1.0, v)))
                    except Exception:
                        logger.exception("AudioPlayer 执行控制命令失败: %s", cmd)
                    continue

                if isinstance(item, bytes):
                    tmp_file = None
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tf:
                            tf.write(item)
                            tmp_file = tf.name

                        pygame.mixer.music.load(tmp_file)
                        pygame.mixer.music.play()
                        while pygame.mixer.music.get_busy() and not self._stop_event.is_set():
                            pygame.time.wait(100)
                    finally:
                        try:
                            if tmp_file and os.path.exists(tmp_file):
                                os.remove(tmp_file)
                        except Exception:
                            logger.debug("删除临时音频文件失败")
                elif isinstance(item, str):
                    if os.path.exists(item):
                        pygame.mixer.music.load(item)
                        pygame.mixer.music.play()
                        while pygame.mixer.music.get_busy() and not self._stop_event.is_set():
                            pygame.time.wait(100)
                    else:
                        logger.warning("AudioPlayer: 文件不存在 %s", item)
            except Exception:
                logger.exception("AudioPlayer 播放出错")

        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        try:
            pygame.mixer.quit()
        except Exception:
            pass

    def play_bytes(self, audio_bytes: bytes):
        self._queue.put(audio_bytes)

    def play_file(self, path: str):
        self._queue.put(path)

    def stop(self):
        self._stop_event.set()
        # 唤醒线程以便退出
        self._queue.put(None)

    def pause(self):
        self._queue.put({'cmd': 'pause'})

    def resume(self):
        self._queue.put({'cmd': 'resume'})

    def stop_playback(self):
        self._queue.put({'cmd': 'stop'})

    def set_volume(self, value: float):
        self._queue.put({'cmd': 'set_volume', 'value': float(value)})


# 全局单例播放器
_AUDIO_PLAYER = AudioPlayer()
_AUDIO_PLAYER.start()


async def _generate_audio_bytes(text: str, voice: str = None, rate: float = 1.0, ssml_volume: float = None) -> bytes:
    """使用 edge-tts 生成音频并返回 bytes。

    参数:
      text: 要合成的文本或 ssml
      voice: edge-tts voice 字符串，None 则使用默认 VOICE
      rate: 语速倍率，1.0 表示正常，0.8 表示慢 80%
      ssml_volume: 可选的 ssml volume（0.0-1.0）
    """
    try:
        v = voice or VOICE

        # 如果需要调整 rate 或 ssml_volume，则用 SSML 包裹文本
        ssml_text = None
        try:
            rate_val = float(rate) if rate is not None else 1.0
        except Exception:
            rate_val = 1.0

        if rate_val != 1.0 or ssml_volume is not None:
            # prosody rate 接受百分比，如 "80%" 表示原速度的80%
            rate_pct = f"{int(rate_val * 100)}%"
            if ssml_volume is not None:
                try:
                    vol_pct = f"{int(float(ssml_volume) * 100)}%"
                except Exception:
                    vol_pct = None
            else:
                vol_pct = None

            if vol_pct:
                ssml_text = f"<speak><prosody rate=\"{rate_pct}\" volume=\"{vol_pct}\">{text}</prosody></speak>"
            else:
                ssml_text = f"<speak><prosody rate=\"{rate_pct}\">{text}</prosody></speak>"

        input_text = ssml_text if ssml_text is not None else text

        communicate = edge_tts.Communicate(input_text, v, boundary="SentenceBoundary")
        audio_bytes = bytearray()
        async for chunk in communicate.stream():
            if chunk.get("type") == "audio":
                audio_bytes.extend(chunk.get("data", b""))
        return bytes(audio_bytes)
    except Exception:
        logger.exception("生成TTS音频失败")
        return b""


def _generate_and_enqueue(text: str, voice: str = None, rate: float = 1.0, ssml_volume: float = None):
    """在线程中运行 asyncio 任务，生成音频后推入播放队列。"""
    try:
        audio = asyncio.run(_generate_audio_bytes(text, voice=voice, rate=rate, ssml_volume=ssml_volume))
        if audio:
            _AUDIO_PLAYER.play_bytes(audio)
        else:
            logger.warning("未生成音频数据: %s", text)
    except Exception:
        logger.exception("生成或入队音频时出错")


def play_text(text: str, voice: str = None, rate: float = 1.0, ssml_volume: float = None):
    """非阻塞接口：在后台线程生成并播放 TTS。

    参数:
      voice: edge-tts voice 名称
      rate: 语速倍率（float），1.0 为正常
      ssml_volume: 可选 SSML 音量（0.0-1.0），通常使用播放端 volume 控制
    """
    try:
        threading.Thread(target=_generate_and_enqueue, args=(text, voice, rate, ssml_volume), daemon=True).start()
    except Exception:
        logger.exception("启动 TTS 线程失败")


def stop_audio_player():
    try:
        _AUDIO_PLAYER.stop()
    except Exception:
        logger.exception("停止 AudioPlayer 失败")


def pause_audio():
    try:
        _AUDIO_PLAYER.pause()
    except Exception:
        logger.exception("暂停播放失败")


def resume_audio():
    try:
        _AUDIO_PLAYER.resume()
    except Exception:
        logger.exception("恢复播放失败")


def stop_playback():
    try:
        _AUDIO_PLAYER.stop_playback()
    except Exception:
        logger.exception("停止播放失败")


def set_volume(value: float):
    try:
        _AUDIO_PLAYER.set_volume(value)
    except Exception:
        logger.exception("设置音量失败")


def get_audio_player():
    return _AUDIO_PLAYER


# 兼容导出：提供无下划线的顶层变量引用
AUDIO_PLAYER = _AUDIO_PLAYER


# 静音支持：保存上一次音量以便恢复
_PREVIOUS_VOLUME = 1.0


def mute_audio():
    global _PREVIOUS_VOLUME
    try:
        # 尝试读取当前音量（若 mixer 可用）
        try:
            current = pygame.mixer.music.get_volume()
            _PREVIOUS_VOLUME = float(current)
        except Exception:
            _PREVIOUS_VOLUME = 1.0
        set_volume(0.0)
    except Exception:
        logger.exception("mute_audio 失败")


def unmute_audio():
    try:
        set_volume(_PREVIOUS_VOLUME)
    except Exception:
        logger.exception("unmute_audio 失败")


def list_available_voices() -> list:
    """尝试列出 edge-tts 可用的 voices。

    此函数尝试多种可能的导出名以兼容不同版本的 edge-tts；若无法获取则返回一个合理的默认示例列表。
    """
    try:
        # 常见直接导出函数或属性
        if hasattr(edge_tts, 'list_voices'):
            try:
                # 检查是否是协程函数
                import inspect
                if inspect.iscoroutinefunction(edge_tts.list_voices):
                    return asyncio.run(edge_tts.list_voices())
                else:
                    return edge_tts.list_voices()
            except Exception:
                # 可能是异步函数
                try:
                    return asyncio.run(edge_tts.list_voices())
                except Exception:
                    pass

        # 有些版本可能把 voices 放在 edge_tts.VoicesManager().get_voices()
        if hasattr(edge_tts, 'VoicesManager'):
            try:
                vm = edge_tts.VoicesManager()
                if hasattr(vm, 'get_voices'):
                    try:
                        # 检查是否是协程函数
                        import inspect
                        if inspect.iscoroutinefunction(vm.get_voices):
                            return asyncio.run(vm.get_voices())
                        else:
                            return vm.get_voices()
                    except Exception:
                        return asyncio.run(vm.get_voices())
            except Exception:
                pass

        # 有些内部变量可能包含 voice 列表
        for attr in ('voices', '_voices', 'VOICE_LIST'):
            if hasattr(edge_tts, attr):
                val = getattr(edge_tts, attr)
                if isinstance(val, (list, tuple)):
                    return list(val)
    except Exception:
        logger.exception("列出 edge-tts voices 时出错")

    # 返回保守的默认列表，便于界面展示
    return [
        "zh-CN-YunjianNeural",
        "zh-CN-XiaoxiaoNeural",
        "en-US-JennyNeural",
        "en-US-GuyNeural"
    ]
