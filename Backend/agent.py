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
fbx_tree = assets.get_found(".fbx")
prefab_tree += fbx_tree
material_tree = assets.get_found(".mat")

with open("asset_info.json", "r") as f:
    j = f.read()
    assets_info = json.loads(j)

MODEL="o3-mini"

RESTRICTIONS="""In fact, only describe objects that are commonly found in scenes built in the game engine Unity. IN FACT, ONLY USE THESE ASSETS:\n"""+str(prefab_tree)+"""."""

class UnityFile:
    def __init__(self, name="testingtesting123"):
        self.name = name
        self.yaml = yamling.YAML()

    def add_skybox(self, skybox_name):
        self.yaml.set_skybox(skybox_name)
        
            
    def add_prefab(self, name, location, rotation):
        self.yaml.add_prefab_instance(name, location, rotation)
         
              
    def add_ground(self, ground_name, transform={"x":0.0, "y":0.0, "z":0.0}):
        guid = uuid.uuid4().hex
        yamling.write_obj_meta(self.yaml.used_assets[ground_name], guid)
        self.yaml.add_ground_prefab_instance(guid, transform)
        
        
    def done_and_write(self, file_name=None):
        if not file_name:
            file_name = self.name
        self.yaml.to_unity_yaml(file_name)
        
global unity
global used_assets

class Designation(BaseModel):
    asset_path: str

class GroundData(BaseModel):
    grid: str
    explanation_of_heights: str

class AssetPath(BaseModel):
    asset_path: str

@dataclass
class PlaceableObject():
    name: str
    info: str

CHEATS = """ IN FACT, just to make things absolutely sure, put the water at x=0, z=50. All other objects just go in the -X +Z quadrant OVER the ground, that is, in (x,z)=(0 -> -50, 0 -> 50), ."""


def asset_lookup(asset_path: str) -> dict:
    if asset_path in list(assets_info.keys()):
        return assets_info[asset_path]
    else:
        #return {"Name": "unknown_object"+str(random.randint(100, 999)), "Importances": None}
        print(asset_path, "not in", list(assets_info.keys()))
        return None
        raise Exception("Asset is unavailable. Please choose an another asset.")
        
@function_tool
async def planObject(description: str) -> PlaceableObject:
    """ 
        Args:
            description: Some text describing that the object should be like, refering to a singular object that's likely to be selected from a common asset library. For example, "water", "a rock", "a house", etc.
    """
    
    agent = Agent(
        name="ObjectPlanner" + str(random.randint(100, 999)),
        #instructions="It is your job to prompt an asset-retriever to get the object you are assigned to place. For example, given that you are supposed to put a rock at [1.2, 2.8, -1.5] and this location is 1m high, the object must be extend at least 1m below its center point, otherwise it is floating mid-air."
        instructions= "Retrieve the asset from the list of available assets that best matches the intended description. Then get the info of that object with asset_lookup. If the info further confirms the choice of asset as fitting the description, go ahead and return the info with the path.",
        output_type = AssetPath,
        model=MODEL
    )
    
    
    
    prompt = {"Description of object": description, "Available assets": prefab_tree}
    
    t = time.time()
    print(agent.name, "started.")
    result = await Runner.run(agent, json.dumps(prompt))
    print(agent.name + ":", time.time() - t, "seconds.")
    
    global unity
    object_asset_path = result.final_output.asset_path
    print(f"Looking up {object_asset_path}")
    object_info = asset_lookup(object_asset_path)
    if object_info == None:
        print(f"Cannot find {object_asset_path} in assets_info. Returning None and using random data.")
        object_name = "UnknownObject" + str(random.randint(100,999))
    else:
        object_name = object_info["Name"]
    unity.yaml.used_assets[object_name] = object_asset_path
    print(object_name, "added to used_assets w path", object_asset_path)
    return PlaceableObject(object_name, json.dumps(object_info["Importances"]))

@function_tool
async def placeObject(object_name: str, placement_of_object_origin: str, rotation: str, explanation: str) -> str:
    """
        Args:
            object_name: The name of the object you just created
            placement_of_object_origin: Must be a JSON-encoded string. Example:
                "{\"x\": 75, \"y\": 10, \"z\": 70}"
            rotation: Must be a JSON-encoded string. Example:
                "{\"x\": 90, \"y\": 0, \"z\": 45}"
            explanation: A human-readable explanation of why this placement was chosen. Example: "I put the water here to be above the height y=0.5 along the riverbed."
    """
    print(f"Loading location {placement_of_object_origin} rotation {rotation}")
    print(f"Why this placement? {explanation}")
    try:
        json_location = json.loads(placement_of_object_origin)
    except ValueError:
        print("Error loading given placement_of_centerpoint into JSON")
        return f"Failed to add object '{object_name}' to location {placement_of_object_origin} in the scene (json.loads() error). Make sure to pass a correct something that can be loaded with json.loads() into JSON."
    try:
        json_rotation = json.loads(rotation)
    except ValueError:
        print("Error loading given rotation into JSON")
        return f"Failed to add object '{object_name}' to rotation {rotation} in the scene (json.loads() error) Make sure to pass a correct something that can be loaded with json.loads() into JSON."
    print(f"Parsed location and rotation into JSON for '{object_name}'")
    global unity
    try:
        unity.add_prefab(object_name, json_location, json_rotation)
        return f"Successfully added object to the scene. Recall the information of {object_name}."
    except Exception:
        print("Error adding prefab...")
        return f"Failed to add object '{object_name}' to the scene. The name is arguments are right. Exception:\n" + str(e) 
    
