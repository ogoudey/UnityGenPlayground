import time
import os
import datetime
import shutil


def log(message: str, wait_time:float=0.1):
    """
    Appends a timestamped message to logs/<scene_name>.log.

    Also prints it??
    """
    
    log_name = os.environ.get("LOG", "xtbd")

    # Create logs directory (relative to current working directory)
    log_dir = os.path.join(os.getcwd(), "logs")
    
    os.makedirs(log_dir, exist_ok=True)

    # Construct the file path
    log_path = os.path.join(log_dir, f"{log_name}.log")

    # Timestamp the message
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{now} {message}\n"

    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
    except Exception as e:
        print("log error")

    # Also print to console
    #print(line, end="") # Removed because contributed to bug coming from Unity window

    if wait_time > 0.05: # not great - kind of a waste of time
        time.sleep(wait_time)

def done(log_name: str):
    """
    Waits 3 seconds, then moves logs/<scene_name>.log
    into archived_logs/<scene_name>.log (creating the folder if needed).
    """
    time.sleep(3)

    # Define paths
    cwd = os.getcwd()
    log_dir = os.path.join(cwd, "logs")
    archive_dir = os.path.join(cwd, "done_logs")

    os.makedirs(archive_dir, exist_ok=True)

    src = os.path.join(log_dir, f"{log_name}.log")
    dst = os.path.join(archive_dir, f"{log_name}.log")

    if os.path.exists(src):
        shutil.move(src, dst)
        print(f"Generation done. Moving log: {dst}")
    else:
        print(f"⚠️ Log file not found for scene '{log_name}' — nothing to be moved.")