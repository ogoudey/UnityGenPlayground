from agents import Agent, Runner, function_tool
from pydantic import BaseModel
import asyncio

from dataclasses import dataclass, asdict

MODEL="o3-mini"

from assets import resources as RESOURCES

OFFLINE=False

@dataclass
class EnrichResponse():
    world_description: str
    explanation: str
    #next_agent: str


@dataclass
class MakeResponse(BaseModel):
    unity_file: str
    #next_agent: str
    
@dataclass
class CorrectMeResponse(BaseModel):
    new_unity_file: str
    explanation: str
    #next_agent: str
    
@dataclass
class NameResponse(BaseModel):
    name: str
    explanation: str
    #next_agent: str


@dataclass
class EnrichInstructions:
    default: str = "You are describing a scene in Unity based on the client's input. Keep it very minimal and assume few resources."
    role: str = None
    
    def __str__(self) -> str:
        return self.default + self.role if self.role else self.default
    
@dataclass
class MakeInstructions:
    default: str = "You are generating a scene in Unity based on the description of the world."
    role: str = None  
    
    def __str__(self) -> str:
        return self.default + self.role if self.role else self.default
        
@dataclass
class CorrectMeInstructions:
    default: str = "You just generated a .unity file based off of a client's input and the available resources. Fix the errors and return the .unity file."
    role: str = None  
    
    def __str__(self) -> str:
        return self.default + self.role if self.role else self.default

    
@dataclass
class EnrichPrompt:
    resources: str
    prompt: str
    
    def __str__(self) -> str:
        """Returns as string"""
        
        return "Given the prompt '" + self.prompt + "', please generate a detailed description of such a world or environment. (This world will later be generated in Unity, so make it feasible for another agent to generate a .unity description of.)"

@dataclass
class MakePrompt:
    """ Example dataclass for potential structuring of scene. """
    world_description: str
    unity_file: str
    resources: str
    
    
    def __str__(self) -> str:
        return "Given the world description " + self.world_description + " please generate a .unity file. You have these resources:\n" + self.resources + "Here's the start:\n" + self.unity_file 

@dataclass
class CorrectMePrompt:
    unity_file: str
    errors: str
    resources: str
    
    def __str__(self) -> str:
        return ".unity file: " + self.unity_file + "\n\nResources:\n" + self.resources + "\nErrors:\n" + self.errors 

client = Agent(
    name="Client",
    instructions=str(EnrichInstructions()),
    model=MODEL,   # cheapest currently available model
    output_type=EnrichResponse,
)

contractor = Agent(
    name="Contractor",
    instructions=str(MakeInstructions()), # You must assign agents to describe the scene.
    model=MODEL,   # cheapest currently available model
    output_type=MakeResponse,
)

repairman = Agent(
    name="Repairman",
    instructions=str(CorrectMeInstructions()), # You must assign agents to describe the scene.
    model=MODEL,   # cheapest currently available model
    output_type=CorrectMeResponse,
)

scene_namer = Agent(
    name="Scenenamer",
    instructions="Simply come up with a name for this world. Prefer single-word names.",
    model=MODEL,
    output_type=NameResponse,
)   

def save_unity_scene(yaml_string: str, path: str):
    """
    Save a YAML string as a .unity scene file.
    """
    if not path.endswith(".unity"):
        raise ValueError("File path must end with .unity")
    with open(path, "w", encoding="utf-8") as f:
        f.write(yaml_string)
    print(f"\nScene written to: {path}")

def recover_unity_scene(path: str) -> str:
    """
    Opens a .unity scene file as a YAML string.
    """
    if not path.endswith(".unity"):
        raise ValueError("File path must end with .unity")
        
    
        
    with open(path, "r", encoding="utf-8") as f:
        unity_file = f.read()
    print(f"\nScene read from: {path}")
    return unity_file

initial_file = """
%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
"""

async def main(prompt="Make a blank scene with two opposing cameras.", make_last=False):
    
    result = await Runner.run(client, str(EnrichPrompt(resources=[], prompt=prompt)))
    print(result.final_output) # Description
    
    result = await Runner.run(contractor, str(MakePrompt(world_description=result.final_output.world_description, unity_file=initial_file, resources=RESOURCES)))
    print(result.final_output.unity_file)
    
    name_result = await Runner.run(scene_namer, prompt)
    name = name_result.final_output.name
    
    import random
    world_name = prompt
    save_unity_scene(result.final_output.unity_file, "../Assets/Scenes/" + name + ".unity")
    if make_last:
        save_unity_scene(result.final_output.unity_file, "../Assets/Scenes/last.unity")
    return True

async def correct(path, errors="Syntax error", make_last=False):
    print("Recovering scene at "+path+" for corrections")
    if path.startswith("Assets"):
        path = "../" + path # because the path is different relative to this file than the menu
    unity_file = recover_unity_scene(path)
    
    if OFFLINE:
        # offline	
        print(unity_file)
        print(errors)
        print(RESOURCES)
        return True
        #
    
    result = await Runner.run(repairman, str(CorrectMePrompt(unity_file=unity_file, errors=errors, resources=RESOURCES)))
    print(result.final_output.new_unity_file) # Description
    
    if make_last:
        save_unity_scene(result.final_output.new_unity_file, "../Assets/Scenes/last.unity")
        save_unity_scene(result.final_output.new_unity_file, path)
    else:
        import random
        path = path.split(".unity")[0] + "x.unity"
        
        save_unity_scene(result.final_output.new_unity_file, path)
    return True

def run_prompt(prompt, make_last):
    asyncio.run(main(prompt, make_last))
    return True

def run_correction(path, errors, make_last):
    asyncio.run(correct(path, errors, make_last))
    return True

