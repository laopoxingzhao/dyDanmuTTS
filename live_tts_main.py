import asyncio
import threading
from edgetts.play_audio_async import play_text

from liveMan import DouyinLiveWebFetcher


class LiveTTS:
    """直播TTS播放器"""
    
    def __init__(self, live_id):
        self.live_id = live_id
        self.fetcher = DouyinLiveWebFetcher(live_id)
        self.running = True

    def start(self):
        """启动直播监听和TTS播放"""
        # 启动直播监听线程
        listener_thread = threading.Thread(target=self._listen_danmaku, name="DanmakuListener")
        listener_thread.daemon = True
        listener_thread.start()
        
        # 启动TTS播放线程
        player_thread = threading.Thread(target=self._tts_player, name="TTSPlayer")
        player_thread.daemon = True
        player_thread.start()
        
        # 等待监听线程结束
        try:
            listener_thread.join()
        except KeyboardInterrupt:
            print("程序退出")
            self.running = False

    def _listen_danmaku(self):
        """监听抖音弹幕"""
        try:
            self.fetcher.start()
        except Exception as e:
            print(f"监听弹幕时发生错误: {e}")

    def _tts_player(self):
        """TTS播放线程"""
        while self.running and self.fetcher.message_handler.is_running():
            try:
                # 从消息处理器获取消息
                message = self.fetcher.get_message(timeout=1)
                
                if message and message['type'] == 'chat':
                    # 处理聊天消息
                    content = message['payload']['content']
                    user_name = message['payload']['user_name']
                    
                    text_to_speak = f"{user_name}说：{content}"
                    print(f"[TTS队列] 添加消息: {text_to_speak}")
                    
                    # 检查是否包含"咨询"关键词
                    if "咨询" in text_to_speak:
                        print(f"[TTS播放] 开始播放: {text_to_speak}")
                        # 调用TTS播放功能
                        try:
                            loop = asyncio.new_event_loop()
                            loop.run_until_complete(play_text(text_to_speak))
                            loop.close()
                        except Exception as e:
                            print(f"TTS播放出错: {e}")
                            continue
                        
            except Exception as e:
                print(f"TTS播放时发生错误: {e}")
                continue


# 程序入口
if __name__ == "__main__":
    # 需要提供实际的直播间ID
    LIVE_ID = ""  # 替换为实际的直播间ID
    
    # 判断输入是否为空
    # 去除空格
    LIVE_ID = LIVE_ID.strip()
    if not LIVE_ID:
        LIVE_ID = input("请输入抖音直播房间ID：")        
    
    # 创建并启动TTS播放器
    tts_player = LiveTTS(LIVE_ID)
    try:
        tts_player.start()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序运行出错: {e}")