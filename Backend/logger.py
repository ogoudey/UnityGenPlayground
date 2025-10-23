import time
#import queue
import os
import queue

from multiprocessing import Manager

_manager = None
queue = None




def log(message, type):
    if queue is None:
        queue = queue.Queue()
    print("[logger] Queue object id:", id(queue))
    queue.put({"message": message, "type": type})
    print(f"[Logger] queue size: {queue.qsize()}")
    print("[Logger]", queue.pop(0)[0])