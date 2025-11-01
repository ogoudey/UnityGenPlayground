import os
import sys
import time
import json
from dataclasses import dataclass
from pathlib import Path
from agents import function_tool, Runner
from pydantic import BaseModel
from subagents import AssetsRelativePathStr, RelativePath
from subagents import ObjectPlanner, GroundCreator, SkyboxPlanner, TexturePlanner, SunPlanner, SoundDesigner
from world import World, UnityWorld
from logger import log
import obj_building
import procedural
from typing import List
import functools
import inspect
import sys
import os
import traceback
import asyncio

DRAWING = True

if DRAWING:
    print(f"Drawing for orchestra")

MODEL = (os.getenv("MODEL") or "o3-mini").strip() or "o3-mini"
print(f"\nThe model running is {MODEL}. Use \033[1m\033[36mexport MODEL='<model_name>'\033[0m (Linux) or `setx MODEL '<model-name>'` (Windows) to change it.")

USE_SHAP_E = bool((os.getenv("SHAP_E") or "").strip() or "")
if USE_SHAP_E:
    print("Importing Shap-E")
    from shap_e import shap_e_test
else:
    print("Not using shap-e. (Normal)")

asset_catalog: dict[str, dict] # and so on
synopses: dict[str, str] # synopsis: relative_path
skybox_material_leaves: List[str]
ground_material_leaves: List[str]
sound_leaves: List[str]
asset_project: Path
world: World | UnityWorld
    


### Form of a Tool ###

#@function_tool
#async def toolNameInThisFormat(args: basic_types) -> basic_type:
#    """docstring"""
#    blah blan

#Try making parameters Pydantic Models

### 

def error_reporter(func):
    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                line_number = exc_tb.tb_lineno
                print("=== Exception caught in inner function ===")
                print(f"Function: {func.__name__}")
                print(f"Error: {e}")
                print(f"Type: {exc_type.__name__}")
                print(f"File: {fname}")
                print(f"Line Number: {line_number}")
                traceback.print_exc()
        return async_wrapper
    else:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                line_number = exc_tb.tb_lineno
                print("=== Exception caught in inner function ===")
                print(f"Function: {func.__name__}")
                print(f"Error: {e}")
                print(f"Type: {exc_type.__name__}")
                print(f"File: {fname}")
                print(f"Line Number: {line_number}")
                traceback.print_exc()
        return sync_wrapper

@function_tool
async def getGroundMatrix() -> dict:
    """docstring"""
    return get_ground_matrix()

@error_reporter
def get_ground_matrix():
    global world
    print("Recalling ground matrix...")
    log("Recalling ground heightmap...", world.scene_name)
    return {"Grid": world.ground_matrix, "Information": "The ground goes from (0,0) to (-50, 50). That is, the top left of the matrix is -50, 50. All objects should be on over the ground."}   

@function_tool
async def positionSun(length_of_day: float, time_of_day: float, sun_brightness: float) -> str:
    """
        Args:
            length_of_day: It is like the planet rotation - how many hours in a day? In Earth-hours (example 18.0). 
            time_of_day: It is like the scene's position on the planet's latitude. Falls between 0.0 and `length_of_day`.
            sun_brightness: It is like the planet's distance from the sun, or like sun's luminosity, etc. Keep it from 0.0 to 1000.0. (0.01 is Earthlike)
    """
    return position_sun(length_of_day, time_of_day, sun_brightness)

@error_reporter
def position_sun(length_of_day: float, time_of_day: float, sun_brightness: float):
    global world
    log("Positioning the sun in the sky...", world.scene_name)
    
    world.add_sun(length_of_day, time_of_day, sun_brightness)
    return f"Successfully added the Sun"

@function_tool
async def createSkybox(skybox_description: str) -> str:
    """
    Adds a skybox to the world...
    """
    return await create_skybox(skybox_description)

