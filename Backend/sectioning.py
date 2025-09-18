import sys
from threading import Thread
import time # sub for actual prompting

from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
import uuid

from dataclasses import dataclass, asdict
import json
import random

import prompting
import yamling

from agents import Agent, Runner, function_tool
from pydantic import BaseModel
import asyncio

from dataclasses import dataclass, asdict

from obj_building import obj_from_grid

import assets
prefab_tree = assets.get_found(".prefab")
material_tree = assets.get_found(".mat")

MODEL="o3-mini"

RESTRICTIONS="""In fact, only describe objects that are commonly found in scenes built in the game engine Unity. IN FACT, ONLY USE THESE ASSETS:\n"""+str(prefab_tree)+"""."""

class UnityFile:
    def __init__(self, name="testingtesting123"):
        self.name = name
        self.yaml = yamling.YAML()

    def add_skybox(self, meta_file):
        print("+ Skybox")
        guid = yamling.get_guid(meta_file)
        self.yaml.set_skybox(guid)
        
            
    def add_prefab(self, meta_file, transform, rotation):
        print("+ Prefab")
        guid = yamling.get_guid(meta_file)
        prefab_path = meta_file.removesuffix(".meta")
        self.yaml.add_prefab_instance(guid, prefab_path, transform, rotation)
         
              
    def add_ground(self, obj_path, transform={"x":0.0, "y":0.0, "z":0.0}):
        print("+ Ground")
        guid = uuid.uuid4().hex
        yamling.write_obj_meta(obj_path, guid)
        self.yaml.add_ground_prefab_instance(guid, transform)
        
        
    def done_and_write(self, file_name=None):
        if not file_name:
            file_name = self.name
        self.yaml.to_unity_yaml(file_name)
        
global unity


class Designation(BaseModel):
    asset_path: str

class GroundData(BaseModel):
    grid: str

@function_tool
async def objectConsult(object_description: str, location: str, rotation: str='{"x": 0.0, "y": 0.0, "z": 0.0}') -> str:
    """ 
        Args:
            object_description: Some text that the describes the object and provides enough information to specifically retrieve the asset from a library/folder of assets.
            location: \"\"\"{"x": float, "y": float, "z": float}" - e.g. "{"x": 75, "y": 10, "z": 70}\"\"\". Remember - Y is up and these units are in base units - meters.
            rotation: \"\"\"{"x": float, "y": float, "z": float}" - e.g. "{"x": 90, "y": 0, "z": 45}\"\"\". These are the angles to rotate around the axis.
    """
    agent = Agent(
        name="ObjectConsultant" + str(random.randint(100, 999)),
        output_type = Designation,
        instructions="Retrieve the asset from the list of available assets that best matches the intended description.",
        model=MODEL  
    )
    
    prompt = {"Object description": object_description,
                "Available assets": prefab_tree}
    t = time.time()
    result = await Runner.run(agent, json.dumps(prompt))
    print(agent.name + ":", time.time() - t, "seconds.")
    asset_path = result.final_output.asset_path + ".meta"

    
    try:
        json_location = json.loads(location)
        json_rotation = json.loads(rotation)
    except Exception as e:
        print(e)
        print("Could not JSONify:", e)
        return f"Failed to add object with description '{object_description}' to {location} in the scene. Make sure to pass a correct something that can be loaded with json.loads() into JSON."
    print("JSON extracted for object with description '{object_description}'.")
    try:
        global unity
        print(f"An object with description '{object_description}' is going to be added to: {location}")
        unity.add_prefab(asset_path, json_location, json_rotation)
        return f"Successfully added object with description '{object_description}' to {location} in the scene, using the asset {result.final_output.asset_path}."
    except Exception as e:
        return f"Could not add asset, likely because nothing an object with a description '{object_description}' is available in the library of assets. {asset_path}"


CHEATS = """ IN FACT, just to make things absolutely sure, put the water at z=50. All other objects just go in the -X +Z quadrant."""

