
import os
import sys
import time
import json
from dataclasses import dataclass
from pathlib import Path
from agents import Runner
from pydantic import BaseModel
from utils.paths import AssetsRelativePathStr, RelativePath
from llms.subagents import ObjectPlanner, GroundCreator, SkyboxPlanner, TexturePlanner, SunPlanner, SoundDesigner
from generating.world import World, UnityWorld
from logger import log
import tools.unity.surface_construction as surface_construction
import tools.unity.procedural as procedural
from typing import List

from tools.wrapped_utils import error_reporter

#from tools.unity.subtool_imports import getGroundMatrix, proposeObject, positionObject, positionVRHumanPlayer, createSkybox, createGround, getContactPoints, createSun, populateHorizon, createSound, create50mx50mGround


asset_catalog: dict[str, dict]
synopses: dict[str, str] # synopsis: relative_path
skybox_material_leaves: List[str]
ground_material_leaves: List[str]
sound_leaves: List[str]
assets: Path # path to Assets/ in Unity
world: World | UnityWorld






USE_SHAP_E = bool((os.getenv("SHAP_E") or "").strip() or "")
if USE_SHAP_E:
    print("Importing Shap-E")
    from shap_e import shap_e_test
else:
    print("\n[Unity core] Not using shap-e. (Normal)\n")




@error_reporter
def position_vr_player(transform: str, rotation: str, explanation: str):
    try:
        json_location = json.loads(transform)
    except ValueError:
        print("Error loading given placement_of_centerpoint into JSON")
        return f"Failed to add player to location {transform} in the scene (json.loads() error). Make sure to pass a correct something that can be loaded with json.loads() into JSON."
    try:
        json_rotation = json.loads(rotation)
    except ValueError:
        print("Error loading given rotation into JSON")
        return f"Failed to add object player to rotation {rotation} in the scene (json.loads() error) Make sure to pass a correct something that can be loaded with json.loads() into JSON."
    
    global world
    log(f"Positioning VR experience at {transform} with rotation {rotation}")
    log(explanation)
    buildID = world.set_vr_player(json_location, json_rotation)
    data = {
            "Player": {
                "Position": f"{json_location}",
                "Rotation": f"{json_rotation}",
            }
        }
    
    if buildID:
        data["buildID"] = buildID
    world.add_data(data)

@error_reporter
def position_agent(name: str, transform: str, rotation: str):
    try:
        json_location = json.loads(transform)
    except ValueError:
        print("Error loading given transform into JSON")
        return f"Failed to add agent to location {transform} in the scene (json.loads() error). Make sure to pass a correct something that can be loaded with json.loads() into JSON."
    try:
        json_rotation = json.loads(rotation)
    except ValueError:
        print("Error loading given rotation into JSON")
        return f"Failed to add agent to rotation {rotation} in the scene (json.loads() error) Make sure to pass a correct something that can be loaded with json.loads() into JSON."
    
    global world
    log(f"Positioning agent at {transform} with rotation {rotation}")
    buildID = world.set_agent(name, json_location, json_rotation)
    data = {
            "Agent": {
                "Position": f"{json_location}",
                "Rotation": f"{json_rotation}",
            }
        }
    
    if buildID:
        data["buildID"] = buildID
    world.add_data(data)
    return f"Successfully added agent to the scene at {transform}. Make sure I'm supplied with destinations."

@error_reporter
def delete(buildID: str):
    # delete from world model and # delete from build instructions
    global world
    try:
        # Is list?
        buildIDs = json.loads(buildID)
        for buildID in buildIDs:
            world.delete_object_by_buildID(buildID)
    except Exception:
        # Not a list...
        world.delete_object_by_buildID(buildID)
    


@error_reporter
def get_contact_points():
    global world
    log("Getting contact points...")
    print("...end contact points")
    return json.dumps(world.contact_points)

@error_reporter
def get_ground_matrix():
    global world
    print("Recalling ground matrix...")
    log("Recalling ground heightmap...")
    return {"Grid": world.ground_matrix, "Information": "The ground goes from (0,0) to (-50, 50). That is, the top left of the matrix is -50, 50. All objects should be on over the ground."}   

@error_reporter
def position_sun(length_of_day: float, time_of_day: float, sun_brightness: float):
    global world
    log("Positioning the sun in the sky...")
    
    buildID = world.add_sun(length_of_day, time_of_day, sun_brightness)
    

    data = {
            "World place in solar system": {
                "time of day": f"{time_of_day} Earth-hours",
                "length of day": f"{length_of_day} Earth-hours",
                "sun brightness": f"{sun_brightness} luminosity"
            }
        }
    if buildID:
        data["buildID"] = buildID
    world.add_data(data)
    return f"Successfully added the Sun"

