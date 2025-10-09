import random
import os
import sys

from agents import Agent
from pydantic import BaseModel

MODEL = (os.getenv("MODEL") or "o3-mini").strip() or "o3-mini"

class GroundData(BaseModel):
    grid: str
    texture_path: str
    explanation_of_heights: str

class AssetPath(BaseModel):
    asset_path: str

class SynopsisNote(BaseModel):
    synopsis: str
    note: str

class SunPlanner(Agent):
    instructions= "It is your job to place the sun in the sky according to the descriptive prompt by fixing certain parameters. Simply return Success, unless something has failed."
    
    def __init__(self, tools, name=None, instructions=None, ):
        super().__init__(
            name=name or f"SunPlanner{random.randint(100,999)}",
            instructions=instructions or SunPlanner.instructions,
            tools=tools,
            model=MODEL,
        )

class ObjectPlanner(Agent):
    instructions_v1= "You will be provided a list of synopses (or summaries) of assets. It is your job to retrieve the synopsis that best matches the intended description to the user who doesn't know what assets are available. If the user seems misguided in their intention for an object, put that in a note and return the closest thing. Try to return one of the synopses for each request, leaving a note of the discrepency if any. Some rules: 1. You cannot change the object synopsis at all when you return it. 2. Don't mention the synopsis in your note. The note should inform placement of the object by refering to any mismatch in features of the retrieved vs desired asset. The user cannot scale or edit the asset you choose, only place it."
    
    def __init__(self, tools, name=None, instructions=None, ):
        super().__init__(
            name=name or f"ObjectPlanner{random.randint(100,999)}",
            instructions=instructions or ObjectPlanner.instructions_v1,
            tools=tools,
            output_type=SynopsisNote,
            model=MODEL,
        )
        
class SkyboxPlanner(Agent):
    instructions= "Given the directory structure (asset tree), return the path to the file of the desired asset."
    
    def __init__(self, name=None, instructions=None):
        super().__init__(
            name=name or f"SkyboxPlanner{random.randint(100,999)}",
            instructions=instructions or SkyboxPlanner.instructions,
            output_type=AssetPath,
            model=MODEL,
        )
        
class TexturePlanner(Agent):
    instructions= "Given the directory structure (asset tree), return the path of a material asset that matches the description."
    
    def __init__(self, name=None, instructions=None):
        super().__init__(
            name=name or f"TexturePlanner{random.randint(100,999)}",
            instructions=instructions or TexturePlanner.instructions,
            output_type=AssetPath,
            model=MODEL,
        )


# Ground planner's example input:
#
#        Example (a string):
#            To make a volcano:
#                1. Form the mountain
#                2. Make the crater in the top.
#        Another example:
#            Make room for a house with a flat 4mx4m base at (-5, 2.5, 5)
#                1. Since the horizonal scale is 5, turn the -5, 5 into coordinates 1,1. Make this coordinate have height 2.5
#                2. Make in the -X, +Z direction the base of the house. 4m / scale of 5 is .8 or 1 grid cell. So make (1, 2), (2, 2), and (2, 1) all height 2.5 too.
#                3. Make the points surrounding the indent a sort of gradient. Have them all close to 2.5, and spread that out, without affecting other landmarks. 
  
class GroundCreator(Agent):
    instructions_v3={"o4-mini":"""Return a heightmap for the ground as an grid of floats, given the input plan, resolution, and scale. 
Rules:
- Write the grid directly as <resolution> rows of <resolution> numbers each, separated by spaces. Do not add code, JSON, or extra symbols.  Think of the lower-left cell as 0,0
- Each number is the ground height in meters. Suppose that 0 is sea level. 
- The grid covers (<resolution> * <scale> - <scale>) meters by (<resolution> * <scale> - <scale>) meters (each cell is <scale> x <scale>) and will be placed in the +X, +Z quadrant. So, the XYZ coordinates (2, 0, 2) fall in the first cell.
- Keep human scale: a human is ~2m tall, so do not make cliffs or holes taller/deeper than 10m unless the prompt requires it. The height is not scaled, only the horizontal will be scaled. A height value of 2 means 2m high.
- Shape the terrain according to the prompt, and form around the placed objects (if any).
- Use the planTexture tool to set the texture/material of the ground (include the path in what you return). 
- After the grid, add an explanation of the landscape and its features. Reference explicitly the input description but don't refer to indices. Put your explanation in terms of meters, not indices. Give abundant information about the ground in terms of meters.

Output format must follow GroundData:
- grid: the float grid as plain text sized according to the resolution. 
- texture_path: the path to the asset of the material for this ground, as returned by the planTexture tool.
- explanation_of_heights: an explanation in around one sentence.
"""}
    
    def __init__(self, tools, name=None, instructions=None):
        super().__init__(
            name=name or f"GroundPlanner{random.randint(100,999)}",
            instructions=instructions or GroundCreator.instructions_v3[MODEL],
            tools=tools,
            model=MODEL,
            output_type=GroundData
        )
        

