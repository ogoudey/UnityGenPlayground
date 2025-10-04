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
print(f"\nThe model running is {MODEL}. Use \033[1m\033[36mexport MODEL='<model_name>'\033[0m (Linux) or `setx MODEL '<model-name>'` (Windows) to change it.")

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
async def placeSun(length_of_day: float, time_of_day: float, sun_brightness: float):
    """
        Args:
            length_of_day: It is like the planet rotation - how many hours in a day? In Earth-hours (example 18.0). 
            time_of_day: It is like the scene's position on the planet's latitude. Falls between 0.0 and `length_of_day`.
            sun_brightness: It is like the planet's distance from the sun, or like sun's luminosity, etc. Keep it from 0.0 to 1000.0. (0.01 is Earthlike)
    """
    global unity
    unity.add_sun(length_of_day, time_of_day, sun_brightness)
    return f"Successfully added the Sun"

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
        return f"Successfully added '{skybox_name}' to the scene."
    except Exception:
        print("Error adding skybox...")
        return f"Failed to add '{skybox_name}' to the scene. The name argument must be right."

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
async def planandplaceGround(steps_to_ground_construction: str):
    """ 
        Calls an agent to construct the ground you give a plan for. The agent can only generate a heightmap in the +X, +Z plane. Be somewhat general. It will literally generate an 11x11 grid, scaled up by 5 to be a 50m x 50m topology (you don't need to mention this to them).  It cannot be much more precise than that, and it cannot go outside those bounds. 
        steps_to_ground_construction: a plan of how the ground planner should construct the ground. Example (a string):
            To make a volcano:
                1. Form the mountain
                2. Make the crater in the top.
        Another example involving remaking:
            Make room for a house with a flat 4mx4m base at (5, 2.5, 5)
                1. Since the horizonal scale is 5, turn the 5, 5 into coordinates 1,1. Make this coordinate have height 2.5
                2. Make in the -X, +Z direction the base of the house. 4m / scale of 5 is .8 or 1 grid cell. So make (1, 2), (2, 2), and (2, 1) all height 2.5 too.
                3. Make the points surrounding the indent a sort of gradient. Have them all close to 2.5, and spread that out, without affecting other landmarks. 
                
    This Tool can be called multiple times to reshape the ground, in order to fit the objects that are static or immalleable.
    """

    agent = GroundPlanner(tools=[planTexture])
    global unity
    prompt = {"Steps to plan": steps_to_ground_construction}
    if len(unity.ground_matrix) > 0:
        prompt["Existing ground to edit"] = unity.ground_matrix
    
    t = time.time()
    print(agent.name, "started")
    result = await Runner.run(agent, json.dumps(prompt))
    print(agent.name + ":", time.time() - t, "seconds.")
    

    explanation = result.final_output.explanation_of_heights
    object_asset_path, unity.ground_matrix = obj_from_grid(result.final_output.grid) # writes obj
    print("Ground obj written.")
    texture_path = result.final_output.texture_path
    
    
    ground_name = object_asset_path.split("/")[-1]
        
    unity.yaml.used_assets[ground_name] = {"Ground": object_asset_path, "Texture": texture_path}
    print(ground_name, "added to used_assets w path", object_asset_path)
    
    json_location = {"x": 0, "y": 0, "z": 0}
    unity.add_ground(ground_name, json_location)
    # Add new contact points under ground
    print("Back from adding ground to scene.")
    unity.contact_points[ground_name] = []
    for i in range(0, len(unity.ground_matrix)):
        for j in range(0, len(unity.ground_matrix[i])):
            contact_point = (j *5, unity.ground_matrix[i][j] + float(json_location["y"]), i * 5)
            unity.contact_points[ground_name].append(contact_point)
    
    
    print(unity.ground_matrix)
    print("Attempting reformatting...")
    formatted_rows = []
    for row in unity.ground_matrix[i]:
        print(row)
        print(type(row))
        # Format each number with fixed width and decimal precision
        row_str = ", ".join(f"{val:6.{decimals}f}" for val in row)
        formatted_rows.append(f"  [ {row_str} ]")

    # Join all rows with brackets around the entire matrix
    legible_result = "\n[\n" + ",\n".join(formatted_rows) + "\n]"
    
    
    

    
    return f"Successfully placed a ground with heightmap {legible_result} in the +X +Z quadrant (these coordinates correspond to the vertices of the ground mesh). The scale of the Xs and Zs is x5. There is no vertical scaling.\n{explanation}"

