#############################################################################
#
#   Module containing all function tools for LLMs. Each is wrapped in an error reporter for debugging.
# 
#       LLM -> tools -> API
#
#
#
#
#############################################################################




import os
import sys
import time
import json
from dataclasses import dataclass
from pathlib import Path
from agents import function_tool, Runner
from pydantic import BaseModel
from utils.paths import AssetsRelativePathStr, RelativePath
from generating.world import World, UnityScene
from logger import log
import tools.unity.surface_construction as surface_construction
import tools.unity.procedural as procedural
from typing import List
from llms.subagents import ObjectPlanner, GroundCreator, SkyboxPlanner, TexturePlanner, SunPlanner, SoundDesigner
import functools
import inspect
import sys
import os
import traceback
import asyncio

WORLD_CLASS = os.environ.get("WORLD_CLASS", "UNITY")


if WORLD_CLASS == "UNITY":
    from tools.unity import core
    
        

### Form of a Tool ###

#@function_tool
#(async) def toolNameInThisFormat(args: basic_types) -> basic_type:
#    """docstring"""
#    blah blan

#Try making parameters Pydantic Models

### 



@function_tool
async def getGroundMatrix() -> dict:
    """docstring"""
    return core.get_ground_matrix()

@function_tool
async def positionSun(length_of_day: float, time_of_day: float, sun_brightness: float) -> str:
    """
        Args:
            length_of_day: It is like the planet rotation - how many hours in a day? In Earth-hours (example 18.0). 
            time_of_day: It is like the scene's position on the planet's latitude. Falls between 0.0 and `length_of_day`.
            sun_brightness: It is like the planet's distance from the sun, or like sun's luminosity, etc. Keep it from 0.0 to 1000.0. (0.01 is Earthlike)
    """
    return core.position_sun(length_of_day, time_of_day, sun_brightness)

@function_tool
async def createSkybox(skybox_description: str) -> str:
    """
    Adds a skybox to the world...
    """
    return await core.create_skybox(skybox_description)

@function_tool
async def createSound(sound_description: str) -> str:
    """
    Creates a sound in the scene that matches your description. (Limited to static wind sounds currently)
    """
    return await core.create_sound(sound_description)

@function_tool
async def createSun(description_of_sun_behavior: str) -> str:
    """
        Plan and place the Sun in the scene. Call this once and only once for each scene. Just describe the Sun and its thematic context briefly. You are effectively prompting another sub-agent to actually deal with positioning the Sun.
    """
    return await core.create_sun(description_of_sun_behavior)

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
    return await core.create_ground(steps_to_ground_construction, 11, 5.0, procedural=False)

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
    return await core.create_ground(steps_to_ground_construction, resolution, scale, procedural=True)

@function_tool
def populateHorizon(asset_name_list: str) -> str:
    """
        Beyond the heightmap and region that you've added objects to, there is a background world that extends to the horizon. You are not required to position objects in this zone. Rather, pass a list of objects that you've already proposed to this tool, and some procedure will automatically populate this zone outside of the important region you've designed. Therefore, pass objects that would realistically be 'randomly' generated.
        asset_name_list: A stringified list of proposed object names. Make sure the names match exactly the Name field of a proposed object returned from proposeObject(). Example: "[\"a house\", \"tree 2\", \"Grass1\"]". All objects are scattered according to Perlin Noise.

    """
    return core.populate_horizon(asset_name_list)

@function_tool
async def addTexture(material_of_object_description: str) -> str:
    """
        Returns the path to a material asset that matches the description. May return "None" if there's no match, in which case use that as the texture_path.
    """
    return await core.add_texture(material_of_object_description)

@function_tool
async def getContactPoints() -> str:
    """
        Returns the vertices of the ground. This is mainly useful for recalling whether the ground meets the positioned objects correctly.
    """
    return core.get_contact_points()

@function_tool
async def proposeObject(description: str):
    """ 
        Args:
            description: Some text describing what the object should be like, refering to a singular object that's likely to be selected from a common asset library. For example, "water", "a rock", "a house", etc.
        If you don't get an object you want, its because there's nothing like the desired asset in the library of available assets. In this case, get creative and find a new solution. You don't NEED to place the object returned, which is the object-planner's best guess.
        By the way, water is one of the objects, and an artificial agent/robot is NOT (for that use positionAgent)
    """
    return await core.propose_object(description)

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
    return core.position_object(object_name, position_of_object_origin, rotation, explanation)

