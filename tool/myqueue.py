import queue
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
import re
from config.config_manager import ConfigManager

class MyQueue:
    def __init__(self):
        self.queue = queue.Queue()

    def put(self, type_or_item, content=None):
        # 如果只传入一个参数，则按原方式处理
        if content is None:
            self.queue.put(type_or_item)
        # 如果传入两个参数，则组合成字典存储
        else:
            item = {
                'type': type_or_item,
                'content': content
            }
            self.queue.put(item)

    def get(self):
        return self.queue.get()

    def empty(self):
        return self.queue.empty()

    def size(self):
        return self.queue.qsize()

    def clear(self):
        self.queue.queue.clear()

uiq= MyQueue()


class TtsQueue:
    """
    TTS队列系统，用于在大量弹幕中生成代表性音频
    使用去重、频率控制和代表性选择算法来减少重复播报
    """
    
    def __init__(self, dedup_time_window=30, min_interval=5, max_queue_size=20):
        """
        初始化TTS队列
        :param dedup_time_window: 去重时间窗口（秒），在此时间内的重复内容将被过滤
        :param min_interval: 同类型消息最小播报间隔（秒）
        :param max_queue_size: 队列最大长度，超过此长度将丢弃旧消息
        """
        self.queue = queue.Queue()
        self.dedup_cache = {}  # 用于去重的缓存
        self.type_last_time = defaultdict(float)  # 记录各类型消息最后播报时间
        self.time_window_cache = {}  # 用于时间窗口去重
        self.lock = threading.Lock()
        self.dedup_time_window = dedup_time_window
        self.min_interval = min_interval
        self.max_queue_size = max_queue_size
        self.recent_messages = deque(maxlen=max_queue_size)  # 保存最近的消息用于去重

    def should_filter_message(self, msg_type, content):
        """
        判断是否应该过滤此消息
        :param msg_type: 消息类型
        :param content: 消息内容
        :return: True表示应该过滤，False表示应该保留
        """
        current_time = time.time()
        
        # 检查是否在去重时间窗口内已存在相同内容
        content_key = f"{msg_type}:{content}"
        if content_key in self.dedup_cache:
            last_time = self.dedup_cache[content_key]
            if current_time - last_time < self.dedup_time_window:
                # 如果在时间窗口内，检查是否需要特殊处理
                return True
        
        # 检查是否超过队列最大长度
        if self.queue.qsize() >= self.max_queue_size:
            print(f"TTS队列已满({self.max_queue_size})，丢弃新消息: {content}")
            return True
        
        # 检查同类型消息的最小间隔
        if current_time - self.type_last_time[msg_type] < self.min_interval:
            # 对于频繁的消息类型，可以考虑只保留有特殊意义的消息
            if msg_type in ['WebcastChatMessage', 'WebcastLikeMessage']:
                # 对于聊天和点赞消息，可以设置更高的过滤阈值
                return True
        
        return False

    def put(self, msg_type, content, user_name=None, gift_name=None, gift_count=None):
        """
        添加消息到TTS队列
        :param msg_type: 消息类型
        :param content: 消息内容
        :param user_name: 用户名（可选）
        :param gift_name: 礼物名称（可选）
        :param gift_count: 礼物数量（可选）
        """
        with self.lock:
            # 根据消息类型生成TTS文本
            tts_text = self._generate_tts_text(msg_type, content, user_name, gift_name, gift_count)
            
            # 检查是否应该过滤此消息
            if self.should_filter_message(msg_type, tts_text):
                return False
            
            # 更新缓存
            content_key = f"{msg_type}:{tts_text}"
            self.dedup_cache[content_key] = time.time()
            self.type_last_time[msg_type] = time.time()
            
            # 添加到队列
            item = {
                'type': msg_type,
                'content': tts_text,
                'timestamp': time.time()
            }
            self.queue.put(item)
            self.recent_messages.append(item)
            
            return True

    def _generate_tts_text(self, msg_type, content, user_name, gift_name, gift_count):
        """
        根据消息类型和参数生成TTS文本
        """
        if msg_type == 'WebcastMemberMessage' and user_name:
            # 用户进入消息
            return f"{user_name}进入了直播间"
        elif msg_type == 'WebcastSocialMessage' and user_name:
            # 关注消息
            return f"{user_name}关注了主播"
        elif msg_type == 'WebcastGiftMessage' and user_name and gift_name:
            # 礼物消息
            count_str = f"x{gift_count}" if gift_count and gift_count > 1 else ""
            return f"{user_name}送出了{gift_name}{count_str}"
        elif msg_type == 'WebcastChatMessage' and user_name and content:
            # 聊天消息，只播报部分关键词或有意义的消息
            # 过滤常见无意义内容
            common_content = ['', '6', '666', '888', '...', '？', '！', '好', '不错', '支持']
            if content.strip() in common_content:
                return f"{user_name}说: {content}"
            elif len(content.strip()) < 2:
                # 太短的内容不播报
                return f"{user_name}说: {content}"
            else:
                # 有意义的聊天内容才播报
                return f"{user_name}说: {content}"
        else:
            # 其他类型的消息直接返回内容
            return content or ""

    def get(self):
        """
        从队列获取一个TTS消息
        """
        if not self.queue.empty():
            return self.queue.get()
        return None

    def empty(self):
        """
        检查队列是否为空
        """
        return self.queue.empty()

    def size(self):
        """
        获取队列大小
        """
        return self.queue.qsize()

    def clear(self):
        """
        清空队列
        """
        with self.lock:
            self.queue.queue.clear()
            self.dedup_cache.clear()
            self.type_last_time.clear()
            self.recent_messages.clear()
    
    def update_config(self, dedup_time_window=None, min_interval=None, max_queue_size=None):
        """
        更新配置参数
        """
        with self.lock:
            if dedup_time_window is not None:
                self.dedup_time_window = dedup_time_window
            if min_interval is not None:
                self.min_interval = min_interval
            if max_queue_size is not None:
                self.max_queue_size = max_queue_size
                # 重新创建deque以应用新的最大长度
                old_messages = list(self.recent_messages)
                self.recent_messages = deque(maxlen=max_queue_size)
                # 添加最近的消息
                for msg in old_messages[-max_queue_size:]:
                    self.recent_messages.append(msg)

# 创建全局TTS队列实例，初始使用默认配置
ttsq = TtsQueue()