@error_reporter
async def create_skybox(skybox_description: str):
    global world

    log("Creating skybox...")
    agent = SkyboxPlanner()
    prompt = {"Object description": skybox_description,
                "Available assets": skybox_material_leaves}
    t = time.time()
    log(f"{agent.name} started creating skybox")
    result = await Runner.run(agent, json.dumps(prompt))
    log(f"{agent.name}: {time.time() - t} seconds")
    path_str = result.final_output.path
    skybox_name = path_str.split("/")[-1]
    print(f"Proposing relative path with Path {Path(path_str)} from {path_str}")
    world.propose_object(skybox_name, RelativePath(path=Path(path_str)))
    buildID = world.add_skybox(skybox_name)
    
    data = {
            "Skybox/atmosphere": {
                "name of skybox": skybox_name
            }
        }
    if buildID:
        data["buildID"] = buildID
    world.add_data(data)
    return f"Successfully added '{skybox_name}' to the scene."

@error_reporter
async def create_sound(sound_description: str):
    global world

    agent = SoundDesigner()
    prompt = prompt = {"Object description": sound_leaves,
                "Available assets": sound_leaves}
    t = time.time()
    log(f"{agent.name} starting on {sound_description}")
    result = await Runner.run(agent, json.dumps(prompt))
    log(f"{agent.name} thought for {time.time() - t} seconds.")
    path_str = result.final_output.path
    sound_name = path_str.split("/")[-1]
    if sound_name == "":
        return f"Unsuccessful adding sound."
    world.propose_object(sound_name, RelativePath(path=Path(path_str)))
    buildID = world.add_sound(sound_name)
    
    
    data = {
            "Sound": {
                "When?": "On start of scene",
                "Where?": "Master sound channel",
                "Name": sound_name,
                "type": f"digitally encoded as a {sound_name.split(".")[-1]}"
            }
        }
    if buildID:
        data["buildID"] = buildID
    world.add_data(data)
    return f"Successfully added '{sound_name}' to the scene."

@error_reporter
async def create_sun(description_of_sun_behavior: str) -> str:
    global world
    log("Creating sun...")
    from tools.tools import positionSun
    agent = SunPlanner(tools=[positionSun])
    prompt = {"Description of desired sun behavior": description_of_sun_behavior}

    t = time.time()
    log(f"{agent.name} started")
    await Runner.run(agent, json.dumps(prompt))
    log(f"{agent.name}: {time.time() - t} seconds")    
    return f"Successfully placed the Sun in the scene"