@function_tool
def positionVRHumanPlayer(transform: str, rotation: str = "{\"x\": 0, \"y\": 0, \"z\": 0}", explanation: str=""):
    """
    This function places the VR headset of the human player in the scene. It places the camera/head, so make it 2m above the ground below them. The player can walk around 1m from where they are placed.
    transform: Must be a JSON-encoded string. Example:
        "{\"x\": 75, \"y\": 10, \"z\": 70}"
    rotation: Must be a JSON-encoded string (only use \" around the variables). All axes at 0 means the player faces dead ahead in the +X direction. Example:
        "{\"x\": 90, \"y\": 0, \"z\": 45}" 
    explanation: A human-readable explanation of the placement(s). Example: "I put the water here to be above the height y=0.5 along the riverbed", or "I put a patch of trees in this section". Be sure to explain the height with regard to the contact points and the open spaces of the heightmap."

    Only call this function once, and remember to be careful not to make them floating. Use what you know about the objects and their positionings.
    """
    core.position_vr_player(transform, rotation, explanation)
    return f"Successfully added player to the scene at {transform}."

@function_tool
def createAgent(name: str, transform: str, rotation: str = "{\"x\": 0, \"y\": 0, \"z\": 0}", explanation: str=""):
    """
    This function places an autonomous path finding agent in the scene. DON'T use propose_object for this.
    name: Any name. (Example: Rob The Robot)
    transform: Must be a JSON-encoded string. Example:
        "{\"x\": 75, \"y\": 10, \"z\": 70}"
    rotation: Must be a JSON-encoded string (only use \" around the variables). All axes at 0 means the player faces dead ahead in the +X direction. Example:
        "{\"x\": 45, \"y\": 0, \"z\": -45}" 

    Only call this function once, and remember to be careful not to make it floating. Use what you know about the objects and their positionings.
    """
    
    return core.position_agent(name, transform, rotation)

@function_tool
def provideDestinationsForAgent(destination_dicts: str):
    """
    Provide (no fewer than 2) destinations for an autonomous path finding agent to navigate to. Provide a stringified (json.load-able) list of dicts with information about each such destination. Be thorough and generous with the allocations, giving the robot opportunities to move all around important parts of the world.
    Don't forget to provide all three categories in each dict in the argument. Must use this to complete an agent.

    transforms: JSON-encoded string representing the destinations. Data should only include name, description (\"desc\"), and transform (\"tf\").
        {\"name\": a label for the destination, \"desc\": a descriptive phrase, \"tf\": {\"x\": float, \"y\": float, \"z\": float}}Examples:
        (for a kitchen): "[{\"name\": \"dishwasher\", \"desc\": \"in front of\"}, \"tf\": {\"x\": 1.28, \"y\": 0.25, \"z\": -4.5}}, {\"name\": \"middle of floor\", \"desc\": \"a good spot to be the center of attention\"}, \"tf\": {\"x\": 1.28, \"y\": 0.25, \"z\": -4.5}}]"
        (for a mountain): "[{\"name\": \"summit\", \"desc\": \"top of the mountain\"}, \"tf\": {\"x\": 25, \"y\": 10, \"z\": 25}}, {\"name\": \"North\", \"desc\": \"North side of the mountain\"}, \"tf\": {\"x\": 0, \"y\": 0.1, \"z\": 120}}]"
    """
    return core.supply_agent_destinations(destination_dicts)

@function_tool
def delete(buildID: str):
    """
    Deletes objects from the scene. Use to make edits to objects (delete then recreate), or simply erase. Use the exact buildIDs found in the existing structures (world model) of the world.
    Pass a list of such buildIDs to delete multiple objects. (Example: "[\"ah1c\", \"23d1\", \"ef63\"]") Try not to use multiple delete() calls where you could use one, passing a list.
    """
    core.delete(buildID)
    return f"Successfully deleted object with buildID {buildID}."