@error_reporter
async def create_skybox(skybox_description: str):
    global world

    log("Creating skybox...", world.scene_name)
    agent = SkyboxPlanner()
    prompt = {"Object description": skybox_description,
                "Available assets": skybox_material_leaves}
    t = time.time()
    log(f"{agent.name} started creating skybox", world.scene_name)
    result = await Runner.run(agent, json.dumps(prompt))
    print(agent.name + ":", time.time() - t, "seconds.")
    path_str = result.final_output.path
    skybox_name = path_str.split("/")[-1]
    print(f"Proposing relative path with Path {Path(path_str)} from {path_str}")
    world.propose_object(skybox_name, RelativePath(path=Path(path_str)))
    world.add_skybox(skybox_name)
    return f"Successfully added '{skybox_name}' to the scene."

@function_tool
async def createSound(sound_description: str) -> str:
    """
    Creates a sound in the scene that matches your description. (Limited to static wind sounds currently)
    """
    return await create_sound(sound_description)

@error_reporter
async def create_sound(sound_description: str):
    global world

    agent = SoundDesigner()
    prompt = prompt = {"Object description": sound_leaves,
                "Available assets": sound_leaves}
    t = time.time()
    log(f"{agent.name} starting on {sound_description}", world.scene_name)
    result = await Runner.run(agent, json.dumps(prompt))
    log(f"{agent.name} thought for {time.time() - t} seconds.", world.scene_name)
    path_str = result.final_output.path
    sound_name = path_str.split("/")[-1]
    world.propose_object(sound_name, RelativePath(path=Path(path_str)))
    world.add_sound(sound_name)
    return f"Successfully added '{sound_name}' to the scene."

@function_tool
async def createSun(description_of_sun_behavior: str) -> str:
    """
        Plan and place the Sun in the scene. Call this once and only once for each scene. Just describe the Sun and its thematic context briefly. You are effectively prompting another sub-agent to actually deal with positioning the Sun.
    """
    return await create_sun(description_of_sun_behavior)

@error_reporter
async def create_sun(description_of_sun_behavior: str) -> str:
    global world
    log("Creating sun...", world.scene_name)
    agent = SunPlanner(tools=[positionSun])
    prompt = {"Description of desired sun behavior": description_of_sun_behavior}

    t = time.time()
    print(agent.name, "started")
    await Runner.run(agent, json.dumps(prompt))
    print(agent.name + ":", time.time() - t, "seconds.")    
    return f"Successfully placed the Sun in the scene"

@function_tool
async def create50mx50mGround(steps_to_ground_construction: str):
    """ 
        Calls an agent to construct the ground you give a plan for. The agent can only generate a heightmap in the +X, +Z plane. Be general and let the planner get creative. Clarify the requirements of the ground, but don't micromanage. It will literally generate a 26 by 26 grid (the vertices), scaled up by 2.0 to be a 50 meters by 50 meters topology. The perimeter of the grid must be at height 0.
        steps_to_ground_construction: a plan of how the ground creator should construct the ground. (0, 0, 0) is 0m, 0m, 0m. Example (a string):
            To make a volcano:
                1. Form the mountain
                2. Make the crater in the top.
            Another example involving remaking:
            Make room for a house with a flat 4mx4m base at (4, 2.5, 4) - a "remaking ground" call.
                1. Since the horizonal scale is 2.0, turn the 4, 4 into coordinates 2,2. Make this coordinate have height 2.5
                2. Make in the +X, +Z direction the base of the house. 4m / scale of 2.0 is 2.0 or 2 grid cells. So make (2, 2), (4, 4), and (2, 2) all height 2.5 too.
                3. Make the points surrounding the indent a sort of gradient. Have them all close to 2.5, and spread that out, without affecting other landmarks.
                
    This Tool should be called multiple times to reshape the ground in order to fit the objects that are static or immalleable.
    """
    return await create_ground(steps_to_ground_construction, 11, 5.0, procedural=False)

