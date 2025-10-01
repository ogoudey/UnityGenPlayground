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
    instructions= "Retrieve the synopsis that best matches the intended description. Return exactly the synopsis. If nothing matches, return nothing or a good substitute."
    
    def __init__(self, tools, name=None, instructions=None, ):
        super().__init__(
            name=name or f"ObjectPlanner{random.randint(100,999)}",
            instructions=instructions or ObjectPlanner.instructions,
            tools=tools,
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
  
class GroundPlanner(Agent):
    instructions="""Return a heightmap for the ground as an 11x11 grid of floats. 
Rules:
- Write the grid directly as 11 rows of 11 numbers each, separated by spaces. Do not add code, JSON, or extra symbols.
- Each number is the ground height in meters. A height of 0 means flat ground at sea level. 
- The grid covers 50m x 50m (each cell is 5m x 5m). 
- Keep human scale: a human is ~2m tall, so do not make cliffs or holes taller/deeper than 10m unless the prompt requires it. 
- Shape the terrain according to the prompt, and form around the placed objects (if any).
- Use the planTexture tool to set the texture/material of the ground (include the path in what you return). 
- After the grid, add one concise sentence explaining the main heightmap features to guide object placement. 

Output format must follow GroundData:
- grid: the 11x11 float grid as plain text. 
- texture_path: the path to the asset of the material for this ground, as returned by the planTexture tool.
- explanation_of_heights: the one-sentence explanation.
"""
    instructions_v2="""Return a heightmap for the ground as an 11x11 grid of floats, given the input plan. 
Rules:
- Write the grid directly as 11 rows of 11 numbers each, separated by spaces. Do not add code, JSON, or extra symbols.  Think of the lower-right cell as 0,0
- Each number is the ground height in meters. Suppose that 0 is sea level. 
- The grid covers 50m x 50m (each cell is 5m x 5m) and will be placed in the -X, +Z quadrant. So, the XYZ coordinates (-2, 0, 2) fall in the first cell.
- Keep human scale: a human is ~2m tall, so do not make cliffs or holes taller/deeper than 10m unless the prompt requires it. The height is not scaled, only the horizontal will be scaled. A value of 2 means 2m high.
- Shape the terrain according to the prompt, and form around the placed objects (if any).
- Use the planTexture tool to set the texture/material of the ground (include the path in what you return). 
- After the grid, add an explanation of the landscape and its features. Reference explicitly the input description

Output format must follow GroundData:
- grid: the 11x11 float grid as plain text. 
- texture_path: the path to the asset of the material for this ground, as returned by the planTexture tool.
- explanation_of_heights: the one-sentence explanation.
"""
    instructions_v3={"o3-mini":"""Return a heightmap for the ground as an 11x11 grid of floats, given the input plan. 
Rules:
- Write the grid directly as 11 rows of 11 numbers each, separated by spaces. Do not add code, JSON, or extra symbols.  Think of the lower-right cell as 0,0
- Each number is the ground height in meters. Suppose that 0 is sea level. 
- The grid covers 50m x 50m (each cell is 5m x 5m) and will be placed in the -X, +Z quadrant. So, the XYZ coordinates (2, 0, 2) fall in the first cell.
- Keep human scale: a human is ~2m tall, so do not make cliffs or holes taller/deeper than 10m unless the prompt requires it. The height is not scaled, only the horizontal will be scaled. A value of 2 means 2m high.
- Shape the terrain according to the prompt, and form around the placed objects (if any).
- Use the planTexture tool to set the texture/material of the ground (include the path in what you return). 
- After the grid, add an explanation of the landscape and its features. Reference explicitly the input description

Output format must follow GroundData:
- grid: the 11x11 float grid as plain text. 
- texture_path: the path to the asset of the material for this ground, as returned by the planTexture tool.
- explanation_of_heights: the one-sentence explanation.
"""}
    
    def __init__(self, tools, name=None, instructions=None):
        super().__init__(
            name=name or f"GroundPlanner{random.randint(100,999)}",
            instructions=instructions or GroundPlanner.instructions_v3[MODEL],
            tools=tools,
            model=MODEL,
            output_type=GroundData
        )
        

