import os
from typing import List
import uuid

WORLD_CLASS = os.environ.get("WORLD_CLASS", "UNITY")

if WORLD_CLASS == "UNITY":
    UNITY_WORLD_TYPE = os.environ.get("WORLD_TYPE", "UNITY_TWO_STEP")
    if UNITY_WORLD_TYPE == "UNITY_GRADUAL":
        MODE = "GRADUAL"
    elif UNITY_WORLD_TYPE == "UNITY_TWO_STEP":
        MODE = "TWO_STEP"

executions: List[tuple] = []

def post_write(func):
    # add the {func: args} to executions so that each function can be executed at another time with `k(v) for k,v in executions.items()`
    if MODE == "TWO_STEP":
        def wrapper(*args, **kwargs):
            buildID = str(uuid.uuid4())[-4:] 
            executions.append((buildID, func, (args, kwargs))) # Stays in build instructions
            return buildID # Goes to core -> world model
        return wrapper
    else:
        return func

def post_execute():
    
    if MODE == "TWO_STEP":
        print(f"Building YAML file...")
        for buildID, func, (args, kwargs) in executions:
            print(f"{func.__name__}")
<<<<<<< HEAD
        for buildID, func, (args, kwargs) in executions:
            print(f"Calling {func} on {args}, {kwargs}")
            try:
                func(*args, **kwargs)
            except Exception as e:
                print(f"FAILED to build on {func.__name__}({args}, {kwargs}):\n\n\t{e}")
=======
        for func, (args, kwargs) in executions:
            #print(f"Calling {func} on {args}, {kwargs}")
            try:
                func(*args, **kwargs)
            except Exception as e:
                print(f"Failed on {func.__name__}({args}, {kwargs}): {e}")
>>>>>>> 645fe225b05492ae321c72e859803effd9b451ab
    else:
        print(f"Not building YAML file... {UNITY_WORLD_TYPE}")
        pass

def dump_build_instructions():
    # dump each execution in string form
    pass

def remove_execution(buildID: str):
    print(f"Removing object with buildID {buildID}")
    for item in executions:
        if item[0] == buildID:
            del item
    print(f"Removed object with buildID {buildID}:\n {executions}")