@error_reporter
async def create_ground(steps_to_ground_construction, resolution, scale, procedural):
    global world
    from tools.tools import addTexture
    agent = GroundCreator(tools=[addTexture], set_perimeter_to_0=True, resolution=resolution, scale=scale)
    prompt = {"Steps to plan": steps_to_ground_construction, "Resolution": resolution, "Scale": scale}
    
    if len(world.ground_matrix) > 0:
        prompt["Existing ground to edit"] = world.ground_matrix
        prompt["Existing ground scale"] = world.ground_scale
        prompt["Existing texture"] = world.current_texture
    t = time.time()
    log(f"{agent.name} starting to create ground.")
    result = await Runner.run(agent, json.dumps(prompt))
    log(f"{agent.name} finished in {time.time() - t} seconds.")
    
    grid:str = result.final_output.grid
    if procedural:
        object_path, ground_matrix = surface_construction.obj_from_grid_procedural(assets / "Assets" / "Manifest", grid, scale)
    else:
        object_path, ground_matrix = surface_construction.obj_from_grid(assets / "Assets" / "Manifest", grid, scale)
    log(f"Ground OBJ written to {object_path}.")
    try:
        assert len(ground_matrix[0]) == len(ground_matrix)
        
    except AssertionError:
        log(f"Oops! Ground matrix was not square but {len(ground_matrix[0])} by {len(ground_matrix)}. Retrying...")
        raise AssertionError(f"Ground matrix is not `square but {len(ground_matrix[0])} by {len(ground_matrix)}. Try a smaller resolution to increase performance.")
    ground_name = object_path.name
    world.ground_matrix = ground_matrix
    world.ground_scale = scale

    texture_path_str:str = result.final_output.texture_path_str
    explanation = result.final_output.explanation_of_heights
    world.current_texture = texture_path_str
        
    name, asset = world.propose_object(ground_name, {"Ground": RelativePath(object_path), "Texture": RelativePath(Path(texture_path_str))})
    log(f"Proposed object {name} as {asset}")
    
    json_location = {"x": 0, "y": 0, "z": 0}
    log("Adding ground to YAML")
    buildID = world.add_ground(ground_name, json_location)
    log("Back from adding ground to YAML")
    # Add new contact points under ground
    print("Back from adding ground to scene.")
    world.contact_points["Ground"] = []
    for i in range(len(world.ground_matrix) -1, -1, -1):
        for j in range(0, len(world.ground_matrix[i])):
            contact_point = (j * scale, world.ground_matrix[i][j] + float(json_location["y"]), (resolution*scale - scale) - i*scale)
            world.contact_points["Ground"].append(contact_point)    

    formatted_rows, decimal = [], 1
    for row in world.ground_matrix:
        # Format each number with fixed width and decimal precision
        row_str = ", ".join(f"{val:6.{decimal}f}" for val in row)
        formatted_rows.append(f"  [ {row_str} ]")

    # Join all rows with brackets around the entire matrix
    legible_result = "\n[\n" + ",\n".join(formatted_rows) + "\n]"
    log(explanation)
    
    data = {
            "Name": ground_name,
            "Texture": world.current_texture,
            "Heightmap": ground_matrix,
            "Scale": world.ground_scale,
            "Position": json_location,
            "Orientation": "The ground goes from (0,0) to (-50, 50). That is, the top left of the matrix is -50, 50. All objects should be positioned over the ground." # held constant elsewhere?
        }
    if buildID:
        data["buildID"] = buildID
    world.add_data(data)
    return f"Successfully placed a ground with heightmap {legible_result} in the +X +Z quadrant (these coordinates correspond to the vertices of the ground mesh). The scale of the Xs and Zs is x5. There is no vertical scaling.\n{explanation}"

@error_reporter
def populate_horizon(asset_name_list: str):
    global world
    log("Populating horizon")
    # I'd like to have a random 2D coordinate generator that excludes numbers that fall within the indices of world.ground_matrix * 
    try:
        asset_name_list = json.loads(asset_name_list)
    except:
        print(f"Failed to load json from {asset_name_list}")
        return f"Failed to json.loads({asset_name_list})."
    log(f"Assets to populate horizon with: {asset_name_list}")
    procedural.populate(asset_name_list, world) # adds proposed objects to world randomly up to a limit (camera fov)
    world.add_data({
        "Ground off to infinite": f"Outside the {world.ground_scale}x {world.current_texture} ground, there are randomly placed {asset_name_list}"
    })
    return f"Successfully populated horizon."

@error_reporter
async def add_texture(material_of_object_description: str):
    global world
    log("Adding texture for ground...")
    if len(ground_material_leaves) == 0:
        print("No textures for ground available! Skipping TexturePlanner.")
        return "None"
    agent = TexturePlanner()
    prompt = {"Material description": material_of_object_description,
                "Available assets": ground_material_leaves}
    t = time.time()
    log(f"{agent.name} started")
    result = await Runner.run(agent, json.dumps(prompt))
    log(f"{agent.name}: {time.time() - t} seconds")
    
    mat_path = result.final_output.path
    print("Found", mat_path, "for", material_of_object_description)
    return mat_path


