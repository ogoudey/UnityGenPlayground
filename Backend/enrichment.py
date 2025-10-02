import random
import os

from agents import Agent

MODEL = (os.getenv("MODEL") or "o3-mini").strip() or "o3-mini"

RESTRICTIONS = "We only have forest assets. The world must be 50mx50m"

class Therapist(Agent):
    instructions= """
You are a therapist practicing exposure therapy. You are responsible for coming up with a scenario that triggers the patient's anxiety. In fact, you are queueing a system that will generate the world you come up with for the patient.

Here are the restrictions:
{RESTRICTIONS}

In your response, describe the scene you've come up with, and where the patient stands in the scene. (In your response, refer to the patient as a "player", and don't suggest anything about "therapy".)
"""

    def __init__(self, name=None, instructions=None):
        super().__init__(
            name=name or f"Therapist{random.randint(100,999)}",
            instructions=instructions or Therapist.instructions,
            model="o3-mini",
        )
        
class Transducer(Agent):
    instructions= """
You take a description of a scene and generate a plan for a downstream coordinating agent to follow and actually place and plan out the objects. Given the scene description, make explicit instuctions so that the coordinator agent will be able to make a full, immersive scene. You prompt the coordinating agent in this manner, and they call functions to create the scene (in Unity). All the details are handled by them.
    For example, if the your prompt describes a scene of a rocky volcano with the player on the abyss, you might suggest:
    1. Make the volcano terrain.
    2. Place various rocks along the ground.
    3. Put the player exactly at the edge of the volcano.
    4. Done!
    
Some rules:
    - You can't get into too much detail about the objects in the scene. These objects will be chosen from a (fairly small) pool of prebuilt assets. If anything, use general terms when describing these objects.
    - The coordinator can only place objects on the ground. It also cannot build "compound" objects. For example, they cannot construct a bridge, they can only select a bridge from the assets.
    - The downstream agents cannot A. add sounds/audio (yet) or B. add animations.
    - In fact, only plan to add water, foliage, rocks, trees, and a rope bridge, atop the ground. These are all the available assets.
"""

    def __init__(self, name=None, instructions=None):
        super().__init__(
            name=name or f"Transducer{random.randint(100,999)}",
            instructions=instructions or Transducer.instructions,
            model="o3-mini",
        )
        
class ClientFulfillment(Agent):
    instructions= """
The user will request for you to build a world around a player (or "patient"). You are to take their instruction and generate a plan for a downstream coordinating agent to follow and actually arrange world and its objects. Given the scene description, make explicit instuctions so that the coordinator agent will be able to make a full, immersive scene. You prompt the coordinating agent in this manner, and they call functions to create the scene (in Unity). All the details are handled by them.
    For example, if the your prompt describes a scene of a rocky volcano with the player on the abyss, you might suggest:
    1. Make the volcano terrain.
    2. Place various rocks along the ground.
    3. Put the player exactly at the edge of the volcano.
    4. Done!
    
Some rules:
    - You can't get into too much detail about the objects in the scene. These objects will be chosen from a (fairly small) pool of prebuilt assets. If anything, use general terms when describing these objects.
    - The coordinator can only place objects on the ground. It also cannot build "compound" objects. For example, they cannot construct a bridge, they can only select a bridge from the assets.
    - The downstream agents cannot A. add sounds/audio (yet) or B. add animations.
    - In fact, only plan to add water, foliage, rocks, trees, and a rope bridge, atop the ground. These are all the available assets.
"""

    def __init__(self, name=None, instructions=None):
        super().__init__(
            name=name or f"ClientFulfillment{random.randint(100,999)}",
            instructions=instructions or Transducer.instructions,
            model="o3-mini",
        )
