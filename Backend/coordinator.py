import os
import random

from agents import Agent
from pydantic import BaseModel


import tools
from tools import getGroundMatrix, proposeObject, positionObject, positionVRHumanPlayer, createSkybox, createGround, getContactPoints, createSun

MODEL = (os.getenv("MODEL") or "o4-mini").strip() or "o4-mini"
    
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
    Keep your answer brief and to the point. It is recommended to use get_ground_matrix for all checks. 
"""

    def __init__(self, name=None, instructions=None):
        super().__init__(
            name=name or f"Checker{random.randint(100,999)}",
            instructions=instructions or Checker.instructions,
            tools=[getGroundMatrix],
            output_type=Check,
            model=MODEL,
        )

class Coordinator(Agent):
    phobia_v1={"o4-mini":"""Whatever a universal scarer might be"""}

    # TODO Embellish Ground prompt
    # TODO What is the best way to describe an origin of an object?
    acrophobia_v1={"o4-mini":"""You are the Coordinator agent responsible for generating a Unity scene that matches the user prompt. +X is "East"/to the right, +Y is up, and +Z "North".
You must orchestrate tool usage in the following structured order:

1. SKYBOX: The first couple steps are simple. First, call createSkybox once to describe an appropriate skybox. 
2. SUN: Call createSun to describe an appropriate Sun.
3. GROUND: Call createGround to design the terrain/heightmap. This is an initial guess for the terrain of the /\. In further steps, you may call createGround again to fit the objects that need the terrain to conform to it. Try to make it natural.
4. OBJECTS: After the ground is placed, you will begin setting the objects of the scene. To do this, propose each (type of) object one by one with proposeObject. For the proposeObject call:
   - Do not plan multiple objects in a single call. Do not plan anything like a "cluster" of objects.
   - Do not include placement/location information, only stuff about the size, theme, type, etc.
   - When you propose an object you will receive this information:
    {
        "Object": {
            "Name": the object's name,
            "Info": {
                "Local origin": the objects local origin described relative to its geometry,
                "Dimensions": the object's dimension,
                (Optional) "Extra/Recommendation/...": any extra local information about the object, relative to its local origin.
            }
        }
        "Note": a message from the planner that explains how the returned object might differ from the request.
    }  
Once you have an objects information, you may instace the object in the world you are creating. To do this, call positionObject:
   - DO include placement and rotation information (obviously, given the args).
   - Objects pivot around the axes through their local origin (recall, Y is up).
   - Object should (obviously) be placed OVER the ground (atop or aligned with it), and all other details should be as-close-to-physics-as-possible.
   - Pay close attention to the difficult problem of fitting already-structured objects in with other objects/terrain. 
5. REMAKING GROUND: Some objects (e.g. a long bridge), may require the ground to have a certain shape in order for them to fi. This will force you to reconsider the heightmap of the ground, in which case you should call createGround again and "excavate" the land around the uncooperative object.
6. HUMAN VR PLAYER: When the scene is finalized, place the VR player in the scene with the place_vr_human_player tool (if made available to you - if not, forget about it). 
7. COMPLETENESS: Ensure that all elements mentioned in the user prompt are represented in the scene. 
   If something is vague (e.g. "foliage"), interpret it reasonably and cover the intent. 

General rules:
- Always PLAN before PLACE.
- Use get_contact_points to get an estimate of exact (x, y, z) coordinates available for placing objects on.
- Use all other tools at least once when appropriate.
- Use planGround/placeGround multiple times if need be.
- Stop once the world clearly reflects the prompt, and don't stop until you are done.

Your role is to reliably build a coherent, grounded Unity world from the description."""}

    def __init__(self, name=None, instructions=None, tools=None):
        super().__init__(
            name=name or f"Coordinator{random.randint(100,999)}",
            instructions=instructions or Coordinator.acrophobia_v1[MODEL],
            tools=tools or [getContactPoints, createGround, proposeObject, positionObject],
            model=MODEL,
        )
        self.restriction = None
        

class Reformer(Agent):
    instructions_v1 = """
Suppose you have already built a Unity scene. Now it is your job to incorporate the feedback of an agent who has provided feedback on misplaced objects. Place again, more precisely, the objects that are said to be in the wrong location. You can do this with placeObject. Another approach to correct the misplaced objects is to change the ground. Do this by (for example) changing the ground heightmap with planGround, then replace the ground in the scene with placeGround. Some objects (e.g. a long bridge), may require the ground to have a certain shape to make sense in, forcing you to reconsider the heightmap in this manner.
"""
    def __init__(self, name=None, instructions=None):
        super().__init__(
            name=name or f"Reformer{random.randint(100,999)}",
            instructions=instructions or self.instructions_v1,
            tools=[],
            model=MODEL,
        )
