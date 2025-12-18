#!/usr/bin/python
# coding:utf-8

import queue
import threading
from typing import Dict, Any, Optional


class MessageHandler:
    """
    消息处理器，用于集中处理和获取直播间的各种消息
    """

    def __init__(self, maxsize: int = 1000):
        """
        初始化消息处理器
        :param maxsize: 消息队列最大容量
        """
        self.message_queue = queue.Queue(maxsize=maxsize)
        self.running = True
        self.lock = threading.Lock()

    def add_message(self, msg_type: str, payload: Dict[str, Any]) -> bool:
        """
        添加消息到队列
        :param msg_type: 消息类型
        :param payload: 消息内容
        :return: 是否添加成功
        """
        if not self.running:
            return False

        message = {
            'type': msg_type,
            'payload': payload
        }

        try:
            self.message_queue.put(message, block=False)
            return True
        except queue.Full:
            # 队列满了，移除最旧的消息再添加新的
            try:
                self.message_queue.get_nowait()
                self.message_queue.put(message, block=False)
                return True
            except queue.Empty:
                return False

    def get_message(self, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        获取一条消息
        :param timeout: 超时时间（秒），None表示阻塞等待
        :return: 消息字典或None（超时或被关闭时）
        """
        if not self.running:
            return None

        try:
            return self.message_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def get_message_nowait(self) -> Optional[Dict[str, Any]]:
        """
        非阻塞获取一条消息
        :return: 消息字典或None（无消息时）
        """
        if not self.running:
            return None

        try:
            return self.message_queue.get_nowait()
        except queue.Empty:
            return None

    def size(self) -> int:
        """
        获取当前队列中的消息数量
        :return: 消息数量
        """
        return self.message_queue.qsize()

    def stop(self):
        """
        停止消息处理器
        """
        with self.lock:
            self.running = False

    def is_running(self) -> bool:
        """
        检查消息处理器是否正在运行
        :return: 是否正在运行
        """
        with self.lock:
            return self.running

    def clear(self):
        """
        清空消息队列
        """
        while not self.message_queue.empty():
            try:
                self.message_queue.get_nowait()
            except queue.Empty:
                break