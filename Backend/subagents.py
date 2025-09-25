import random
import os

from agents import Agent
from pydantic import BaseModel

MODEL = (os.getenv("MODEL") or "o3-mini").strip() or "o3-mini"

class GroundData(BaseModel):
    grid: str
    explanation_of_heights: str

class AssetPath(BaseModel):
    asset_path: str

class ObjectPlanner(Agent):
    instructions= "Retrieve the synopsis that best matches the intended description. Return exactly the synopsis."
    
    def __init__(self, tools, name=None, instructions=None, ):
        super().__init__(
            name=name or f"ObjectPlanner{random.randint(100,999)}",
            instructions=instructions or ObjectPlanner.instructions,
            tools=tools,
            model=MODEL,
        )
        
class SkyboxPlanner(Agent):
    instructions= "Given the directory structure (asset tree), return the path to the file of the desired asset."
    
    def __init__(self, tools, name=None, instructions=None):
        super().__init__(
            name=name or f"SkyboxPlanner{random.randint(100,999)}",
            instructions=instructions or SkyboxPlanner.instructions,
            tools=tools,
            output_type=AssetPath,
            model=MODEL,
        )
        
class GroundPlanner(Agent):
    instructions="""Return a heightmap for the ground as an 11x11 grid of floats. 
Rules:
- Write the grid directly as 11 rows of 11 numbers each, separated by spaces. Do not add code, JSON, or extra symbols. 
- Each number is the ground height in meters. A height of 0 means flat ground at sea level. 
- The grid covers 50m x 50m (each cell is 5m x 5m). 
- Keep human scale: a human is ~2m tall, so do not make cliffs or holes taller/deeper than 10m unless the prompt requires it. 
- Shape the terrain according to the prompt, and form around the placed objects. 
- After the grid, add one concise sentence explaining the main heightmap features to guide object placement. 

Output format must follow GroundData:
- grid: the 11x11 float grid as plain text. 
- explanation_of_heights: the one-sentence explanation.
"""
    
    def __init__(self, tools, name=None, instructions=None):
        super().__init__(
            name=name or f"ObjectPlanner{random.randint(100,999)}",
            instructions=instructions or GroundPlanner.instructions,
            tools=tools,
            model=MODEL,
            output_type=GroundData
        )