@function_tool
async def createSectionL0(prompt: str, region: str):
    section_leaderl0 = Agent(
        name="SectionLeaderL0wGroundLeader",
        tools=[planObject, planGround],
        instructions="""You are an architect of a scene. According to the prompt, you design a (section of a) scene by creating objects. Reference one object per call to planObject, since some downstream agent needs to take your description and find the right asset. You should create the ground before any objects are created, so that you can properly arrange objects in the scene. To create the ground, you prompt an agent to generate a heightmap that fits the scene. Make sure to place objects ATOP the ground.""" + RESTRICTIONS + CHEATS,
        model=MODEL
    )
    
    prompt = {"Description of the scene": prompt}
    
    await Runner.run(section_leader0_w_groundleader, json.dumps(prompt))
    return f"Successfully allocated generation of this section which has description '{description}'."


@function_tool
async def createSkybox(skybox_description: str) -> Designation:
    agent = Agent(
        name="SkyboxCreator" + str(random.randint(100, 999)),
        output_type = AssetPath,
        instructions="Given the directory structure (asset tree), return the path to the file of the desired asset.",
        model=MODEL
        
    )
    prompt = {"Object description": skybox_description,
                "Available assets": material_tree}

    t = time.time()
    print(agent.name, "started")
    result = await Runner.run(agent, json.dumps(prompt))
    print(agent.name + ":", time.time() - t, "seconds.")
    
    global unity
    
    object_asset_path = result.final_output.asset_path
    
    object_info = {"Name": object_asset_path.split("/")[-1], "Importances": "Nothing to mention"}

    object_name = object_info["Name"]
    

    
    unity.yaml.used_assets[object_name] = object_asset_path

    print(object_name, "added to used_assets w path", object_asset_path)

    return PlaceableObject(object_name, json.dumps(object_info["Importances"]))

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
async def placeSkybox(skybox_name: str) -> str:
    """
        Args:
            skybox_name: The name of the ground you just created
    """

    global unity
    try:
        unity.add_skybox(skybox_name)
    except Exception:
        print("Error adding skybox...")
        return f"Failed to add '{skybox_name}' to the scene. The name argument must be right."

@function_tool
async def placeGround(ground_name: str, placement_of_ground_origin: str, explanation: str) -> str:
    """
        Args:
            ground_name: The name of the ground you just created
            placement_of_ground_origin: Must be a JSON-encoded string. Example:
                "{\"x\": 0, \"y\": 0, \"z\": 0}"
            rotation: Must be a JSON-encoded string. Example:
                "{\"x\": 90, \"y\": 0, \"z\": 45}"
            explanation: A brief human-readable explanation of this placement, include detail on where this object is and what space it covers.
    """
    print(f"Loading placement of centerpoint {placement_of_ground_origin}") 
    print(f"Why this ground placement? {explanation}")
    try:
        json_location = json.loads(placement_of_ground_origin)
    except ValueError:
        print(f"Error loading given location into JSON: {placement_of_ground_origin}")
        return f"Failed to add object '{ground_name}' to location {location} in the scene. Make sure to pass a correct something that can be loaded with json.loads() into JSON."
        
    global unity


    try:
        unity.add_ground(ground_name, json_location)

        return f"Successfully added ground to the scene. Recall the information of {ground_name}: {'all positions are open for further placement. the dimensions are 50m x 50m in the -X, +Z directions.'}."
    except Exception as e:
        print("Error adding ground...", e)
        return f"Failed to add '{ground_name}' to the scene. Make sure the arguments are right."
    

