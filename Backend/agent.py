import sys
import os
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
prefab_leaves = assets.get_found(".prefab")
fbx_tree = assets.get_found(".fbx")
material_leaves = assets.get_found(".mat")



with open("asset_info.json", "r") as f:
    j = f.read()
    assets_info = json.loads(j)
print(f"\nAsset info sheet loaded with {len(assets_info)} entries")

with open("synopsis_file.json", "r") as s:
    v = s.read()
    synopses = json.loads(v)
print(f"\nSynopsis file loaded with {len(synopses)} entries")

async def update_synopsis_file():
    i = 1
    updates_needed = len(assets_info) - len(synopses)
    for asset_path, asset_info in assets_info.items():
        found = False
        for synopsis, ante_asset_path in synopses.items():
            if ante_asset_path == asset_path:
                found = True
                break # on to next asset
        if found == True:
            continue
        else:
            print(asset_path, "not found in synopses...")
            print(f"Generating synopsis... {i}/{updates_needed}")
            i += 1
            new_synopsis = await generate_synopsis(asset_info)
            synopses[new_synopsis] = asset_path
            print(asset_info)
            print("------>", new_synopsis)
    print("Synopsis file up to date.")
    if updates_needed > 0:
        with open("synopsis_file.json", "w") as s:
            output_str = json.dumps(synopses, indent=2)
            s.write(output_str)
            print("Synopsis file updated.")


    



async def generate_synopsis(asset_info):
    synopsis_generator = Agent(
        name="SynopsisGenerator",
        instructions = "Give a brief description of the asset, given supplied info. Context: You are describing a .prefab asset for a Unity world. Later these synopses will be used to assist retrieval of the asset based on a new desired description. For example, later, something like 'a small rock with moss' will be passed to an agent who then looks at synopses like the one you are generating and returns the corresponding asset info. So keep it brief. Put your answer as a 'noun phrase' - no 'this object is...' but rather 'a rock with such and such...'",
        model=MODEL
    )
    prompt = {"Asset info": asset_info}
    result = await Runner.run(synopsis_generator, json.dumps(prompt))
    return result.final_output

MODEL="o3-mini"

RESTRICTIONS="""In fact, only describe objects that are commonly found in scenes built in the game engine Unity. IN FACT, ONLY USE THESE ASSETS:\n"""+str(prefab_leaves)+"""."""



class UnityFile:
    def __init__(self, name="testingtesting123"):
        self.name = name
        self.yaml = yamling.YAML()
        
        self.ground_matrix = []
        self.contact_points = dict()

    def add_skybox(self, skybox_name):
        self.yaml.set_skybox(skybox_name)
        
            
    def add_prefab(self, name, location, rotation):
        self.yaml.add_prefab_instance(name, location, rotation)
         
              
    def add_ground(self, ground_name, transform={"x":0.0, "y":0.0, "z":0.0}):
        if unity.yaml.remove_prefab_instance_if_exists(ground_name):
            print(ground_name, "Removed existing ground from YAML")
        guid = uuid.uuid4().hex
        yamling.write_obj_meta(self.yaml.used_assets[ground_name], guid)
        self.yaml.add_ground_prefab_instance(guid, transform)
        
        
    def done_and_write(self, file_name=None):
        if not file_name:
            file_name = self.name
        self.yaml.to_unity_yaml(file_name)
 
@function_tool
async def get_ground_matrix():
    global unity
    print("Recalling ground matrix...")
    return unity.ground_matrix     
        
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
    
class Check(BaseModel):
    #object_name: str
    check_status: bool
    reason: str

CHEATS = """ IN FACT, just to make things absolutely sure, put the water at x=0, z=50. All other objects just go in the -X +Z quadrant OVER the ground, that is, in (x,z)=(0 -> -50, 0 -> 50), ."""