@function_tool
async def planTexture(material_of_object_description: str) -> str:
    """
        Returns the path to a material asset that matches the description. May return "None" if there's no match, in which case use that as the texture_path.
    """
    if len(screened_material_leaves) == 0:
        print("No textures for ground available! Skipping TexturePlanner.")
        return "None"
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
async def planObject(description: str) -> PlaceableObject:
    """ 
        Args:
            description: Some text describing that the object should be like, refering to a singular object that's likely to be selected from a common asset library. For example, "water", "a rock", "a house", etc.
        If you don't get an object you want, its because there's nothing like the desired asset in the library of available assets. In this case, get creative and find a new solution. You don't NEED to place the object returned, which is the object-planner's best guess.
    """

    agent = ObjectPlanner(tools=[get_ground_matrix])
    prompt = {"Description of object": description, "Synopses to choose from": list(synopses.keys())}

    
    t = time.time()
    print(f"{agent.name} started on {description}")
    result = await Runner.run(agent, json.dumps(prompt))
    print(agent.name + ":", time.time() - t, "seconds.")
    
    global unity

    print(f"Matched synopsis '{result.final_output.synopsis}' to description '{description}'")
    try:
        object_asset_path = synopses[result.final_output.synopsis]
    except KeyError:
        print(result.final_output, "is not in synopsis file. (Agent problem - the list of synopses were passed to it.)")
        return f"This agent failed to match the description to an object, maybe because the object does not exist in the available assets."
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
        note_from_planner = result.final_output.note
        object_info["Importances"]["Note"] = note_from_planner
    unity.yaml.used_assets[object_name] = object_asset_path
    print(f"\t{object_name} added to used_assets w path {object_asset_path}")
    return PlaceableObject(object_name, json.dumps(object_info["Importances"]))

@function_tool
async def placeObject(object_name: str, placement_of_object_origin: str, rotation: str, explanation: str) -> str:
    """
        This function permits you to place the PlannedObject in the scene. You may place a single instance of the object or multiple ones, but always refer to the object you've planned. You cannot scale the object. 
        Args:
            object_name: The name of the object you have planned, PlaceableObject.name. (Must match exactly that name.)
            placement_of_object_origin: Must be a JSON-encoded string. OPTIONALLY, can be a list of such strings in order to place a sequence objects or scatter them. Examples:
                "{\"x\": 75, \"y\": 2.8, \"z\": 70}", OR "[{\"x\": 73, \"y\": 10, \"z\": 20}, {\"x\": 50, \"y\": 1.2, \"z\": 72}, ...]"
            rotation: Must be a JSON-encoded string. OPTIONALLY, can be a list of such strings in order to place a sequence objects. Example:
                "{\"x\": 90, \"y\": 0, \"z\": 45}", "[{\"x\": 90, \"y\": 0, \"z\": 45}, {\"x\": 0, \"y\": 0, \"z\": 270}]"
            explanation: A human-readable explanation of the placement(s). Include in your explanation the specific shape of the object, as contained in the PlaceableObject that you've planned. For most placements, its good practice to refer to a contact point from get_contact_points. If the object can't be placed on the ground, edit the ground with planandplaceGround."
    """
    
    print(f"Placing '{object_name}' ---> {placement_of_object_origin} with rotation(s) {rotation}")
    global unity
    try:
        assert object_name in unity.yaml.used_assets
    except AssertionError:
        print(f"Object {object_name} is not showing up in {unity.yaml.used_assets}")
        return f"The object {object_name} has not been planned. Please call planObject before placeObject and refer to the planned object in the arguments of placeObject."
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
    #print(objects_to_sequence)
    while len(objects_to_sequence) > 0:
        json_location, json_rotation = objects_to_sequence.pop(0)
        print(object_name, "-->", (json_location, json_rotation))
        try:
            for parent, contact_points in unity.contact_points.items():
                # Popping contact points
                if (json_location["x"], json_location["y"], json_location["z"]) in unity.contact_points[parent]:
                    print("POPPING contact point", (json_location["x"], json_location["y"], json_location["z"]), "from contact points")
                    #unity.contact_points[object_name].remove((json_location["x"], json_location["y"], json_location["z"]))
                    
                    
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
    response = f"Added object(s) to the scene. Recall the information of {object_name} at the placed point(s)."
    if "Post-placement" in assets_info[unity.yaml.used_assets[object_name]]:
        response += assets_info[unity.yaml.used_assets[object_name]]["Post-placement"]

    return response
    
@function_tool
def place_vr_human_player(transform: str, rotation: str = "{\"x\": 75, \"y\": 10, \"z\": 70}", explanation: str=""):
    """
    This function places the VR headset of the human player in the scene. It places the camera/head, so make it 2m above the ground below them. The player can walk around 1m from where they are placed.
    transform: Must be a JSON-encoded string. Example:
        "{\"x\": 75, \"y\": 10, \"z\": 70}"
    rotation: Must be a JSON-encoded string (only use \" around the variables). Example:
        "{\"x\": 90, \"y\": 0, \"z\": 45}" 
    explanation: A human-readable explanation of the placement(s). Example: "I put the water here to be above the height y=0.5 along the riverbed", or "I put a patch of trees in this section". Be sure to explain the height with regard to the contact points and the open spaces of the heightmap."

    Only call this function once, if successful.
    """
    print(f"Placing human VR player ---> location {transform}, rotation {rotation}")
    print(f"Why this placement?:\n\t{explanation}")

    global unity
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
    print(f"Parsed player's location and rotation into JSON")
    unity.set_vr_player(json_location, json_rotation)
    return f"Successfully added player to the scene at {json_location}."
    
@function_tool
async def get_contact_points() -> str:
    """
        Returns the points in the scene which are available to place objects on.
    """
    global unity
    return json.dumps(unity.contact_points)






    
    
""" Helpers """
def asset_lookup(asset_path: str) -> dict:
    if asset_path in list(assets_info.keys()):
        return assets_info[asset_path]
    else:
        #return {"Name": "unknown_object"+str(random.randint(100, 999)), "Importances": None}
        print(asset_path, "not in", list(assets_info.keys()))
        return None
        raise Exception("Asset is unavailable. Please choose an another asset.")
