import time
import os
import datetime
import shutil

def log(message: str, scene_name: str, wait_time:float=0.0):
    """
    Appends a timestamped message to logs/<scene_name>.log.

    Also prints it
    """
    # Create logs directory (relative to current working directory)
    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)

    # Construct the file path
    log_path = os.path.join(log_dir, f"{scene_name}.log")

    # Timestamp the message
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{now} {message}\n"

    # Write (live append)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line)
        f.flush()

    # Also print to console
    print(line, end="")
    if wait_time > 0.1:
        time.sleep(wait_time)

def done(scene_name: str):
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

    src = os.path.join(log_dir, f"{scene_name}.log")
    dst = os.path.join(archive_dir, f"{scene_name}.log")

    if os.path.exists(src):
        shutil.move(src, dst)
        print(f"Generation done. Moving log: {dst}")
    else:
        print(f"⚠️ Log file not found for scene '{scene_name}' — nothing to be moved.")