import time

from multiprocessing import Manager

manager = None
queue = None


def log(message, type='normal'):
    global manager
    global queue
    
    if manager is None:
        manager = Manager()
        queue = manager.Queue()
    queue.put({"message": message, "type": type})
    time.sleep(0.001)