@function_tool
async def createObject(description: str, location: str, rotation: str, explanation: str="") -> str:
    """ 
        Args:
            description: Some text describing that the object should be like, refering to a singular object that's likely to be selected from a common asset library.
            location: \"\"\"{"x": float, "y": float, "z": float}" - e.g. "{"x": 75, "y": 10, "z": 70}\"\"\". Remember - Y is up and these units are in base units - meters. All objects are in the -X +Y -Z quadrant, so to cover the -X, +Z ground put the object at z=Z_object where Z_object is the of the z-side (z dimension) of the object."""+CHEATS+"""
            rotation: \"\"\"{"x": float, "y": float, "z": float}" - e.g. "{"x": 90, "y": 0, "z": 45}\"\"\". These are the angles to rotate around the axis. Defaults to no rotation.
            explanation: Your reasoning for the above args you've settled on, with particular emphasis on correct positioning of the object.
    """
    print("Explanation:", explanation)
    
    agent = Agent(
        name="ObjectCreator" + str(random.randint(100, 999)),
        tools=[objectConsult],
        #instructions="It is your job to prompt an asset-retriever to get the object you are assigned to place. For example, given that you are supposed to put a rock at [1.2, 2.8, -1.5] and this location is 1m high, the object must be extend at least 1m below its center point, otherwise it is floating mid-air."
        instructions= "Name the object and use the objectConsult tool to retrieve the asset path.",
        model=MODEL
    )
    
    
    
    prompt = {"Description of object": description,
                "Intended location of object": location,
                "Intended rotation of object": rotation}
    t = time.time()
    await Runner.run(agent, json.dumps(prompt))
    print(agent.name + ":", time.time() - t, "seconds.")
    print("--------------object creation done-------------------")
    return f"Successfully called objectConsult."

async def test_river(prompt="A river with two opposing banks"):
    global unity
    unity = UnityFile("test_river" + str(random.randint(100, 999)))
    

    
    section_leaderl0 = Agent(
        name="SectionLeaderL0wGroundLeader",
        tools=[createObject, createGround],
        instructions="""You are an architect of a scene. According to the prompt, you design a (section of a) scene by creating objects. Reference one object per call to createObject, since some downstream agent needs to take your description and find the right asset. You should create the ground before any objects are created, so that you can properly arrange objects in the scene. To create the ground, you prompt an agent to generate a heightmap that fits the scene. Make sure to place objects ATOP the ground.""" + RESTRICTIONS + CHEATS,
        model=MODEL
    )
    
    prompt = {"Description of the scene": prompt}
    
    await Runner.run(section_leader0_w_groundleader, json.dumps(prompt))

@function_tool
async def createSectionL0(prompt: str, region: str):
    section_leaderl0 = Agent(
        name="SectionLeaderL0wGroundLeader",
        tools=[createObject, createGround],
        instructions="""You are an architect of a scene. According to the prompt, you design a (section of a) scene by creating objects. Reference one object per call to createObject, since some downstream agent needs to take your description and find the right asset. You should create the ground before any objects are created, so that you can properly arrange objects in the scene. To create the ground, you prompt an agent to generate a heightmap that fits the scene. Make sure to place objects ATOP the ground.""" + RESTRICTIONS + CHEATS,
        model=MODEL
    )
    
    prompt = {"Description of the scene": prompt}
    
    await Runner.run(section_leader0_w_groundleader, json.dumps(prompt))
    return f"Successfully allocated generation of this section which has description '{description}'."

@function_tool
async def createSectionL1(description: str, region: str):
    agent = Agent(
        name="SectionLeader" + str(random.randint(100, 999)),
        tools=[createSectionL0, createObject],
        instructions="You are an architect of a scene. According to the prompt, you design a (section of a) scene by either creating objects or by (recursively) assigning a 'section leader' (like yourself) to a sub-section of the scene which is restricted to a region.",
        model=MODEL
    )
    
    prompt = {"Description of your section": description, "Region to work in": region}
    
    await Runner.run(agent, json.dumps(prompt))
    return f"Successfully allocated generation of this section which has description '{description}'."
 
@function_tool
async def createSectionL2(description: str, region: str):
    agent = Agent(
        name="SectionLeader" + str(random.randint(100, 999)),
        tools=[createSectionL1, createObject],
        instructions="You are an architect of a scene. According to the prompt, you design a (section of a) scene by either creating objects or by (recursively) assigning a 'section leader' (like yourself) to a sub-section of the scene which is restricted to a region.",
        model=MODEL
    )
    
    prompt = {"Description of your section": description, "Region to work in": region}
    
    await Runner.run(agent, json.dumps(prompt))
    return f"Successfully allocated generation of this section which has description '{description}'."