def asset_lookup(asset_path: str) -> dict:
    if asset_path in list(assets_info.keys()):
        return assets_info[asset_path]
    else:
        #return {"Name": "unknown_object"+str(random.randint(100, 999)), "Importances": None}
        print(asset_path, "not in", list(assets_info.keys()))
        return None
        raise Exception("Asset is unavailable. Please choose an another asset.")


planObjectMode = "SYNOPSIS"
#planObjectMode = "PREFAB_LEAVES"

@function_tool
async def planObject(description: str) -> PlaceableObject:
    """ 
        Args:
            description: Some text describing that the object should be like, refering to a singular object that's likely to be selected from a common asset library. For example, "water", "a rock", "a house", etc.
    """
    if planObjectMode == "SYNOPSIS":
        agent = Agent(
            name="ObjectPlanner" + str(random.randint(100, 999)),
            #instructions="It is your job to prompt an asset-retriever to get the object you are assigned to place. For example, given that you are supposed to put a rock at [1.2, 2.8, -1.5] and this location is 1m high, the object must be extend at least 1m below its center point, otherwise it is floating mid-air."
            instructions= "Retrieve the synopsis that best matches the intended description. Return exactly the synopsis.",
            model=MODEL
        )
        prompt = {"Description of object": description, "Synopses to choose from": list(synopses.keys())}
    else:    
        agent = Agent(
            name="ObjectPlanner" + str(random.randint(100, 999)),
            #instructions="It is your job to prompt an asset-retriever to get the object you are assigned to place. For example, given that you are supposed to put a rock at [1.2, 2.8, -1.5] and this location is 1m high, the object must be extend at least 1m below its center point, otherwise it is floating mid-air."
            instructions= "Retrieve the asset from the list of available assets that best matches the intended description. Then get the info of that object with asset_lookup. If the info further confirms the choice of asset as fitting the description, go ahead and return the info with the path.",
            output_type = AssetPath,
            model=MODEL
        )
    
        prompt = {"Description of object": description, "Available assets": prefab_leaves}
    
    t = time.time()
    print(agent.name, "started.")
    result = await Runner.run(agent, json.dumps(prompt))
    print(agent.name + ":", time.time() - t, "seconds.")
    
    global unity
    if planObjectMode == "SYNOPSIS":
        print(f"Matched description '{description}' to '{result.final_output}'")
        try:
            object_asset_path = synopses[result.final_output]
        except KeyError:
            print(result.final_output, "is not in synopsis file")
            
    
    else:
        object_asset_path = result.final_output.asset_path
    print(f"\t----> {object_asset_path}")
    object_info = asset_lookup(object_asset_path)
    print("\tLooking up asset path in info sheet...")
    if object_info == None:
        raise Exception("We're sorry, no assets could be found to fit that description. Please try again with another slightly different object in mind, or leave the desired object out altogether if it is not crucial to the scene.")
        print(f"\t!!! Cannot find {object_asset_path} in assets_info. Returning None and useless information.")
        object_name = "UnknownObject" + str(random.randint(100,999))
        object_info = {"Importances": "Place this object as normal."}
    else:
        print(f"\tFound:\n{object_info}")
        object_name = object_info["Name"]
    unity.yaml.used_assets[object_name] = object_asset_path
    print(f"\t{object_name} added to used_assets w path {object_asset_path}")
    return PlaceableObject(object_name, json.dumps(object_info["Importances"]))

