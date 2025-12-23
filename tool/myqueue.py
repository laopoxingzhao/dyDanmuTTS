import queue

import threading
import time

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