@function_tool
async def createGround(steps_to_ground_construction: str, resolution: int, scale: float):
    """ 
        Calls an agent to construct the ground you give a plan for. The agent can only generate a heightmap in the +X, +Z plane. Be general and let the planner get creative. Clarify the requirements of the ground, but don't micromanage. It will literally generate a <resolution> by <resolution> grid (the vertices), scaled up by <scale> to be a (<resolution> * <scale> - <scale>) meters by (<resolution> * <scale> - <scale>) meters topology. The perimeter of the grid must be at height 0. Finer resolution compromises performance, while scale compromises realism - keep this in mind. The ground must be square - N by N.
        steps_to_ground_construction: a plan of how the ground creator should construct the ground. (0, 0, 0) is 0m, 0m, 0m. Example (a string):
            To make a volcano:
                1. Form the mountain
                2. Make the crater in the top.
            Another example involving remaking:
            Make room for a house with a flat 4mx4m base at (5, 2.5, 5) - a "remaking ground" call.
                1. Since the horizonal scale is 5.0, turn the 5, 5 into coordinates 1,1. Make this coordinate have height 2.5
                2. Make in the -X, +Z direction the base of the house. 4m / scale of 5.0 is .8 or 1 grid cell. So make (1, 2), (2, 2), and (2, 1) all height 2.5 too.
                3. Make the points surrounding the indent a sort of gradient. Have them all close to 2.5, and spread that out, without affecting other landmarks.
        resolution: an integer < 20 that is the number of vertices along one edge of the ground mesh. The ground must be a square. For performance reasons, keep the resolution under 20. (Example: 11)
        scale: a float that is the number of meters between each vertex. (Example: 5.0)
                
    This Tool can be called multiple times to reshape the ground, in order to fit the objects that are static or immalleable.
    """
    return await create_ground(steps_to_ground_construction, resolution, scale, procedural=True)

@error_reporter
async def create_ground(steps_to_ground_construction, resolution, scale, procedural):
    global world

    agent = GroundCreator(tools=[addTexture], set_perimeter_to_0=True, resolution=resolution, scale=scale)
    prompt = {"Steps to plan": steps_to_ground_construction, "Resolution": resolution, "Scale": scale}
    
    if len(world.ground_matrix) > 0:
        prompt["Existing ground to edit"] = world.ground_matrix
        prompt["Existing ground scale"] = world.ground_scale
        prompt["Existing texture"] = world.current_texture
    t = time.time()
    log(f"{agent.name} starting to create ground.", world.scene_name)
    result = await Runner.run(agent, json.dumps(prompt))
    log(f"{agent.name} finished in {time.time() - t} seconds.", world.scene_name)
    
    grid:str = result.final_output.grid
    if procedural:
        object_path, ground_matrix = obj_building.obj_from_grid_procedural(asset_project / "Assets" / "Manifest", grid, scale)
    else:
        object_path, ground_matrix = obj_building.obj_from_grid(asset_project / "Assets" / "Manifest", grid, scale)
    log(f"Ground OBJ written to {object_path}.", world.scene_name)
    try:
        assert len(ground_matrix[0]) == len(ground_matrix)
        
    except AssertionError:
        log(f"Oops! Ground matrix was not square but {len(ground_matrix[0])} by {len(ground_matrix)}. Retrying...", world.scene_name)
        raise AssertionError(f"Ground matrix is not square but {len(ground_matrix[0])} by {len(ground_matrix)}. Try a smaller resolution to increase performance.")
    ground_name = object_path.name
    world.ground_matrix = ground_matrix
    world.ground_scale = scale

    texture_path_str:str = result.final_output.texture_path_str
    explanation = result.final_output.explanation_of_heights
    world.current_texture = texture_path_str
    
    
        
    name, asset = world.propose_object(ground_name, {"Ground": RelativePath(object_path), "Texture": RelativePath(Path(texture_path_str))})
    log(f"Proposed object {name} as {asset}", world.scene_name)

    print(ground_name, "added to proposed_objects w path", object_path.as_posix())
    
    json_location = {"x": 0, "y": 0, "z": 0}
    world.add_ground(ground_name, json_location)
    # Add new contact points under ground
    print("Back from adding ground to scene.")
    world.contact_points["Ground"] = []
    for i in range(len(world.ground_matrix) -1, -1, -1):
        for j in range(0, len(world.ground_matrix[i])):
            contact_point = (j * scale, world.ground_matrix[i][j] + float(json_location["y"]), (resolution*scale - scale) - i*scale)
            world.contact_points["Ground"].append(contact_point)    
    
    print(world.ground_matrix, "\n...end ground_matrix.")

    formatted_rows, decimal = [], 1
    for row in world.ground_matrix:
        # Format each number with fixed width and decimal precision
        row_str = ", ".join(f"{val:6.{decimal}f}" for val in row)
        formatted_rows.append(f"  [ {row_str} ]")

    # Join all rows with brackets around the entire matrix
    legible_result = "\n[\n" + ",\n".join(formatted_rows) + "\n]"
    log(explanation, world.scene_name)
    return f"Successfully placed a ground with heightmap {legible_result} in the +X +Z quadrant (these coordinates correspond to the vertices of the ground mesh). The scale of the Xs and Zs is x5. There is no vertical scaling.\n{explanation}"