@function_tool
async def skyboxConsult(skybox_description: str, important_info: str="skybox1 has blue sky, skybox2 has cloudy sky") -> Designation:
    agent = Agent(
        name="SkyboxConsultant" + str(random.randint(100, 999)),
        output_type = Designation,
        instructions="Given the directory structure (asset tree), return the path to the file of the desired asset.",
        model=MODEL
        
    )
    prompt = {"Object description": skybox_description,
                "Available assets": material_tree}

    result = await Runner.run(agent, json.dumps(prompt))
    asset_path = result.final_output.asset_path
    
    global unity
    unity.add_skybox(asset_path + ".meta")
    print("--------------skybox creation done-------------------") 
    return f"Successfully added skybox with description '{skybox_description}' to the scene."

async def createSkyboxLeader(description: str="Plain blue sky"):
    
    agent = Agent(
        name="SkyboxLeader",
        tools=[skyboxConsult],
        instructions="You will be given a description of an intended Unity scene and you are to prompt an agent (through the skyboxConsult tool) to select the right asset. Name the object and use the skyboxConsult tool to retrieve the asset path. The agent you prompt will be looking for a skybox that corresponds to your prompt."
    )
    
    prompt = {"Description of scene": description}
    
    result = await Runner.run(agent, json.dumps(prompt))
    
    return f"Successfully added skybox given description '{description}'"

@function_tool
async def createGround(ground_description: str):
    """ 
        ground_description: a description of what the ground should look like.
    """

    agent = Agent(
        name="GroundCreator",
        instructions="Give me a 10x10 grid of floats, written out directly as rows of numbers, no code, that represents the heightmap of the ground described by the prompt.",
        output_type=GroundData
    )
    prompt = {"Description of the ground": ground_description}
    
    t = time.time()
    result = await Runner.run(agent, json.dumps(prompt))
    print(agent.name + ":", time.time() - t, "seconds.")
    
    asset_path, matrix = obj_from_grid(result.final_output.grid) # writes obj
    print("Ground obj written.")
    
    global unity    
    unity.add_ground(asset_path)
    
    print(matrix)
    print("--------------ground creation done-------------------") 
    unit_size = 5
    
    return f"ground created with heightmap:\n{result.final_output.grid}\nEach cell is {unit_size}m by {unit_size}m, and this grid goes in the -X and +Z directions. The value in each cell represents the height/Y dimension of the ground in base units. Anything below that amount will be below the ground and invisible. Keep these facts in mind for further object placement."

@function_tool
async def createGroundLeader(description: str="A mountain"):
    
    agent = Agent(
        name="GroundLeader",
        tools=[createGround],
        instructions="You will be given a description of an intended Unity scene and you are to prompt an agent (through the groundConsult tool) to generate a heightmap. You're going to "
    )
    
    prompt = {"Description of scene": description}
    
    result = await Runner.run(agent, json.dumps(prompt))
    
    return f"Successfully added skybox given description '{description}'" 
   
async def main(prompt):
    global unity
    unity = UnityFile("test0")
    
    await createSkyboxLeader(prompt)


    
    agent = Agent(
        name="SectionLeader0",
        tools=[createSectionL2, createObject],
        instructions="You are an architect of a scene, you design a (section of a) scene by either creating objects, or by (recursively) assigning a 'section leader' (like yourself) to a sub-section of the scene which is restricted to a region.",
        model=MODEL
    )
    
    prompt = {"Description of your section": prompt, "Region to work in": "completely open - scene origin is at (0,0,0)"}
    
    await Runner.run(agent, json.dumps(prompt))
    
    unity.done_and_write() # writes


""" Tests """


async def test_skybox(prompt="A forest with the sun out"):
    

    global unity
    unity = UnityFile("test_skybox" + str(random.randint(100, 999)))
    
    await createSkyboxLeader(prompt) # success/fail
    
    unity.done_and_write()
    
