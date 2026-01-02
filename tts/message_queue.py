"""
消息队列模块 - 管理TTS消息队列
"""
import threading
import time
from queue import PriorityQueue, Empty
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from config.log import g_logger


class MessageType(Enum):
    """消息类型枚举"""
    KEYWORD_REPLY = 1  # 关键词回复
    DANMU_CHAT = 2     # 普通弹幕
    SYSTEM_MESSAGE = 3  # 系统消息
    MEMBER_ENTER = 4   # 进入直播间
    GIFT_SEND = 5      # 送礼
    SOCIAL_FOLLOW = 6  # 关注
    LIKE = 7           # 点赞


@dataclass(order=True)
class TTSMessage:
    """TTS消息"""
    priority: int = field(compare=True)
    message_type: MessageType = field(compare=False)
    text: str = field(compare=False)
    variables: Dict[str, Any] = field(default_factory=dict, compare=False)
    timestamp: float = field(default_factory=time.time, compare=False)
    
    def __post_init__(self):
        """初始化后处理"""
        if self.priority < 0:
            self.priority = 0
        elif self.priority > 10:
            self.priority = 10


class MessageQueue:
    """TTS消息队列"""
    
    def __init__(self, max_size: int = 30):
        """
        初始化消息队列
        
        Args:
            max_size: 队列最大大小
        """
        self.queue = PriorityQueue(maxsize=max_size)
        self.max_size = max_size
        self.current_size = 0
        self._lock = threading.Lock()
        
        # 统计信息
        self.stats = {
            'total_added': 0,
            'total_processed': 0,
            'total_dropped': 0,
            'queue_size': 0
        }
        
        g_logger.info(f"TTS消息队列初始化 - 最大大小: {max_size}")
    
    def add_message(self, text: str, priority: int = 5, 
                   message_type: MessageType = MessageType.DANMU_CHAT,
                   variables: Dict[str, Any] = None) -> bool:
        """
        添加消息到队列
        
        Args:
            text: 消息文本
            priority: 优先级 (0-10, 越高越优先)
            message_type: 消息类型
            variables: 变量字典
            
        Returns:
            bool: 是否添加成功
        """
        try:
            with self._lock:
                # 检查队列是否已满
                if self.current_size >= self.max_size:
                    # 移除最低优先级的消息
                    self._remove_lowest_priority()
                
                # 创建消息对象
                message = TTSMessage(
                    priority=priority,
                    message_type=message_type,
                    text=text,
                    variables=variables or {}
                )
                
                # 添加到队列
                self.queue.put(message)
                self.current_size += 1
                self.stats['total_added'] += 1
                self.stats['queue_size'] = self.current_size
                
                g_logger.debug(f"添加消息到队列: {text[:30]}... (优先级: {priority})")
                return True
                
        except Exception as e:
            g_logger.error(f"添加消息到队列失败: {e}")
            return False
    
    def get_message(self, timeout: float = 1.0) -> Optional[TTSMessage]:
        """
        从队列获取消息
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            TTSMessage or None: 消息对象或None
        """
        try:
            message = self.queue.get(timeout=timeout)
            
            with self._lock:
                self.current_size -= 1
                self.stats['total_processed'] += 1
                self.stats['queue_size'] = self.current_size
            
            g_logger.debug(f"从队列获取消息: {message.text[:30]}...")
            return message
            
        except Empty:
            return None
        except Exception as e:
            g_logger.error(f"从队列获取消息失败: {e}")
            return None
    
    def clear(self):
        """清空队列"""
        with self._lock:
            while not self.queue.empty():
                try:
                    self.queue.get_nowait()
                except Empty:
                    break
            
            self.current_size = 0
            self.stats['queue_size'] = 0
            
        g_logger.info("TTS消息队列已清空")
    
    def get_size(self) -> int:
        """获取当前队列大小"""
        return self.current_size
    
    def is_empty(self) -> bool:
        """检查队列是否为空"""
        return self.current_size == 0
    
    def is_full(self) -> bool:
        """检查队列是否已满"""
        return self.current_size >= self.max_size
    
    def _remove_lowest_priority(self):
        """移除最低优先级的消息"""
        try:
            # 获取所有消息
            messages = []
            while not self.queue.empty():
                try:
                    messages.append(self.queue.get_nowait())
                except Empty:
                    break
            
            # 按优先级排序
            messages.sort(key=lambda x: x.priority)
            
            # 移除最低优先级的消息
            if messages:
                removed = messages.pop(0)
                g_logger.debug(f"移除低优先级消息: {removed.text[:30]}...")
                self.stats['total_dropped'] += 1
            
            # 重新添加剩余消息
            for msg in messages:
                self.queue.put(msg)
                
        except Exception as e:
            g_logger.error(f"移除低优先级消息失败: {e}")
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.stats.copy()
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'total_added': 0,
            'total_processed': 0,
            'total_dropped': 0,
            'queue_size': self.current_size
        }
        g_logger.info("消息队列统计已重置")