@function_tool
def populateHorizon(asset_name_list: str) -> str:
    """
        Beyond the heightmap and region that you've added objects to, there is a background world that extends to the horizon. You are not required to position objects in this zone. Rather, pass a list of objects that you've already proposed to this tool, and some procedure will automatically populate this zone outside of the important region you've designed. Therefore, pass objects that would realistically be 'randomly' generated.
        asset_name_list: A stringified list of proposed object names. Make sure the names match exactly the Name field of a proposed object returned from proposeObject(). Example: "[\"a house\", \"tree 2\", \"Grass1\"]". All objects are scattered according to Perlin Noise.

    """
    return populate_horizon(asset_name_list)

@error_reporter
def populate_horizon(asset_name_list: str):
    global world
    log("Populating horizon", world.scene_name)
    # I'd like to have a random 2D coordinate generator that excludes numbers that fall within the indices of world.ground_matrix * 
    try:
        asset_name_list = json.loads(asset_name_list)
    except:
        print(f"Failed to load json from {asset_name_list}")
        return f"Failed to json.loads({asset_name_list})."
    print("Assets to populate horizon with:", asset_name_list)
    procedural.populate(asset_name_list, world) # adds proposed objects to world randomly up to a limit (camera fov)
    return f"Successfully populated horizon."

@function_tool
async def addTexture(material_of_object_description: str) -> str:
    """
        Returns the path to a material asset that matches the description. May return "None" if there's no match, in which case use that as the texture_path.
    """
    return await add_texture(material_of_object_description)

@error_reporter
async def add_texture(material_of_object_description: str):
    global world
    log("Adding texture for ground...", world.scene_name)
    if len(ground_material_leaves) == 0:
        print("No textures for ground available! Skipping TexturePlanner.")
        return "None"
    agent = TexturePlanner()
    prompt = {"Material description": material_of_object_description,
                "Available assets": ground_material_leaves}
    t = time.time()
    print(agent.name, "started")
    result = await Runner.run(agent, json.dumps(prompt))
    print(agent.name + ":", time.time() - t, "seconds.")
    
    mat_path = result.final_output.path
    print("Found", mat_path, "for", material_of_object_description)
    return mat_path

@function_tool
async def proposeObject(description: str):
    """ 
        Args:
            description: Some text describing that the object should be like, refering to a singular object that's likely to be selected from a common asset library. For example, "water", "a rock", "a house", etc.
        If you don't get an object you want, its because there's nothing like the desired asset in the library of available assets. In this case, get creative and find a new solution. You don't NEED to place the object returned, which is the object-planner's best guess.
        By the way, water is one of the objects.
    """
    return await propose_object(description)

