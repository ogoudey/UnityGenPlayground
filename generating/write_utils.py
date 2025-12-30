import os

WORLD_CLASS = os.environ.get("WORLD_CLASS", "UNITY")

if WORLD_CLASS == "UNITY":
    UNITY_WORLD_TYPE = os.environ.get("WORLD_TYPE", "UNITY_TWO_STEP")
    if UNITY_WORLD_TYPE == "UNITY_GRADUAL":
        MODE = "GRADUAL"
    elif UNITY_WORLD_TYPE == "UNITY_TWO_STEP":
        MODE = "TWO_STEP"

executions = {}

def post_write(func):
    # add the {func: args} to executions so that each function can be executed at another time with `k(v) for k,v in executions.items()`
    if MODE == "TWO_STEP":
        def wrapper(*args, **kwargs):
            executions[func] = (args, kwargs)
        return wrapper
    else:
        return func
        def nothing(*args, **kwargs):
            return func(*args, **kwargs)
        return nothing

def post_execute():
    if MODE == "TWO_STEP":
        for func, (args, kwargs) in executions.items():
            func(*args, **kwargs)
    else:
        pass