@function_tool
async def planGround(ground_description: str):
    """ 
        ground_description: a description of what the ground should look like.
    """

    agent = Agent(
        name="GroundPlanner",
        instructions="Give me a 11x11 grid of floats, written out directly as rows of numbers, no code, that represents the heightmap of the ground described by the prompt. The length and width are defined by one grid unit times 5. (So the ground is 50m x 50m.) The height is in meters, so a height of 1 is one meter. A human we'll say is 2m. Let the ground be human-scale. In your response, explain the decisions of the heightmap to aid further placement of object on the ground. ",
        output_type=GroundData
    )
    prompt = {"Description of the ground": ground_description}
    
    t = time.time()
    print(agent.name, "started")
    result = await Runner.run(agent, json.dumps(prompt))
    print(agent.name + ":", time.time() - t, "seconds.")
    
    explanation = result.final_output.explanation_of_heights
    object_asset_path, matrix = obj_from_grid(result.final_output.grid) # writes obj
    print("Ground obj written.")
    
    object_info = {"Name": object_asset_path.split("/")[-1], "Importances": {"grid": str(matrix), "open positions": "all positions are open for further placement", "dimensions": "50m x 50m in the -X, +Z directions.", "Notes": "centerpoint is on the +X, -Z corner. " + explanation, "Unplaced!": "Make sure to use placeGround to place this object."},}
    
    global unity

    object_name = object_info["Name"]
     
    
    
    
    unity.yaml.used_assets[object_name] = object_asset_path
    print(object_name, "added to used_assets w path", object_asset_path)
    return PlaceableObject(object_name, json.dumps(object_info["Importances"]))
    


""" Tests """

async def test_skybox(prompt="A blue sky"):
    global unity
    unity = UnityFile("test_blue_sky" + str(random.randint(100, 999)))
    

    
    leader = Agent(
        name="Leader",
        tools=[createSkybox, placeSkybox],
        instructions="You make a Unity world according to the prompt. You are the primary agent in a swarm of LLM-guided agents. It is your job to archestrate the use of tools to generate the scene described by the prompt.",
        model=MODEL
    )
    
    prompt = {"Description of the scene": prompt}
    
    await Runner.run(leader, "We'll start simple:\n" + json.dumps(prompt))
    
    unity.done_and_write()

async def test_ground(prompt="A mountain"):
    global unity
    unity = UnityFile("test_mountain" + str(random.randint(100, 999)))
    

    
    leader = Agent(
        name="Leader",
        tools=[planGround, placeGround],
        instructions="You make a Unity world according to the prompt. You are the primary agent in a swarm of LLM-guided agents. It is your job to archestrate the use of tools to generate the scene described by the prompt.",
        model=MODEL
    )
    
    prompt = {"Description of the scene": prompt}
    
    await Runner.run(leader, "We'll start simple, with just generating the ground:\n" + json.dumps(prompt))
    
    unity.done_and_write()

async def test_river(prompt="A river"):
    global unity
    unity = UnityFile("test_river" + str(random.randint(100, 999)))
    
    leader = Agent(
        name="Leader",
        tools=[planGround, placeGround, planObject, placeObject],
        instructions="You make a Unity world according to the prompt. You are the primary agent in a swarm of LLM-guided agents. It is your job to archestrate the use of tools to generate the scene described by the prompt.\n\
        You are the architect of the scene. According to the prompt, you design the scene by creating objects. Reference one object per call to planObject, since some downstream agent needs to take your description and find the right asset. You should create the ground before any objects are created, so that you can properly arrange objects in the scene. To create the ground, you prompt an agent to generate a heightmap that fits the scene. Make sure to place objects ATOP the ground. Make sure to PLACE every object right after you CREATE it. That is (1) create the object/ground/etc (2) place the object/ground/etc, before moving on to the next thing.",
        model=MODEL
    )
    
    prompt = {"Description of the scene": prompt}
    
    await Runner.run(leader, json.dumps(prompt))
    
    unity.done_and_write()

async def test_river_bridge(prompt="A river cutting through a terrain, and a bridge going over it."):
    global unity
    unity = UnityFile("test_river_bridge" + str(random.randint(100, 999)))
    
    leader = Agent(
        name="Leader",
        tools=[planGround, placeGround, planObject, placeObject],
        instructions="You make a Unity world according to the prompt. You are the primary agent in a swarm of LLM-guided agents. It is your job to archestrate the use of tools to generate the scene described by the prompt.\n\
        You are the architect of the scene. According to the prompt, you design the scene by creating objects. Reference one object per call to planObject, since some downstream agent needs to take your description and find the right asset. You should create the ground before any objects are created, so that you can properly arrange objects in the scene. To create the ground, you prompt an agent to generate a heightmap that fits the scene. Make sure to place objects ATOP the ground. Make sure to PLACE all the object you CREATE.",
        model=MODEL
    )
    
    prompt = {"Description of the scene": prompt}
    
    await Runner.run(leader, json.dumps(prompt))
    
    unity.done_and_write()


test_dispatcher = {
    # = deprecated test


    "test_skybox": test_skybox,


    #"test_bridge_L1": test_bridge_L1,

    "test_ground": test_ground,
    "test_river": test_river,
    "test_river_bridge": test_river_bridge,


}

import sys
if __name__ == "__main__":
    prompt = "A forest"
    if sys.argv[1]:
        try:
            test_function = test_dispatcher[sys.argv[1]]
        except KeyError("Invalid test name. Choose from: " + str(test_dispatcher)):
            test_function = input("Choice:\n")
            test_function = test_dispatcher[test_function]
        asyncio.run(test_function())
        
    else:
        asyncio.run(main(prompt))


















