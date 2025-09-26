import os
import sys
import random
import time
import json
from dataclasses import dataclass, asdict

from agents import function_tool, Runner
from pydantic import BaseModel

from subagents import ObjectPlanner, GroundPlanner, SkyboxPlanner, TexturePlanner, SunPlanner

from obj_building import obj_from_grid

import assets
import synopsis_generator

""" Preprocessing """
assets_info = assets.load()
synopses = synopsis_generator.load(assets_info)

material_leaves = assets.get_found(".mat") # for planning the skybox

screened_material_leaves = assets.get_found(file_type=".mat", folder="../Assets/Ground Materials") 

""" End preprocessing """

global unity
global used_assets
    
MODEL = (os.getenv("MODEL") or "o3-mini").strip() or "o3-mini"

@dataclass
class PlaceableObject():
    name: str
    info: str
    
class Designation(BaseModel):
    asset_path: str

@function_tool
async def get_ground_matrix():
    global unity
    print("Recalling ground matrix...")
    return {"Grid": unity.ground_matrix, "Information": "The ground goes from (0,0) to (-50, 50). That is, the top left of the matrix is -50, 50. All objects should be on over the ground."}   

@function_tool
async def planObject(description: str) -> PlaceableObject:
    """ 
        Args:
            description: Some text describing that the object should be like, refering to a singular object that's likely to be selected from a common asset library. For example, "water", "a rock", "a house", etc.
    """

    agent = ObjectPlanner(tools=[get_ground_matrix])
    prompt = {"Description of object": description, "Synopses to choose from": list(synopses.keys())}

    
    t = time.time()
    print(f"{agent.name} started on {description}")
    result = await Runner.run(agent, json.dumps(prompt))
    print(agent.name + ":", time.time() - t, "seconds.")
    
    global unity

    print(f"Matched synopsis '{result.final_output}' to description '{description}'")
    try:
        object_asset_path = synopses[result.final_output]
    except KeyError:
        print(result.final_output, "is not in synopsis file. (Agent problem - the list of synopses were passed to it.)")

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
            placement_of_object_origin: Must be a JSON-encoded string. OPTIONALLY, can be a list of such strings in order to place a sequence objects. Examples:
                "{\"x\": 75, \"y\": 2.8, \"z\": 70}", "[{\"x\": 75, \"y\": 10, \"z\": 70}, {\"x\": 70, \"y\": 1.2, \"z\": 65}, ...]"
            rotation: Must be a JSON-encoded string. OPTIONALLY, can be a list of such strings in order to place a sequence objects. Example:
                "{\"x\": 90, \"y\": 0, \"z\": 45}", "[{\"x\": 90, \"y\": 0, \"z\": 45}, {\"x\": 0, \"y\": 0, \"z\": 270}]"
            explanation: A human-readable explanation of the placement(s). Example: "I put the water here to be above the height y=0.5 along the riverbed", or "I put a patch of trees in this section". Be sure to explain the height with regard to the contact points and the open spaces of the heightmap."
    """
    
    
    print(f"Placing '{object_name}' ---> {placement_of_object_origin} with rotation(s) {rotation}")
    global unity
    assert object_name in unity.yaml.used_assets
    print(f"Why this placement?:\n\t{explanation}")
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
    
    #HEre we check if its a list or a singleton
    objects_to_sequence = []
    if type(json_location) == list:
        if type(json_rotation) == list:
            objects_to_sequence.append((json_location, json_rotation))
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
        try:
            for parent, contact_points in unity.contact_points.items():
                # Popping contact points
                if (json_location["x"], json_location["y"], json_location["z"]) in unity.contact_points[parent]:
                    print("POPPING contact point", (json_location["x"], json_location["y"], json_location["z"]), "from contact points")
                    unity.contact_points[object_name].remove((json_location["x"], json_location["y"], json_location["z"]))
                    
                    
            unity.add_prefab(object_name, json_location, json_rotation)

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            line_number = exc_tb.tb_lineno
            print(f"Error: {e}")
            print(f"Type: {exc_type}")
            print(f"File: {fname}")
            print(f"Line Number: {line_number}")
            failed_placements.append((json_location, json_rotation))
    if len(failed_placements) == max_len:
        return f"Failed to place one or all of {object_name}. Failed placements:\n{failed_placements}"
    return f"Successfully added object to the scene. Recall the information of {object_name}."
    
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
    agent = SkyboxPlanner()
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
        print("Back from adding ground to scene.")
        unity.contact_points[ground_name] = []
        for i in range(0, len(unity.ground_matrix)):
            for j in range(0, len(unity.ground_matrix[i])):
                contact_point = (i * 5 + float(json_location["x"]), j *5 + float(json_location["y"]), unity.ground_matrix[i][j] + float(json_location["z"]))
                unity.contact_points[ground_name].append(contact_point)
        return f"Successfully added ground to the scene. Recall the information of {ground_name}: {'all positions are open for further placement. the dimensions are 50m x 50m in the -X, +Z directions.'}. In other words, the ground goes from (0,0) to (-50, 50) with these heights:\n{unity.ground_matrix}. That is, the top left of the matrix is -50, 50. All objects should be atop the ground."
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        line_number = exc_tb.tb_lineno
        print(f"Error: {e}")
        print(f"Type: {exc_type}")
        print(f"File: {fname}")
        print(f"Line Number: {line_number}")
        return f"Failed to add '{ground_name}' to the scene. Make sure the arguments are right."

@function_tool
async def get_contact_points() -> str:
    """
        Returns the points in the scene which are available to place objects on.
    """
    global unity
    return json.dumps(unity.contact_points)

@function_tool
async def placeSun(length_of_day: float, percentage_daylight: float, time_of_day: float, sun_brightness: float):
    """
        Args:
            length_of_day: It is like the planet rotation - how many hours in a day? In Earth-hours (example 18.0). 
            percentage_daylight: It is like the scene's position on planet's longitude. From 0.0 to 100.0.
            time_of_day: It is like the scene's position on the planet's latitude. Falls between 0.0 and `length_of_day`.
            sun_brightness: It is like the planet's distance from the sun, or like sun's luminosity, etc. Keep it from 0.0 to 10.0.
    """
    global unity
    unity.add_sun(length_of_day, percentage_daylight, time_of_day, sun_brightness)
    return f"Successfully added the Sun"

@function_tool
async def planandplaceSun(description_of_sun_behavior: str) -> str:
    """
        Plan and place the Sun in the scene. Call this once and only once for each scene. Just describe the Sun and its thematic context briefly. You are effectively prompting another sub-agent to actually deal with positioning the Sun.
    """
    agent = SunPlanner(tools=[placeSun])
    prompt = {"Description of desired sun behavior": description_of_sun_behavior}

    t = time.time()
    print(agent.name, "started")
    await Runner.run(agent, json.dumps(prompt))
    print(agent.name + ":", time.time() - t, "seconds.")

    
    # No PlaceableObject. Consider it placed.
    return f"Successfully placed the Sun in the scene"
    
@function_tool
async def planTexture(material_of_object_description: str) -> str:
    """
        Returns the path to a material asset that matches the description.
    """
    agent = TexturePlanner()
    prompt = {"Material description": material_of_object_description,
                "Available assets": screened_material_leaves}
    t = time.time()
    print(agent.name, "started")
    result = await Runner.run(agent, json.dumps(prompt))
    print(agent.name + ":", time.time() - t, "seconds.")
    
    global unity
    mat_asset_path = result.final_output.asset_path
    print("Found", mat_asset_path, "for", material_of_object_description)
    return mat_asset_path

@function_tool
async def planGround(ground_description: str):
    """ 
        ground_description: a description of what the ground should look like.
    Can be called multiple times, to reshape the ground, to fit the object that are static, immalleable.
    """

    agent = GroundPlanner(tools=[get_ground_matrix, planTexture])
    prompt = {"Description of the ground": ground_description}
    t = time.time()
    print(agent.name, "started")
    result = await Runner.run(agent, json.dumps(prompt))
    print(agent.name + ":", time.time() - t, "seconds.")
    
    global unity
    explanation = result.final_output.explanation_of_heights
    object_asset_path, unity.ground_matrix = obj_from_grid(result.final_output.grid) # writes obj
    print("Ground obj written.")
    texture_path = result.final_output.texture_path
    
    
    object_info = {"Name": object_asset_path.split("/")[-1], "Importances": {"grid": str(unity.ground_matrix), "open contact points": "all positions are open for further placement", "dimensions": "50m x 50m in the -X, +Z directions.", "Local origin": "origin is on the +X, -Z corner." + explanation, "Unplaced!": "Make sure to use placeGround to place this object."},}
    
    object_name = object_info["Name"]
    
    unity.yaml.used_assets[object_name] = {"Ground": object_asset_path, "Texture": texture_path}
    print(object_name, "added to used_assets w path", object_asset_path)
    return PlaceableObject(object_name, json.dumps(object_info["Importances"]))
    
    
""" Helpers """
def asset_lookup(asset_path: str) -> dict:
    if asset_path in list(assets_info.keys()):
        return assets_info[asset_path]
    else:
        #return {"Name": "unknown_object"+str(random.randint(100, 999)), "Importances": None}
        print(asset_path, "not in", list(assets_info.keys()))
        return None
        raise Exception("Asset is unavailable. Please choose an another asset.")