@function_tool
async def placeObject(object_name: str, placement_of_object_origin: str, rotation: str, explanation: str) -> str:
    """
        Args:
            object_name: The name of the object you have planned, PlaceableObject.name. (Must match exactly that name.)
            placement_of_object_origin: Must be a JSON-encoded string. Example:
                "{\"x\": 75, \"y\": 10, \"z\": 70}"
            rotation: Must be a JSON-encoded string. Example:
                "{\"x\": 90, \"y\": 0, \"z\": 45}"
            explanation: A human-readable explanation of why this placement was chosen. Example: "I put the water here to be above the height y=0.5 along the riverbed. Be sure to explain the height with regard to the contact points and the open spaces of the heightmap."
    """
    print(f"Placing '{object_name}' ---> {placement_of_object_origin} with rotation {rotation}")
    global unity
    assert object_name in unity.yaml.used_assets
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
    
    try:
        for parent, contact_points in unity.contact_points.items():
            # Popping contact points
            if (json_location["x"], json_location["y"], json_location["z"]) in unity.contact_points[parent]:
                print("POPPING contact point", (json_location["x"], json_location["y"], json_location["z"]), "from contact points")
                unity.contact_points[object_name].remove((json_location["x"], json_location["y"], json_location["z"]))
                
                
        unity.add_prefab(object_name, json_location, json_rotation)
        return f"Successfully added object to the scene. Recall the information of {object_name}."
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        line_number = exc_tb.tb_lineno
        print(f"Error: {e}")
        print(f"Type: {exc_type}")
        print(f"File: {fname}")
        print(f"Line Number: {line_number}")
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
def place_vr_human_player(transform: str, rotation: str = "{\"x\": 75, \"y\": 10, \"z\": 70}"):
    """
    This function places the human player (who's wearing VR) in the scene. The player can walk around 1m from where they are placed.
    transform: Must be a JSON-encoded string. Example:
        "{\"x\": 75, \"y\": 10, \"z\": 70}"
    rotation: Must be a JSON-encoded string. Example:
        "{\"x\": 90, \"y\": 0, \"z\": 45}"
    """
    print(f"Placing human VR player ---> location {transform}, rotation {rotation}")
    global unity
    try:
        json_location = json.loads(transform)
    except ValueError:
        print("Error loading given placement_of_centerpoint into JSON")
        return f"Failed to add player to location {location} in the scene (json.loads() error). Make sure to pass a correct something that can be loaded with json.loads() into JSON."
    try:
        json_rotation = json.loads(rotation)
    except ValueError:
        print("Error loading given rotation into JSON")
        return f"Failed to add object player to rotation {rotation} in the scene (json.loads() error) Make sure to pass a correct something that can be loaded with json.loads() into JSON."
    print(f"Parsed player's location and rotation into JSON")
    unity.set_vr_player(transform, rotation)
    return f"Successfully added player to the scene at {location}."
    

@function_tool
async def planSkybox(skybox_description: str) -> Designation:
    agent = Agent(
        name="SkyboxCreator" + str(random.randint(100, 999)),
        output_type = AssetPath,
        instructions="Given the directory structure (asset tree), return the path to the file of the desired asset.",
        model=MODEL
    )
    prompt = {"Object description": skybox_description,
                "Available assets": material_leaves}

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