@error_reporter
async def propose_object(description: str):
    if assets is None:
        print("Asset project not set. Needed for linking objects.")
        return f"Somethings wrong. Report to user: 'Asset project not set (is {assets}) Needed for linking objects.'"
    global world
    if USE_SHAP_E:
        object_path = shap_e_test.generate(assets, prompt=description)
        world.propose_object(description, RelativePath(path=Path(object_path)))
        return {"Object":{"Name":description, "Info": "Assume the origin is at the object's center."}}
    from tools.tools import getGroundMatrix
    agent = ObjectPlanner(tools=[getGroundMatrix])
    prompt = {"Description of object": description, "Synopses to choose from": list(synopses.keys())}
    t = time.time()
    log(f"{agent.name} starting to match '{description}'")
    result = await Runner.run(agent, json.dumps(prompt))
    log(f"{agent.name} matched synopsis '{result.final_output.synopsis}' to the description in {time.time() - t} seconds.")
    synopsis: str = result.final_output.synopsis
    try:
        object_path = Path(synopses[synopsis])
        log(f"{synopsis} has path {object_path}")
    except KeyError:
        print(result.final_output, "is not in synopsis file. (Agent problem - the list of synopses were passed to it.)")
        return f"This agent failed to match the description to an object, maybe because the object does not exist in the available assets."
    log(f"Looking up {object_path} in catalog...")
    object_data = asset_lookup(object_path)
    
    if object_data == None:
        raise Exception("We're sorry, no assets could be found to fit that description. Please try again with another slightly different object in mind, or leave the desired object out altogether if it is not crucial to the scene.")
    else:
        print(f"\tGathered info:\n{object_data}")
    log(f"Catalog says {object_path} is {object_data["Name"]}")
    proposed_object_path = assets / object_path
    log(f"Converting path {object_path} to Asset with path {Path(proposed_object_path)}")
    object_name, proposed_asset = world.propose_object(object_data["Name"], RelativePath(path=Path(proposed_object_path)))
    log(f"Proposed object {object_name} as {proposed_asset}")
    json_blob = {
        "Object": object_data,
        "Note": result.final_output.note
    }
    print(f"\tMatcher to conductor: {json_blob["Note"]}")
    return json_blob



@error_reporter
def position_object(object_name: str, position_of_object_origin: str, rotation: str, explanation: str) -> str:
    global world 
    try:
        assert object_name in world.proposed_objects
    except AssertionError:
        print(f"Object {object_name} is not showing up in {world.proposed_objects}")
        return f"The object {object_name} has not been proposed. Please call proposeObject before positionObject and refer to the proposed object in the arguments of positionObject."
    try:
        json_location = json.loads(position_of_object_origin)
    except ValueError:
        print("Error loading given position into JSON")
        return f"Failed to add object '{object_name}' to location {position_of_object_origin} in the scene (json.loads() error). Make sure to pass a correct something that can be loaded with json.loads() into JSON."
    try:
        json_rotation = json.loads(rotation)
    except ValueError:
        print("Error loading given rotation into JSON")
        return f"Failed to add object '{object_name}' to rotation {rotation} in the scene (json.loads() error) Make sure to pass a correct something that can be loaded with json.loads() into JSON."
    log(f"Positioning {object_name}. Arguments: {position_of_object_origin}, {rotation}")
    asset_path = world.get_pathstr_relative_to_assets(object_name, assets) # (logging in there)
    log(f"Is {asset_path} in the assest_catalog?")
    if asset_path in list(asset_catalog.keys()):
        object_data = asset_catalog[asset_path].copy()
    else:
        object_data = {"Name": object_name}
    log(f"Successfully parsed location(s) and rotation(s) for proposed {object_name}")
    log(f"{json_location} {json_rotation}")
    print(f"\tExplanation: {explanation}")
    
    #HEre we check if its a list or a singleton
    objects_to_sequence = []
    if type(json_location) == list:
        if type(json_rotation) == list:
            for i in range(0, len(json_location)):
                objects_to_sequence.append((json_location[i], json_rotation[i])) # a zip
        else:
            return f"If you sequentially place the location/placement of origin, you must pass that amount of rotations too."
    else:
        if type(json_rotation) == list:
            return f"If you sequentially place the rotation, you must pass that amount of locations too."
        else:
            objects_to_sequence = [(json_location, json_rotation)]
         
    failed_placements = [] 
    max_len = len(objects_to_sequence)

    while len(objects_to_sequence) > 0:
        json_location, json_rotation = objects_to_sequence.pop(0)
        print(object_name, "-->", (json_location, json_rotation))
        for parent, contact_points in world.contact_points.items():
            # Popping contact points
            if (json_location["x"], json_location["y"], json_location["z"]) in world.contact_points[parent]:
                print("POPPING contact point", (json_location["x"], json_location["y"], json_location["z"]), "from contact points")
                #world.contact_points[object_name].remove((json_location["x"], json_location["y"], json_location["z"]))
        print("Positioning...........")
        print(asset_path)       
        print("...........") 
        log(f"Positioning {object_name} at {json.dumps(json_location)}")
        if asset_path in list(asset_catalog.keys()):        
            buildID = world.add_prefab(object_name, json_location, json_rotation)
        else:
            log(f"This asset {asset_path} is not in asset_catalog")
            buildID = world.add_orphan_prefab(object_name, json_location, json_rotation)
        object_data["Position"] = json_location
        object_data["Rotation"] = json_rotation
        if buildID:
            object_data["buildID"] = buildID
        world.add_data(object_data)
    if len(failed_placements) == max_len:
        return f"Failed to place one or all of {object_name}. Failed placements:\n{failed_placements}"
    log(f"Positioned {object_name} {max_len - len(failed_placements)} times.")
    if max_len - len(failed_placements) > 1:
        response = f"Added {object_name} objects to the scene. Recall the information of {object_name} at the placed positions."
    else:
        response = f"Added {object_name} to the scene. Recall the information of {object_name} at the placed position."
    return response

