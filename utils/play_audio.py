import os
import logging

logger = logging.getLogger(__name__)

from tts import play_audio_async as audio_module


def play_audio(file_path: str):
    """委托给后台 AudioPlayer 播放文件（非阻塞）"""
    if not os.path.exists(file_path):
        logger.error("错误：找不到文件 %s", file_path)
        return
    try:
        audio_module._AUDIO_PLAYER.play_file(file_path)
    except Exception:
        logger.exception("调用 AudioPlayer.play_file 失败")


def play_audio_file():
    audio_file = "test.mp3"
    if os.path.exists(audio_file):
        logger.info("正在播放: %s", audio_file)
        play_audio(audio_file)
    else:
        logger.warning("未找到音频文件: %s", audio_file)
        logger.warning("请先生成音频文件")