async def planSkyboxLeader(description: str="Plain blue sky"):
    
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
            ground_name: The name of the ground you just planned. That is, PlaceableObject.name
            placement_of_ground_origin: Must be a JSON-encoded string. Example:
                "{\"x\": 0, \"y\": 0, \"z\": 0}"
            rotation: Must be a JSON-encoded string. Example:
                "{\"x\": 90, \"y\": 0, \"z\": 45}"
            explanation: A brief human-readable explanation of this placement, include detail on where this object is and what space it covers.
        Cannot be called twice. Once the ground is placed, it's placed.
    """
    print(f"Loading placement of ground ---> {placement_of_ground_origin}") 
    print(f"Why this ground placement? {explanation}")
    try:
        json_location = json.loads(placement_of_ground_origin)
    except ValueError:
        print(f"Error loading given location into JSON: {placement_of_ground_origin}")
        return f"Failed to add object '{ground_name}' to location {placement_of_ground_origin} in the scene. Make sure to pass a correct something that can be loaded with json.loads() into JSON."
        
    global unity


    try:
        
        unity.add_ground(ground_name, json_location)
        
        # Add new contact points under ground
        unity.contact_points[ground_name] = []
        for i in range(0, len(unity.ground_matrix)):
            for j in range(0, len(unity.ground_matrix[i])):
                contact_point = (i * 5 + float(json_location["x"]), j *5 + float(json_location["y"]), unity.ground_matrix[i][j] + float(json_location["z"]))
                unity.contact_points[ground_name].append(contact_point)
        return f"Successfully added ground to the scene. Recall the information of {ground_name}: {'all positions are open for further placement. the dimensions are 50m x 50m in the -X, +Z directions.'}. In other words, the ground goes from (0,0) to (-50, 50) All objects should be on top of me."
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        line_number = exc_tb.tb_lineno
        print(f"Error: {e}")
        print(f"Type: {exc_type}")
        print(f"File: {fname}")
        print(f"Line Number: {line_number}")
        return f"Failed to add '{ground_name}' to the scene. Make sure the arguments are right."
        
plan_ground_insturctions_v1 = """Give me a 11x11 grid of floats, written out directly as rows of numbers, no code, that represents the heightmap of the ground described by the prompt. The length and width are defined by one grid unit times 5. (So the ground is 50m x 50m.) The height is in meters, so a height of 1 is one meter. A human we'll say is 2m. Let the ground be human-scale. In your response, briefly explain (one sentence) the decisions of the heightmap to aid further placement of object on the ground.
"""    
plan_ground_instructions_v2 = """Return a heightmap for the ground as an 11x11 grid of floats. 
Rules:
- Write the grid directly as 11 rows of 11 numbers each, separated by spaces. Do not add code, JSON, or extra symbols. 
- Each number is the ground height in meters. A height of 0 means flat ground at sea level. 
- The grid covers 50m x 50m (each cell is 5m x 5m). 
- Keep human scale: a human is ~2m tall, so do not make cliffs or holes taller/deeper than 10m unless the prompt requires it. 
- Shape the terrain according to the prompt, and form around the placed objects. 
- After the grid, add one concise sentence explaining the main heightmap features to guide object placement. 

Output format must follow GroundData:
- grid: the 11x11 float grid as plain text. 
- explanation_of_heights: the one-sentence explanation.
"""

@function_tool
async def get_contact_points() -> str:
    """
        Returns the points in the scene which are available to place objects on.
    """
    global unity
    
    return json.dumps(unity.contact_points)

@function_tool
async def planGround(ground_description: str):
    """ 
        ground_description: a description of what the ground should look like.
    Can be called multiple times, to reshape the ground, to fit the object that are static, immalleable.
    """

    agent = Agent(
        name="GroundPlanner",
        instructions=plan_ground_instructions_v2,
        output_type=GroundData
    )
    prompt = {"Description of the ground": ground_description}
    
    t = time.time()
    print(agent.name, "started")
    result = await Runner.run(agent, json.dumps(prompt))
    print(agent.name + ":", time.time() - t, "seconds.")
    
    global unity
    
    explanation = result.final_output.explanation_of_heights
    object_asset_path, unity.ground_matrix = obj_from_grid(result.final_output.grid) # writes obj
    print("Ground obj written.")
    
    object_info = {"Name": object_asset_path.split("/")[-1], "Importances": {"grid": str(unity.ground_matrix), "open contact points": "all positions are open for further placement", "dimensions": "50m x 50m in the -X, +Z directions.", "Local origin": "origin is on the +X, -Z corner." + explanation, "Unplaced!": "Make sure to use placeGround to place this object."},}
    


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
        tools=[planSkybox, placeSkybox],
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

instruction_v1 = "You make a Unity world according to the prompt. You are the primary agent in a swarm of LLM-guided agents. It is your job to orchestrate the use of tools to generate the scene described by the prompt. Reference one object per call to planObject, since some downstream agent needs to take your description and find the right asset. First you PLAN something, then you PLACE. Furthermore, you should place the ground before you place any other objects, so that all the objects are correctly related to the ground. To plan out the ground, you prompt an agent to generate a heightmap that fits the given description of the scene. Make sure to place objects ATOP the ground. The skybox should also loosely match the description. 'Contact points' will be points 3D coordinates that are unobstructed and useful for placing further objects, such as the coordinates atop the ground. They are just supposed to be guides, though not necessary to use."

instruction_v2 = """You are the Leader agent responsible for generating a Unity scene that matches the user prompt. 
You must orchestrate tool usage in the following structured order:

