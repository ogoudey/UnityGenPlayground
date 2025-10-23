import time
#import queue
import os
from queue import Queue

_manager = None
queue = None




def log(message, type="normal"):
    global queue
    if queue is None:
        queue = Queue()
    #print("[logger] Queue object id:", id(queue))
    queue.put({"message": message, "type": type})
    #print(f"[Logger] queue size: {queue.qsize()}")
