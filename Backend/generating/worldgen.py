#############################################################################
#
#   Core world generation module. Responsibilities:
#       1. Linking the Conductor agent to tools
#       2. Setting the world type of the tools
#       3. 
# Contains the following class hierarchy:
#
#                       WorldGen
#                          V
#                    UnityWorldGen
#                          V
#                      VRWorldGen
#                          V
#                   AcrophobiaWorldGen <- the one we use
#
# Environment variables OR arguments to the Class are use as the generator's settings.
# 
#
# 
#                         Env variables     Initialization args
#                                        |
#  python (tests)      set env variables |  python args
#                         _______________|______________
#                                        |
# from Unity (prod)     shell from Unity | args from Unity 
#                                        |
# 
#
#############################################################################


from pathlib import Path
import os
import random
from agents import Runner, function_tool
from Backend.agents.orchestra import instruments
import time
from typing import Any, Optional, List
import Backend.load.assets as assets
import Backend.load.synopsis_generator as synopsis_generator
from Backend.agents.orchestra import Checker, Reformer, Conductor
from Backend.tools.tools import getGroundMatrix, proposeObject, positionObject, positionVRHumanPlayer, createSkybox, createGround, getContactPoints, createSun, populateHorizon, createSound, create50mx50mGround

from logger import log

from Backend.agents.supertools import ConductorRunner

from Backend.generating.world import UnityScene

class EnvironmentError(Exception):
    pass

try:
    val = os.getenv("ASSETS")
    ASSETS: Path = Path(val) if not val is None else None

    WORLDGEN_CLASS = "AcrophobiaWorldGen"
    MODEL = (os.getenv("MODEL") or "o4-mini").strip() or "o4-mini"
except Exception as e:
    raise EnvironmentError("Could not establish environment variables: {e}")



def log_env_vars():
    print(f"ASSETS: {ASSETS}")
    print(f"WORLDGEN_CLASS: {WORLDGEN_CLASS}")
    print(f"MODEL: {MODEL}")

class WorldGen:
    def __init__(self, preexisting_world: Optional[Any]=None, conductor_name: str="WorldConductor", conductor_system_prompt: str = "", conductor_tools: List[function_tool]=[]):
        if preexisting_world:
            # load preexising world or something - not really used yet
            pass
        self.preexisting_world = preexisting_world

        self.conductor = Conductor(name="Default", system_prompt=conductor_system_prompt, tools=conductor_tools + [getGroundMatrix, proposeObject, positionObject])
    
    async def load(self):
        pass

    async def run(self, prompt):
        result = await Runner.run(self.conductor, prompt)
        print(result.final_output)
        return result.final_output
    
class UnityWorldGen(WorldGen):
    scene_name: str
    def __init__(self, scene_name: str, assets_folder: Optional[Path]=None, conductor_name: str="UnityWorldConductor", conductor_system_prompt: str="", conductor_tools: List[function_tool]=[]):
        super().__init__(None, conductor_name, conductor_system_prompt, conductor_tools + [createGround, createSkybox, createSun, createSound, populateHorizon])

        

        # Unity specific stuff below
        self.scene_name = scene_name
        instruments.world = UnityScene(scene_name)  

        if assets_folder is None:
            if ASSETS is None:
                raise EnvironmentError(f"Cannot locate Assets folder. Is {assets_folder} or {ASSETS}. Please set the ASSETS environment variable, or pass the Path as args.")
            assets_folder = ASSETS

        
        if assets_folder.exists():
            log(f"Asset Project is \033[1m\033[36m{assets_folder}\033[0m", scene_name)
        else:
            log(f"Could not find asset project {assets_folder}!!", scene_name)
            if assets_folder:
                print(f"Asset project with path {assets_folder} does not exist.")
                raise FileNotFoundError(f"Asset project with path {assets_folder} does not exist.")
            else:
                print("\033[1m\033[31mAsset project path does not exist or was not provided.\033[0m")
                raise FileNotFoundError("Asset project path does not exist or was not provided.")
        instruments.assets = assets_folder
        
        self.conductor_runner = ConductorRunner(run_conductor_function=self.run)

    async def load(self):
        instruments.asset_catalog = assets.load(instruments.assets, self.scene_name)
        instruments.synopses = await synopsis_generator.load(instruments.assets, instruments.asset_catalog,  self.scene_name)
        instruments.skybox_material_leaves =  assets.get_found(".mat", instruments.assets /"Skybox Materials",  scene_name_for_logging=self.scene_name)
        instruments.ground_material_leaves = assets.get_found(".mat", instruments.assets /"Ground Materials",  scene_name_for_logging=self.scene_name)
        instruments.sound_leaves = assets.get_found(".mp3", instruments.assets/ "Sounds",  scene_name_for_logging=self.scene_name)
        
    
    async def run(self, prompt):
        """
            prompt: prompt for Conductor agent to generate world. Example: Generate a fish tank.
        """
        result = await Runner.run(self.conductor, prompt, max_turns=20)
        scene_path = instruments.world.done_and_write(instruments.assets / "Generations" / self.scene_name)

        return scene_path


    async def regime(self, regime_prompt):
        log("Starting regime", self.scene_name)
        result = await Runner.run(self.conductor_runner, regime_prompt)
        log(result.final_output, self.scene_name)
        log("Done", self.scene_name)
        

class VRWorldGen(UnityWorldGen):
    
    def __init__(self, scene_name: str, assets_folder: Optional[Path]=None, conductor_name: str="VRExperienceConductor", conductor_system_prompt: str="...", conductor_tools: List[function_tool]=[], ):
        super().__init__(scene_name, assets_folder, conductor_name, conductor_system_prompt, conductor_tools + [positionVRHumanPlayer])
                
class AcrophobiaWorldGen(VRWorldGen):
    bridge_prompt="Generate a world that triggers acrophobia while crossing a bridge."
    mountain_prompt="Generate a world that triggers acrophobia on the summit of a mountain."
    skyscraper_prompt="Generate a world that triggers acrophobia on a tall skyscraper."
    building_prompt="Generate a world that triggers acrophobia on a medium-sized building - not too scary."
    roof_prompt="Generate a world that triggers a very sensitive acrophobia by placing a player on the roof of a low house/building."
    platform_prompt="Generate a world that triggers a very sensitive acrophobia by placing a player on a platform."
    bridge_regime_prompt="Generate multiple stages of worlds that trigger acrophobia while crossing a bridge. Have the stages get progressively harder. Let there be three stages and let the heights of the bridges in each stage progress as 2m, 5m, 10m above ground or sea level."

    def __init__(self, scene_name: str, assets_folder: Optional[Path]=None, conductor_name: str="AcrophobiaConductor", conductor_system_prompt: str=Conductor.acrophobia_v1[MODEL], conductor_tools: List[function_tool]=[]):
        super().__init__(scene_name, assets_folder, conductor_name, conductor_system_prompt, conductor_tools)