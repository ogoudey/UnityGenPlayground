import os
from typing import List
import uuid
import json
WORLD_CLASS = os.environ.get("WORLD_CLASS", "UNITY")

if WORLD_CLASS == "UNITY":
    WORLD_GEN_TECHNIQUE = os.environ.get("WORLD_GEN_TECHNIQUE", "UNITY_TWO_STEP")
    if WORLD_GEN_TECHNIQUE == "UNITY_GRADUAL":
        MODE = "GRADUAL"
    elif WORLD_GEN_TECHNIQUE == "UNITY_TWO_STEP":
        MODE = "TWO_STEP"

executions: List[tuple] = []
func_registry = {}

def post_write(func):
    func_registry[func.__name__] = func
    # add the {func: args} to executions so that each function can be executed at another time with `k(v) for k,v in executions.items()`
    if MODE == "TWO_STEP":
        def wrapper(*args, **kwargs):
            buildID = str(uuid.uuid4())[-4:] 
            print(f"Appending {str(len(executions) + 1)}. {func.__name__} (ID: {buildID})")
            executions.append((buildID, func, (args[1:], kwargs))) # Stays in build instructions. Removed __self__
            return buildID # Goes to core -> world model
        return wrapper
    else:
        return func

def post_execute(world_instance):
    global executions
    if MODE == "TWO_STEP":
        i = 1
        print(f"Building YAML file with these functions:")
        for buildID, func, (args, kwargs) in executions:
            print(f"\t{i}. {func.__name__}")
            i += 1
        i = 1
        print(f"Executing:")
        for buildID, func, (args, kwargs) in executions:
            #print(f"Calling {func} on {world_instance}, {args}, {kwargs}")
            try:
                print(f"\t{i}. {func.__name__}")
                func(world_instance, *args, **kwargs)
                i += 1
            except Exception as e:
                print(f"FAILED to build on {func.__name__}({args}, {kwargs}):\n\n\t{e}")
        print(f"Clearing executions")
        executions = []
    else:
        print(f"Not building YAML file... {WORLD_GEN_TECHNIQUE}")
        pass

def remove_execution(buildID: str):
    print(f"Removing object with buildID {buildID}")
    for i, item in enumerate(executions):
        if item[0] == buildID:
            del executions[i]
            print(f"Removed object with buildID {buildID}.")
            return
    print(f"Could not find object with buildID {buildID}")

def dump_build_instructions(file_path):
    """
    Save the executions list to a file.
    Each entry: (buildID, func_name, (args, kwargs))
    """
    with open(file_path, "w") as f:
        i = 1
        # Convert args/kwargs to JSON-serializable
        serializable = []
        for buildID, func, (args, kwargs) in executions:
            print(f"\t\t{str(i)}. {func.__name__}")
            i += 1
            serializable.append({
                "buildID": buildID,
                "func": func.__name__,
                "args": args,
                "kwargs": kwargs
            })
        json.dump(serializable, f, indent=2)

def dump_propositions(file_path, propositions):
    dict_props = propositions.to_dict()
    for k, v in dict_props.items():
        print(f"\t\t{k}: {v}")

    with open(file_path, "w") as f:
        # Convert args/kwargs to JSON-serializable
        json.dump(dict_props, f, indent=2)

def recall_build_instructions(file_path):
    """
    Read the file, look up functions in func_registry, and execute them.
    Returns a list of (buildID, result)
    """
    with open(file_path, "r") as f:
        serializable = json.load(f)
    global executions
    executions = []
    for entry in serializable:
        buildID = entry["buildID"]
        func_name = entry["func"]
        args = entry["args"]
        kwargs = entry["kwargs"]
        print(f"Recalling {len(executions) + 1} {func_name}")
        func = func_registry.get(func_name)
        if func is None:
            raise ValueError(f"Function '{func_name}' not registered in func_registry")
        
        executions.append((buildID, func, (args, kwargs)))
        

def recall_propositions(file_path):
    with open(file_path, "r") as f:
        serializable = json.load(f)
    return serializable
