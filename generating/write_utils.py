import os
from typing import List
import uuid
import json
WORLD_CLASS = os.environ.get("WORLD_CLASS", "UNITY")

if WORLD_CLASS == "UNITY":
    UNITY_WORLD_TYPE = os.environ.get("WORLD_TYPE", "UNITY_TWO_STEP")
    if UNITY_WORLD_TYPE == "UNITY_GRADUAL":
        MODE = "GRADUAL"
    elif UNITY_WORLD_TYPE == "UNITY_TWO_STEP":
        MODE = "TWO_STEP"

executions: List[tuple] = []
func_registry = {}

def post_write(func):
    func_registry[func.__name__] = func
    # add the {func: args} to executions so that each function can be executed at another time with `k(v) for k,v in executions.items()`
    if MODE == "TWO_STEP":
        def wrapper(*args, **kwargs):
            buildID = str(uuid.uuid4())[-4:] 
            executions.append((buildID, func, (args[1:], kwargs))) # Stays in build instructions. Removed __self__
            return buildID # Goes to core -> world model
        return wrapper
    else:
        return func

def post_execute(world_instance):
    
    if MODE == "TWO_STEP":
        print(f"Building YAML file...")
        for buildID, func, (args, kwargs) in executions:
            print(f"{func.__name__}")
        for buildID, func, (args, kwargs) in executions:
            #print(f"Calling {func} on {world_instance}, {args}, {kwargs}")
            try:
                func(world_instance, *args, **kwargs)
            except Exception as e:
                print(f"FAILED to build on {func.__name__}({args}, {kwargs}):\n\n\t{e}")
    else:
        print(f"Not building YAML file... {UNITY_WORLD_TYPE}")
        pass

def remove_execution(buildID: str):
    print(f"Removing object with buildID {buildID}")
    for item in executions:
        if item[0] == buildID:
            del item
    print(f"Removed object with buildID {buildID}:\n {executions}")

def dump_build_instructions(file_path):
    """
    Save the executions list to a file.
    Each entry: (buildID, func_name, (args, kwargs))
    """
    with open(file_path, "w") as f:
        # Convert args/kwargs to JSON-serializable
        serializable = []
        for buildID, func, (args, kwargs) in executions:
            print(f"Dumping {func.__name__}")
            serializable.append({
                "buildID": buildID,
                "func": func.__name__,
                "args": args,
                "kwargs": kwargs
            })
        json.dump(serializable, f, indent=2)

def dump_propositions(file_path, propositions):
    print(f"Dumping propositions")
    with open(file_path, "w") as f:
        # Convert args/kwargs to JSON-serializable
        serializable = []
        json.dump(propositions.to_dict(), f, indent=2)

def recall_build_instructions(file_path):
    """
    Read the file, look up functions in func_registry, and execute them.
    Returns a list of (buildID, result)
    """
    with open(file_path, "r") as f:
        serializable = json.load(f)
    
    executions = []
    for entry in serializable:
        buildID = entry["buildID"]
        func_name = entry["func"]
        args = entry["args"]
        kwargs = entry["kwargs"]
        print(f"Recalling {func_name}")
        func = func_registry.get(func_name)
        if func is None:
            raise ValueError(f"Function '{func_name}' not registered in func_registry")
        
        executions.append((buildID, func, (args, kwargs)))
        print(f"Executions {executions}")

def recall_propositions(file_path):
    with open(file_path, "r") as f:
        serializable = json.load(f)
    return serializable