1. SKYBOX: First, call planSkybox once to describe an appropriate skybox, then call placeSkybox to place it. 
2. GROUND: Next, call planGround to design the terrain/heightmap, then call placeGround to place it. This is an initial guess for the terrain of the ground. In further steps, you may call planGround again to fit various "bulky objects".
3. OBJECTS: After the ground is placed, plan each object one by one with planObject. For each planObject call, 
   immediately follow it with a corresponding placeObject call. 
   - Each object must be placed over the ground (atop or aligned with it). 
   - Bridges, rivers, foliage, rocks, or props must all be handled in this way. 
   - Do not plan multiple objects in a single call. 
4. REGROUNDING: Some objects (e.g. a long bridge), may require the ground to have a certain shape to make sense in, forcing you to reconsider the heightmap of the ground. In this case, call planGround again with requires heights mentioned to in a sense "excavate" the existing ground.
5. COMPLETENESS: Ensure that all elements mentioned in the user prompt are represented in the scene. 
   If something is vague (e.g. "foliage"), interpret it reasonably and cover the intent. 

General rules:
- Always PLAN before PLACE.
- Use get_contact_points to get an estimate of exact (x, y, z) coordinates available for placing objects on.
- Use all other tools at least once when appropriate.
- Use planGround/placeGround multiple times if need be.
- Stop once the world clearly reflects the prompt.

Your role is to reliably build a coherent, grounded Unity world from the description."""





checker_instructions_v1 = """
You are responsible for checking the placed assets in a Unity scene. You will be given an object, and the ability to get the ground matrix (which is scaled by x5). Essentially you must ask:
    Given the
        1. Ground heightmap (matrix),
        2. Reference info about the object,
        3. Actual placement of the object in the scene...
    Is the placement good or bad? Well positioned or somehow off - either in the ground or floating, offset or wrong in some other way?
    If there's not enough information to deduce the correctness of placement, be sure to explain that.
    Keep your answer brief and to the point.