@error_reporter
async def propose_object(description: str):
    if asset_project is None:
        print("Asset project not set. Needed for linking objects.")
        return f"Somethings wrong. Report to user: 'Asset project not set (is {asset_project}) Needed for linking objects.'"
    global world
    if USE_SHAP_E:
        object_path = shap_e_test.generate(asset_project, prompt=description)
        world.propose_object(description, RelativePath(path=Path(object_path)))
        return {"Object":{"Name":description, "Info": "Assume the origin is at the object's center."}}
    agent = ObjectPlanner(tools=[getGroundMatrix])
    prompt = {"Description of object": description, "Synopses to choose from": list(synopses.keys())}
    t = time.time()
    log(f"{agent.name} starting to match '{description}'", world.scene_name)
    result = await Runner.run(agent, json.dumps(prompt))
    log(f"{agent.name} matched synopsis '{result.final_output.synopsis}' to the description in {time.time() - t} seconds.", world.scene_name)
    synopsis: str = result.final_output.synopsis
    try:
        object_path = Path(synopses[synopsis])
        log(f"{synopsis} has path {object_path}", world.scene_name)
    except KeyError:
        print(result.final_output, "is not in synopsis file. (Agent problem - the list of synopses were passed to it.)")
        return f"This agent failed to match the description to an object, maybe because the object does not exist in the available assets."
    log("Looking up {object_path} in catalog...", world.scene_name)
    object_data = asset_lookup(object_path)
    
    if object_data == None:
        raise Exception("We're sorry, no assets could be found to fit that description. Please try again with another slightly different object in mind, or leave the desired object out altogether if it is not crucial to the scene.")
    else:
        print(f"\tGathered info:\n{object_data}")
    log(f"Catalog says {object_path} is {object_data["Name"]}", world.scene_name)
    proposed_object_path = asset_project / object_path
    log(f"Converting path {object_path} to Asset with path {Path(proposed_object_path)}", world.scene_name)
    object_name, proposed_asset = world.propose_object(object_data["Name"], RelativePath(path=Path(proposed_object_path)))
    log(f"Proposed object {object_name} as {proposed_asset}", world.scene_name)
    json_blob = {
        "Object": object_data,
        "Note": result.final_output.note
    }
    log(f"Matcher to conductor: {json_blob["Note"]}", world.scene_name)
    return json_blob

@function_tool
async def positionObject(object_name: str, position_of_object_origin: str, rotation: str, explanation: str) -> str:
    """
        This function permits you to place a proposed object in the scene. You may place a single instance of the object or multiple ones, but always refer to the object you've planned. You cannot scale the object. Pay close attention to how the object will be positioned in the world, given that you are positioning its local origin.
        Args:
            object_name: The name of the object you have proposed. (Must match exactly that name.)
            position_of_object_origin: Must be a JSON-encoded string. OPTIONALLY, can be a list of such strings in order to place a sequence objects or scatter them. Remember, Y is up! Examples:
                "{\"x\": 75, \"y\": 2.8, \"z\": 70}", OR "[{\"x\": 73, \"y\": 10, \"z\": 20}, {\"x\": 50, \"y\": 1.2, \"z\": 72}, ...]"
            rotation: Must be a JSON-encoded string. OPTIONALLY, can be a list of such strings in order to place a sequence objects. Example:
                "{\"x\": 90, \"y\": 0, \"z\": 45}", "[{\"x\": 90, \"y\": 0, \"z\": 45}, {\"x\": 0, \"y\": 0, \"z\": 270}]"
            explanation: A human-readable explanation of the placement(s). Include in your explanation the specific shape of the object, as contained in the PlaceableObject that you've planned. For most placements, its good practice to refer to a contact point from get_contact_points. If the object can't be placed on the ground, edit the ground with planandplaceGround."
    """
    return position_object(object_name, position_of_object_origin, rotation, explanation)