@error_reporter
def supply_agent_destinations(destinations: str):
    try:
        destinations_json = json.loads(destinations)
    except ValueError:
        print("Error loading given destinations into JSON")
        return "Error loading given destinations into JSON. Make sure it is loadable with Python json.loads()"
    destination_list = []
    for destination in destinations_json:
        try:
            destination_name = destination["name"]
            destination_desc = destination["desc"]
            transform = destination["tf"]
        except Exception as e:
            print(f"Error unpacking JSON\n{destination}\n\n{destinations_json}")
            return f"ERROR. Make sure to provide, \"name\", \"desc\", and \"tf\" keys."
        buildID = world.add_destination(destination_name, destination_desc, transform)
        data = destination.copy()
        data["buildID"] = buildID
        destination_list.append(data)
    world.add_data({
        "Agent destinations": destination_list
    })
    return "Successfully added agent destinations to world."

@error_reporter
def position_stage_points(position_of_object_origin: str, rotation: str, explanation: str) -> str:
    global world 
    try:
        json_location = json.loads(position_of_object_origin)
    except ValueError:
        print("Error loading given position into JSON")
        return f"Failed to add object to location {position_of_object_origin} in the scene (json.loads() error). Make sure to pass a correct something that can be loaded with json.loads() into JSON."
    try:
        json_rotation = json.loads(rotation)
    except ValueError:
        print("Error loading given rotation into JSON")
        return f"Failed to add object to rotation {rotation} in the scene (json.loads() error) Make sure to pass a correct something that can be loaded with json.loads() into JSON."
    log(f"Stage points: {json_location} {json_rotation}")
    print(f"\tExplanation: {explanation}")
    
    #HEre we check if its a list or a singleton
    objects_to_sequence = []
    if type(json_location) == list:
        if type(json_rotation) == list:
            for i in range(0, len(json_location)):
                objects_to_sequence.append((json_location[i], json_rotation[i])) # a zip
        else:
            return f"If you sequentially place the location/placement of origin, you must pass that amount of rotations too."
    else:
        if type(json_rotation) == list:
            return f"If you sequentially place the rotation, you must pass that amount of locations too."
        else:
            objects_to_sequence = [(json_location, json_rotation)]
         
    failed_placements = [] 
    max_len = len(objects_to_sequence)

    while len(objects_to_sequence) > 0:
        json_location, json_rotation = objects_to_sequence.pop(0)

        buildID = world.add_stage_point(json_location, json_rotation)
        object_data = {
            "Position": json_location,
            "Rotation": json_rotation
        }
        if buildID:
            object_data["buildID"] = buildID
        world.add_data(object_data)
    return "Successfully provided destinations to agent."
# needs `add_stage_point`

@error_reporter
def position_stage_points(object_name: str, position_of_object_origin: str, rotation: str, explanation: str) -> str:
    try:
        destinations_json = json.loads(destinations)
    except ValueError:
        print("Error loading given destinations into JSON")
        return "Error loading given destinations into JSON. Make sure it is loadable with Python json.loads()"
    destination_list = []
    for destination in destinations_json:
        try:
            destination_name = destination["name"]
            destination_desc = destination["desc"]
            transform = destination["tf"]
        except Exception as e:
            print(f"Error unpacking JSON\n{destination}\n\n{destinations_json}")
            return f"ERROR. Make sure to provide, \"name\", \"desc\", and \"tf\" keys."
        buildID = world.add_destination(destination_name, destination_desc, transform)
        data = destination.copy()
        data["buildID"] = buildID
        destination_list.append(data)
    world.add_data({
        "Agent destinations": destination_list
    })

""" Helpers """
def asset_lookup(path: Path) -> dict:
    
    if path.as_posix() in list(asset_catalog.keys()):
        return asset_catalog[path.as_posix()]
    else:
        global world
        #return {"Name": "unknown_object"+str(random.randint(100, 999)), "Importances": None}
        log(f"Oops! {path.as_posix()} not in {list(asset_catalog.keys())}")
        return None