async def test_ground(prompt="A mountain"):
    

    global unity
    unity = UnityFile("test_ground" + str(random.randint(100, 999)))
    
    #await createGroundLeader(prompt) # commented because it needs a NotAsTool implementation
    
    unity.done_and_write()

async def test_leaves(prompt="A forest"):
    

    global unity
    unity = UnityFile("test_leaves" + str(random.randint(100, 999)))
    
    await createObjectNotAsTool(description="a spruce tree", location={"x": -1045.6066, "y": 2196.2122, "z": 3885.3037}, other_important_info="clear for placement")
    await createObjectNotAsTool(description="a spruce tree", location={"x": -1145.6066, "y": 2196.2122, "z": 3885.3037}, other_important_info="clear for placement")
    await createObjectNotAsTool(description="a rock", location={"x": -1145.6066, "y": 2196.2122, "z": 3885.3037}, other_important_info="clear for placement")
    
    unity.done_and_write()
    


async def test_stem(prompt="Two trees"):
    

    global unity
    unity = UnityFile("test_stem" + str(random.randint(100, 999)))
    
    #await createSkyboxLeader(prompt) # success/fail
    
    section_leader0 = Agent(
        name="SectionLeaderL0",
        tools=[createObject],
        instructions="""You are an architect of a scene. According to the prompt, you design a (section of a) scene by creating objects. Reference one object per call to createObject, since some downstream agent needs to take your description and find the right asset.""" + RESTRICTIONS,
        model=MODEL
    )
    
    prompt = {"Description of your section": prompt, "Region to work in": "completely open - scene origin is at (0,0,0)"}
    
    await Runner.run(section_leader0, json.dumps(prompt))
    
    unity.done_and_write()

async def test_create_ground(prompt={"ground_description": "a mountain", "location": '{"x":0.0, "y":0.0, "z":0.0}', "grid_dimensions": "20 by 20", "unit_size": 10.0}):
    global unity
    unity = UnityFile("test_create_ground" + str(random.randint(100, 999)))
    
    await createGroundNotAsTool(prompt["ground_description"], prompt["location"], prompt["grid_dimensions"], prompt["unit_size"])
    
    unity.done_and_write()
    
  
async def test_stem_and_sky(prompt="A forest"):
    

    global unity
    unity = UnityFile("test_stem_and_sky" + str(random.randint(100, 999)))
    
    await createSkyboxLeader(prompt) # success/fail
    
    section_leader0 = Agent(
        name="SectionLeaderL0",
        tools=[createObject],
        instructions="""You are an architect of a scene. According to the prompt, you design a (section of a) scene by either creating objects or by (recursively) assigning a 'section leader' (like yourself) to a sub-section of the scene which is restricted to a region. Reference one object per call to createObject, since some downstream agent needs to take your description and find the right asset.""" + RESTRICTIONS,
        model=MODEL
    )
    
    prompt = {"Description of your section": prompt, "Region to work in": "completely open - scene origin is at (0,0,0)"}
    
    await Runner.run(section_leader0, json.dumps(prompt))
    
    unity.done_and_write()
    
async def test_L1(prompt="A forest"):
    

    global unity
    unity = UnityFile("test_L1" + str(random.randint(100, 999)))
    await createSkyboxLeader(prompt) # success/fail
    
    section_leaderL1 = Agent(
        name="SectionLeaderL1",
        tools=[createSectionL0, createObject],
        instructions="""You are an architect of a scene, you design a (section of a) scene by either creating objects, or by (recursively) assigning a 'section leader' (like yourself) to a sub-section of the scene which is restricted to a region. If you do use createObject, reference only one object per call, since some downstream agent needs to take your description and find the right asset.""" + RESTRICTIONS,
        model=MODEL
    )
    
    prompt = {"Description of your section": prompt, "Region to work in": "completely open - scene origin is at (0,0,0)"}
    
    await Runner.run(section_leaderL1, json.dumps(prompt))
    
    unity.done_and_write()
    