@error_reporter
def position_object(object_name: str, position_of_object_origin: str, rotation: str, explanation: str) -> str:
    global world 
    try:
        assert object_name in world.unity_file.proposed_objects
    except AssertionError:
        print(f"Object {object_name} is not showing up in {world.unity_file.proposed_objects}")
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
    asset_path = world.get_pathstr_relative_to_asset_project(object_name, asset_project) # (logging in there)
    log(f"Is {asset_path} in the assest_catalog?", world.scene_name)
    if asset_path in list(asset_catalog.keys()):
        object_data = asset_catalog[asset_path]
    else:
        object_data = {"Name": object_name}
    log(f"Successfully parsed location(s) and rotation(s) for proposed {object_name}", world.scene_name)
    log(explanation, world.scene_name)
    
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
        if asset_path in list(asset_catalog.keys()):        
            world.add_prefab(object_name, json_location, json_rotation)
        else:
            world.add_orphan_prefab(object_name, json_location, json_rotation)
        object_data["Position"] = json_location
        object_data["Rotation"] = json_rotation
        world.add_data(object_data)
    if len(failed_placements) == max_len:
        return f"Failed to place one or all of {object_name}. Failed placements:\n{failed_placements}"
    log(f"Positioned {object_name} {max_len - len(failed_placements)} times.", world.scene_name)
    if max_len - len(failed_placements) > 1:
        response = f"Added {object_name} objects to the scene. Recall the information of {object_name} at the placed positions."
    else:
        response = f"Added {object_name} to the scene. Recall the information of {object_name} at the placed position."
    return response
    
@function_tool
def positionVRHumanPlayer(transform: str, rotation: str = "{\"x\": 75, \"y\": 10, \"z\": 70}", explanation: str=""):
    """
    This function places the VR headset of the human player in the scene. It places the camera/head, so make it 2m above the ground below them. The player can walk around 1m from where they are placed.
    transform: Must be a JSON-encoded string. Example:
        "{\"x\": 75, \"y\": 10, \"z\": 70}"
    rotation: Must be a JSON-encoded string (only use \" around the variables). All axes at 0 means the player faces dead ahead in the +X direction. Example:
        "{\"x\": 90, \"y\": 0, \"z\": 45}" 
    explanation: A human-readable explanation of the placement(s). Example: "I put the water here to be above the height y=0.5 along the riverbed", or "I put a patch of trees in this section". Be sure to explain the height with regard to the contact points and the open spaces of the heightmap."

    Only call this function once, and remember to be careful not to make them floating. Use what you know about the objects and their positionings.
    """
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
    log(f"Positioning VR experience at {transform} with rotation {rotation}", world.scene_name)
    log(explanation, world.scene_name)
    world.set_vr_player(json_location, json_rotation)
    return f"Successfully added player to the scene at {json_location}."
    
@function_tool
async def getContactPoints() -> str:
    """
        Returns the vertices of the ground. This is mainly useful for recalling whether the ground meets the positioned objects correctly.
    """
    global world
    print(world.contact_points)
    print("...end contact points")
    return json.dumps(world.contact_points)

""" Helpers """
def asset_lookup(path: Path) -> dict:
    
    if path.as_posix() in list(asset_catalog.keys()):
        return asset_catalog[path.as_posix()]
    else:
        global world
        #return {"Name": "unknown_object"+str(random.randint(100, 999)), "Importances": None}
        log(f"Oops! {path.as_posix()} not in {list(asset_catalog.keys())}", world.scene_name)
        return None
    
### Tests ###
if __name__ == "__main__":
    import assets
    from world import UnityWorld
    u = UnityWorld("world")
    world = u
    asset_project = Path("../Resources/Asset Projects/acrophobia_v1")
    asset_catalog = {"Assets/Proxy Games/Stylized Nature Kit Lite/Prefabs/Water/Flat Water.prefab": {"Name": "water1"}}
    synopses = {"some flat water": "Assets/Proxy Games/Stylized Nature Kit Lite/Prefabs/Water/Flat Water.prefab"}
    ground_material_leaves = ["grass"]
    #asyncio.run(propose_object("water"))
    #position_object("water1", json.dumps({"x":0.0, "y":0.0, "z":0.0}), json.dumps({"x":0.0, "y":0.0, "z":0.0}), "because it is")
    asyncio.run(create_ground("Just return a plain", 10, 1.0, False))






