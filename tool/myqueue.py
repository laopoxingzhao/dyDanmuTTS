import queue

import threading
import time

class MyQueue:
    def __init__(self):
        self.queue = queue.Queue()

    def put(self, item):
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
