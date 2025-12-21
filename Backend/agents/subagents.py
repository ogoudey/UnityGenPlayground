import random
import os
import sys
from pathlib import Path
from agents import Agent
from pydantic import BaseModel, field_validator
from dataclasses import dataclass

MODEL = (os.getenv("MODEL") or "o3-mini").strip() or "o3-mini"



@dataclass
class RelativePath:
    path: Path
    
class AssetsRelativePathStr(BaseModel):
    path: str

class SynopsisNote(BaseModel):
    synopsis: str
    note: str

class GroundData(BaseModel):
    grid: str
    texture_path_str: str
    explanation_of_heights: str

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
            output_type=AssetsRelativePathStr,
            model=MODEL,
        )

class SoundDesigner(Agent):
    instructions = "Given the directory structure (asset tree), return the path to the file of the asset that best fits the desired description of a sound."

    def __init__(self, name=None, instructions=None, ):
        super().__init__(
            name=name or f"SoundDesigner{random.randint(100,999)}",
            instructions=instructions or SoundDesigner.instructions,
            output_type=AssetsRelativePathStr,
            model=MODEL,
        )

class TexturePlanner(Agent):
    instructions= "Given the directory structure (asset tree), return the path of a material asset that matches the description."
    
    def __init__(self, name=None, instructions=None):
        super().__init__(
            name=name or f"TexturePlanner{random.randint(100,999)}",
            instructions=instructions or TexturePlanner.instructions,
            output_type=AssetsRelativePathStr,
            model=MODEL,
        )

class GroundCreator(Agent):
    instructions_v3={"o4-mini":"""Return a heightmap for the ground as an grid of floats, given the input plan, resolution, and scale. 
Rules:
- Write the grid directly as {resolution} rows of {resolution} numbers each, separated by spaces. Do not add code, JSON, or extra symbols.  Think of the lower-left cell as 0,0
- Each number is the ground height in meters. Suppose that 0 is sea level. 
- The grid covers ({resolution} * {scale} - {scale}) meters by ({resolution} * {scale} - {scale}) meters (each cell is {scale} x {scale}) and will be placed in the +X, +Z quadrant. So, the XYZ coordinates (2, 0, 2) fall in the first cell.
- Keep human scale: a human is ~2m tall, so do not make cliffs or holes taller/deeper than 10m unless the prompt requires it. The height is not scaled, only the horizontal will be scaled. A height value of 2 means 2m high.
- Shape the terrain according to the prompt, and form around the placed objects (if any).
- Use the planTexture tool to set the texture/material of the ground (include the path in what you return). 
- After the grid, add an explanation of the landscape and its features. Reference explicitly the input description but don't refer to indices. Put your explanation in terms of meters, not indices. Give abundant information about the ground in terms of meters.

Output format must follow GroundData:
- grid: the float grid as plain text sized according to the resolution. 
- texture_path: the path to the asset of the material for this ground, as returned by the planTexture tool.
- explanation_of_heights: an explanation in around one sentence.
"""}
    instructions_v3_perimeter_0={"o4-mini":"""Return a square heightmap for the ground as a {resolution} by {resolution} grid of floats, given the input plan, resolution, and scale. 
Rules:
- Write the grid directly as {resolution} rows of {resolution} numbers each, separated by spaces. Do not add code, JSON, or extra symbols.  Think of the lower-left cell as 0,0
- Each number is the ground height in meters. Suppose that -1m is sea level. 
- The grid covers {dimension} meters by {dimension} meters. Each cell is {scale} x {scale} and will be placed in the +X, +Z quadrant. So, the XYZ coordinates (2, 0, 2), for example, fall in the first cell.
- Keep human scale: a human is ~2m tall, so do not make cliffs or holes taller/deeper than 10m unless the prompt requires it. The height is not scaled, only the horizontal will be scaled. A height value of 2, for example, means 2m high.
- Shape the terrain according to the prompt, and form around the placed objects (if any).
- Use the planTexture tool to set the texture/material of the ground (include the path in what you return). 
- After the grid, add an explanation of the landscape and its features. Reference explicitly the input description but don't refer to indices. Put your explanation in terms of meters, not indices. Give abundant information about the ground in terms of meters.
- The values on the perimeter of the world must be 0. This is important because this smallish grid you're making slots within an outside plain. This outside plain is at "ground level" - heights of 0.
                                 
Output format must follow GroundData:
- grid: the float grid as plain text sized according to the resolution (perimeter 0) MUST BE {resolution} x {resolution}. After generating the grid, verify internally that it is a perfect square ({resolution} rows x {resolution} columns).
If not, correct it before continuing.
- texture_path: the path to the asset of the material for this ground, as returned by the planTexture tool.
- explanation_of_heights: an explanation in around one sentence.
"""}
    
    def __init__(self, tools, name=None, instructions=None, set_perimeter_to_0=True, resolution=10, scale=5.0):
        if set_perimeter_to_0:
            known_instructions = GroundCreator.instructions_v3_perimeter_0[MODEL]
        else:
            known_instructions = GroundCreator.instructions_v3[MODEL]
        dimension = resolution*scale - scale

        super().__init__(
            name=name or f"GroundPlanner{random.randint(100,999)}",
            instructions=(instructions or known_instructions).format(resolution=resolution, scale=scale, dimension=dimension),
            tools=tools,
            model=MODEL,
            output_type=GroundData
        )
        