"""

reform_instructions_v1 = """
Suppose you have already built a Unity scene. Now it is your job to incorporate the feedback of an agent who has provided feedback on misplaced objects. Place again, more precisely, the objects that are said to be in the wrong location. You can do this with placeObject. Another approach to correct the misplaced objects is to change the ground. Do this by (for example) changing the ground heightmap with planGround, then replace the ground in the scene with placeGround. Some objects (e.g. a long bridge), may require the ground to have a certain shape to make sense in, forcing you to reconsider the heightmap in this manner.
"""

async def test_river_bridge(prompt="A 5m deep river cutting through a terrain with some foliage, and a bridge going over it connecting two banks."):
    global unity
    unity = UnityFile("test_river_bridge" + str(random.randint(100, 999)))
    
    leader = Agent(
        name="Leader",
        tools=[get_contact_points, planSkybox, placeSkybox, planGround, placeGround, planObject, placeObject],
        instructions=instruction_v2,
        model=MODEL
    )
    
    prompt = {"Description of the scene": prompt}
    
    await Runner.run(leader, json.dumps(prompt), max_turns=20)
    
    unity.done_and_write()
    unity.name += "_v2"
    
    print("\n\n__Checking__\nGoing through used assets:", unity.yaml.placed_assets)
    
    checker = Agent(
        name="Checker",
        tools=[get_ground_matrix],
        instructions=checker_instructions_v1,
        output_type=Check,
        model=MODEL
    )
    feedback = {}
    for asset_name, placement in unity.yaml.placed_assets.items():
        
        print("Checking", asset_name, "...")
        if asset_name in list(unity.yaml.used_assets.keys()):
            path = unity.yaml.used_assets[asset_name]
            reference_info = assets_info[path]
        elif "ground" in asset_name:
            reference_info = {"grid": unity.ground_matrix, "other info": "scaled by 5 and covering the -X +Z quadrant. 50m by 50m."}
        else:
            reference_info = None
            print(asset_name, "not in asset info sheet (which is ")
         
        prompt = {"Reference info": reference_info, "Actual placement": placement}
             
        result = await Runner.run(checker, json.dumps(prompt), max_turns=10)
        check_status = result.final_output.check_status
        reason = result.final_output.reason
        if not check_status:
            feedback[asset_name] = reason
    
    
    
    print(feedback)

    reformer = Agent(
        name="Reformer",
        tools=[placeObject, planGround, placeGround],
        instructions=reform_instructions_v1,
        model=MODEL
    )
    
    print(f"Giving feedback on {len(feedback)} objects...")
    prompt = {"Feedback": feedback}
    result = await Runner.run(reformer, json.dumps(prompt), max_turns=10)
    print(f"{result.final_output}")
    
    
    unity.done_and_write()

async def test_river_bridge_vr(prompt="A 5m deep river cutting through a terrain with some foliage, and a bridge going over it connecting two banks. With a VR player to be placed.", instructions=""):
    global unity
    unity = UnityFile("test_river_bridge" + str(random.randint(100, 999)))
    
    leader = Agent(
        name="Leader",
        tools=[get_contact_points, place_vr_human_player, planSkybox, placeSkybox, planGround, placeGround, planObject, placeObject],
        instructions=instruction_v2,
        model=MODEL
    )
    
    prompt = {"Description of the scene": prompt}
    
    await Runner.run(leader, json.dumps(prompt), max_turns=20)
    
    print("\n\n__Checking__\nGoing through used assets:", unity.yaml.placed_assets)
    
    checker = Agent(
        name="Checker",
        tools=[get_ground_matrix],
        instructions=checker_instructions_v1,
        output_type=Check,
        model=MODEL
    )
    
    for asset_name, placement in unity.yaml.placed_assets.items():
        
        print("Checking", asset_name, "...")
        if asset_name in list(unity.yaml.used_assets.keys()):
            path = unity.yaml.used_assets[asset_name]
            reference_info = assets_info[path]
        elif "ground" in asset_name:
            reference_info = {"grid": unity.ground_matrix, "other info": "scaled by 5 and covering the -X +Z quadrant. 50m by 50m."}
        else:
            reference_info = None
            print(asset_name, "not in asset info sheet (which is ")
         
        prompt = {"Reference info": reference_info, "Actual placement": placement}
             
        result = await Runner.run(checker, json.dumps(prompt), max_turns=10)
        check = result.check_status
        result = await Runner.run(checker, json.dumps(prompt), max_turns=10)
        check_status = result.final_output.check_status
        reason = result.final_output.reason
        if not check_status:
            feedback[asset_name] = reason
        
    print(feedback)

    checker = Agent(
        name="Reformer",
        tools=[placeObject],
        instructions=checker_instructions_v1,
        output_type=Check,
        model=MODEL
    )
    
    print(f"Giving feedback on {len(feedback)} objects...")
    prompt = {"Feedback": feedback}
    result = await Runner.run(checker, json.dumps(prompt), max_turns=10)
        
    
    
    unity.done_and_write()

test_dispatcher = {
    # = deprecated test


    "test_skybox": test_skybox,


    #"test_bridge_L1": test_bridge_L1,

    "test_ground": test_ground,
    "test_river": test_river,
    "test_river_bridge": test_river_bridge,
    "test_vr": test_river_bridge_vr,

}

import sys
if __name__ == "__main__":
    asyncio.run(update_synopsis_file())
    
    

    
    if sys.argv[1]:
        try:
            test_function = test_dispatcher[sys.argv[1]]
        except KeyError("Invalid test name. Choose from: " + str(list(test_dispatcher.keys()))):
            sys.exit(1)
        asyncio.run(test_function())
        
    else:
        print("Please include test from:", list(test_dispatcher.keys()))


















