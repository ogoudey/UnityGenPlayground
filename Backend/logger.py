from multiprocessing import Manager

manager = Manager()
queue = manager.Queue()

def log(message, type='normal'):
    queue.put({"message": message, "type": type})