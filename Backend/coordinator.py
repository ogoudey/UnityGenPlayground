import os
import random

from agents import Agent
from pydantic import BaseModel


import tools
from tools import get_ground_matrix, planObject, placeObject, place_vr_human_player, planSkybox, placeSkybox, placeGround, get_contact_points, planGround, planandplaceSun

MODEL = (os.getenv("MODEL") or "o3-mini").strip() or "o3-mini"
    
class Check(BaseModel):
    #object_name: str
    check_status: bool
    reason: str

class Checker(Agent):
    instructions= """
You are responsible for checking the placed assets in a Unity scene. You will be given an object, and the ability to get the ground matrix (which is scaled by x5). Essentially you must ask:
    Given the
        1. Ground heightmap (matrix),
        2. Reference info about the object,
        3. Actual placement of the object in the scene...
    Is the placement good or bad? Well positioned or somehow off - either in the ground or floating, offset or wrong in some other way?
    If there's not enough information to deduce the correctness of placement, be sure to explain that.
    Keep your answer brief and to the point. 
"""

    def __init__(self, name=None, instructions=None):
        super().__init__(
            name=name or f"Checker{random.randint(100,999)}",
            instructions=instructions or Checker.instructions,
            tools=[get_ground_matrix],
            output_type=Check,
            model=MODEL,
        )

class Coordinator(Agent):    
    instructions_v1= "You make a Unity world according to the prompt. You are the primary agent in a swarm of LLM-guided agents. It is your job to orchestrate the use of tools to generate the scene described by the prompt. Reference one object per call to planObject, since some downstream agent needs to take your description and find the right asset. First you PLAN something, then you PLACE. Furthermore, you should place the ground before you place any other objects, so that all the objects are correctly related to the ground. To plan out the ground, you prompt an agent to generate a heightmap that fits the given description of the scene. Make sure to place objects ATOP the ground. The skybox should also loosely match the description. 'Contact points' will be points 3D coordinates that are unobstructed and useful for placing further objects, such as the coordinates atop the ground. They are just supposed to be guides, though not necessary to use."
    instructions_v2= """You are the Coordinator agent responsible for generating a Unity scene that matches the user prompt. 
You must orchestrate tool usage in the following structured order:

1. SKYBOX: First, call planSkybox once to describe an appropriate skybox, then call placeSkybox to place it. 
2. SUN: Then, call planandplaceSun to describe an appropriate Sun.
3. GROUND: Next, call planGround to design the terrain/heightmap, then call placeGround to place it. This is an initial guess for the terrain of the ground. In further steps, you may call planGround again to fit various "bulky objects".
4. OBJECTS: After the ground is placed, plan each object one by one with planObject. For the planObject call:
   - Do not plan multiple objects in a single call. Do not plan anything like a "cluster" of objects (to do this call the function multiple times). These must be single objects.
   immediately follow it with a corresponding placeObject call. 
   - Do not include placement/location information, only stuff about the size, theme, type, etc.
    For the placeObject call:
   - DO include placement and rotation information (obviously, given the args).
   - Each object must be placed over the ground (atop or aligned with it). 
   - Bridges, rivers, foliage, rocks, or props must all be handled in this way. 

5. REGROUNDING: Some objects (e.g. a long bridge), may require the ground to have a certain shape to make sense in, forcing you to reconsider the heightmap of the ground. In this case, call planGround again with requires heights mentioned to in a sense "excavate" the existing ground.
6. COMPLETENESS: Ensure that all elements mentioned in the user prompt are represented in the scene. 
   If something is vague (e.g. "foliage"), interpret it reasonably and cover the intent. 

General rules:
- Always PLAN before PLACE.
- Use get_contact_points to get an estimate of exact (x, y, z) coordinates available for placing objects on.
- Use all other tools at least once when appropriate.
- Use planGround/placeGround multiple times if need be.
- Stop once the world clearly reflects the prompt.

Your role is to reliably build a coherent, grounded Unity world from the description."""

    def __init__(self, name=None, instructions=None, tools=None):
        super().__init__(
            name=name or f"Coordinator{random.randint(100,999)}",
            instructions=instructions or Coordinator.instructions_v2,
            tools=tools or [get_contact_points, place_vr_human_player, planSkybox, placeSkybox, planGround, placeGround, planObject, placeObject, planandplaceSun],
            model=MODEL,
        )
        

class Reformer(Agent):
    instructions_v1 = """
Suppose you have already built a Unity scene. Now it is your job to incorporate the feedback of an agent who has provided feedback on misplaced objects. Place again, more precisely, the objects that are said to be in the wrong location. You can do this with placeObject. Another approach to correct the misplaced objects is to change the ground. Do this by (for example) changing the ground heightmap with planGround, then replace the ground in the scene with placeGround. Some objects (e.g. a long bridge), may require the ground to have a certain shape to make sense in, forcing you to reconsider the heightmap in this manner.
"""
    def __init__(self, name=None, instructions=None):
        super().__init__(
            name=name or f"Reformer{random.randint(100,999)}",
            instructions=instructions or self.instructions_v1,
            tools=[placeObject, planGround, placeGround],
            model=MODEL,
        )
