import os
from typing import List

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
            executions.append((func, (args, kwargs)))
        return wrapper
    else:
        return func
        def nothing(*args, **kwargs):
            return func(*args, **kwargs)
        return nothing

def post_execute():
    
    if MODE == "TWO_STEP":
        print(f"Building YAML file...")
        for func, (args, kwargs) in executions:
            print(f"{func.__name__}")
        for func, (args, kwargs) in executions:
            print(f"Calling {func} on {args}, {kwargs}")
            func(*args, **kwargs)
    else:
        print(f"Not building YAML file... {UNITY_WORLD_TYPE}")
        pass