async def test_lab(prompt="A laboratory"):
    global unity
    unity = UnityFile("test_laboratory" + str(random.randint(100, 999)))
    await createSkyboxLeader(prompt) # success/fail
    
    section_leaderL1 = Agent(
        name="SectionLeaderL1",
        tools=[createSectionL0, createObject],
        instructions="""You are an architect of a scene, you design a (section of a) scene by either creating objects, or by (recursively) assigning a 'section leader' (like yourself) to a sub-section of the scene which is restricted to a region. If you do use createObject, reference only one object per call, since some downstream agent needs to take your description and find the right asset.""" + RESTRICTIONS,
        model=MODEL
    )
    
    prompt = {"Description of your section": prompt, "Region to work in": "completely open - scene origin is at (0,0,0)"}
    
    await Runner.run(section_leaderL1, json.dumps(prompt))
    
    unity.done_and_write()
 
async def test_river(prompt="A river with two opposing banks"):
    global unity
    unity = UnityFile("test_river" + str(random.randint(100, 999)))
    

    
    section_leader0_w_groundleader = Agent(
        name="SectionLeaderL0wGroundLeader",
        tools=[createObject, createGround],
        instructions="""You are an architect of a scene. According to the prompt, you design a (section of a) scene by creating objects. Reference one object per call to createObject, since some downstream agent needs to take your description and find the right asset. You should create the ground before any objects are created, so that you can properly arrange objects in the scene. To create the ground, you prompt an agent to generate a heightmap that fits the scene. Make sure to place objects ATOP the ground.""" + RESTRICTIONS + CHEATS,
        model=MODEL
    )
    
    prompt = {"Description of the scene": prompt}
    
    await Runner.run(section_leader0_w_groundleader, json.dumps(prompt))
    
    
    
    unity.done_and_write()

async def test_river_bridge(prompt="A river with two steep opposing banks and a bridge crossing it."):
    global unity
    unity = UnityFile("test_river_bridge" + str(random.randint(100, 999)))
    

    
    section_leader0_w_groundleader = Agent(
        name="SectionLeaderL0wGroundLeader",
        tools=[createObject, createGround],
        instructions="""You are an architect of a scene. According to the prompt, you design a (section of a) scene by creating objects. Reference one object per call to createObject, since some downstream agent needs to take your description and find the right asset. You should create the ground before any objects are created, so that you can properly arrange objects in the scene. To create the ground, you prompt an agent to generate a heightmap that fits the scene. Make sure to place objects ATOP the ground.""" + RESTRICTIONS + CHEATS,
        model=MODEL
    )
    
    prompt = {"Description of the scene": prompt}
    
    await Runner.run(section_leader0_w_groundleader, json.dumps(prompt))
    
    unity.done_and_write()
    
async def test_river_bridge_L1(prompt="A river with two steep opposing banks and a bridge crossing it, in a forest."):
    global unity
    unity = UnityFile("test_river_bridge_L1" + str(random.randint(100, 999)))
    

    
    section_leader0_w_groundleader = Agent(
        name="SectionLeaderL0wGroundLeader",
        tools=[createObject, createSectionL0, createGround],
        instructions="""You are an architect of a scene. According to the prompt, you design a (section of a) scene by creating objects. Reference one object per call to createObject, since some downstream agent needs to take your description and find the right asset. You should create the ground before any objects are created, so that you can properly arrange objects in the scene. To create the ground, you prompt an agent to generate a heightmap that fits the scene. Make sure to place objects ATOP the ground.""" + RESTRICTIONS + CHEATS,
        model=MODEL
    )
    
    prompt = {"Description of the scene": prompt}
    
    await Runner.run(section_leader0_w_groundleader, json.dumps(prompt))
    
    unity.done_and_write()
   

test_dispatcher = {
    # = deprecated test
    "test_leaves": test_leaves,
    "test_stem": test_stem,
    "test_skybox": test_skybox,
    "test_stem_and_sky": test_stem_and_sky,
    "test_L1": test_L1,
    #"test_bridge_L1": test_bridge_L1,
    "test_lab": test_lab,
    "test_ground": test_ground,
    "test_river": test_river,
    "test_create_ground": test_create_ground,
    "test_river_bridge": test_river_bridge,
    "test_river_bridge_L1": test_river_bridge_L1,
}

import sys
if __name__ == "__main__":
    prompt = "A forest"
    if sys.argv[1]:
        asyncio.run(test_dispatcher[sys.argv[1]]())
    else:
        asyncio.run(main(prompt))


















