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
import sys
from pathlib import Path
import os
import random
from agents import Runner, function_tool
from tools import tools as instruments
import time
from typing import Any, Optional, List
import load.assets as assets
import load.synopsis_generator as synopsis_generator
from llms.orchestra import Conductor
from tools.tools import getGroundMatrix, proposeObject, positionObject, positionVRHumanPlayer, createSkybox, createGround, getContactPoints, createSun, populateHorizon, createSound, create50mx50mGround

from logger import log

from llms.supertools import ConductorRunner

from generating.world import UnityWorld

class EnvironmentError(Exception):
    pass

try:
    val = os.getenv("ASSETS")
    ASSETS: Path = Path(val) if not val is None else None
    MODEL = (os.getenv("MODEL") or "o4-mini").strip() or "o4-mini"
    SKYBOX = os.environ.get("SKYBOX_MATERIALS", "Skybox Materials")
    GROUND = os.environ.get("GROUND_MATERIALS", "Ground Materials")
    SOUNDS = os.environ.get("SOUNDS", "Sounds")
except Exception as e:
    raise EnvironmentError("Could not establish environment variables: {e}")




class WorldGen:
    def __init__(self, world_name: Optional[Any]=None, conductor_name: str="WorldConductor", conductor_system_prompt: str = "", conductor_tools: List[function_tool]=[]):
        if world_name:
            # load preexising world or something - not really used yet
            pass
        self.world_name = world_name

        self.conductor = Conductor(name="Default", system_prompt=conductor_system_prompt, tools=conductor_tools + [getGroundMatrix, proposeObject, positionObject])
    
    async def load(self):
        pass

    async def run(self, prompt):
        result = await Runner.run(self.conductor, prompt)
        print(result.final_output)
        return result.final_output
    
class UnityWorldGen(WorldGen):
    scene: str
    def __init__(self, world_name: str, scene_name: str, assets_folder: Optional[Path]=None, conductor_name: str="UnityWorldConductor", conductor_system_prompt: str="", conductor_tools: List[function_tool]=[]):
        super().__init__(None, conductor_name, conductor_system_prompt, conductor_tools + [createGround, createSkybox, createSun, createSound, populateHorizon])

        

        # Unity specific stuff below
                
        instruments.core.world = UnityWorld(world_name, scene_name)  

        if assets_folder is None:
            if ASSETS is None:
                raise EnvironmentError(f"\nCannot locate Assets folder. Tried:\n\tUnityWorldGen arg: {assets_folder}\n\tASSETS env variable: {ASSETS}.\nPlease set at least one to a Unity Project/Assets folder.")
            assets_folder = ASSETS

        
        if assets_folder.exists():
            log(f"Asset Project is \033[1m\033[36m{assets_folder}\033[0m")
        else:
            log(f"Could not find asset project {assets_folder}!!")
            if assets_folder:
                print(f"Asset project with path {assets_folder} does not exist.")
                raise FileNotFoundError(f"Asset project with path {assets_folder} does not exist.")
            else:
                print("\033[1m\033[31mAsset project path does not exist or was not provided.\033[0m")
                raise FileNotFoundError("Asset project path does not exist or was not provided.")
        instruments.core.assets = assets_folder
        
        self.conductor_runner = ConductorRunner(run_conductor_function=self.run)

    async def load(self):
        instruments.core.asset_catalog = assets.load(instruments.core.assets)
        instruments.core.synopses = await synopsis_generator.load(instruments.core.assets, instruments.core.asset_catalog)
        instruments.core.skybox_material_leaves =  assets.get_found(".mat", instruments.core.assets / SKYBOX)
        instruments.core.ground_material_leaves = assets.get_found(".mat", instruments.core.assets / GROUND)
        instruments.core.sound_leaves = assets.get_found(".mp3", instruments.core.assets / SOUNDS)
        
    async def dummy_run(self, prompt):
        print(f"Thinking on {prompt}")
        time.sleep(5)
        return "Done"
    
    async def run(self, prompt):
        """
            prompt: prompt for Conductor agent to generate world. Example: Generate a fish tank.
        """
        result = await Runner.run(self.conductor, prompt, max_turns=20)
        try:
            scene_path = instruments.core.world.done_and_write(instruments.core.assets / "Generations" / instruments.core.world.scene.name)
            log(f"{result.final_output}")
            return scene_path
        except Exception:
            print(f"Did not write scene:\n{result.final_output}")
            return f"Did not write scene:\n{result.final_output}."

    @classmethod
    async def generate(cls, world_name: str, assets_folder: Optional[Path], prompt: str):
        wg = cls(world_name, f"{world_name}_0", assets_folder)
        await wg.load()
        scene_path = await wg.run(prompt)
        return scene_path

    async def regime(self, regime_prompt):
        log("Starting regime", self.scene_0)
        result = await Runner.run(self.conductor_runner, regime_prompt)
        log(result.final_output, self.scene_0)
        log("Done", self.scene_0)
        

class VRWorldGen(UnityWorldGen):
    
    def __init__(self, world_name: str, scene_name: str, assets_folder: Optional[Path]=None, conductor_name: str="VRExperienceConductor", conductor_system_prompt: str="...", conductor_tools: List[function_tool]=[], ):
        super().__init__(world_name, scene_name, assets_folder, conductor_name, conductor_system_prompt, conductor_tools + [positionVRHumanPlayer])
                
class AcrophobiaWorldGen(VRWorldGen):
    bridge_prompt="Generate a world that triggers acrophobia while crossing a bridge."
    mountain_prompt="Generate a world that triggers acrophobia on the summit of a mountain."
    skyscraper_prompt="Generate a world that triggers acrophobia on a tall skyscraper."
    building_prompt="Generate a world that triggers acrophobia on a medium-sized building - not too scary."
    roof_prompt="Generate a world that triggers a very sensitive acrophobia by placing a player on the roof of a low house/building."
    platform_prompt="Generate a world that triggers a very sensitive acrophobia by placing a player on a platform."
    bridge_regime_prompt="Generate multiple stages of worlds that trigger acrophobia while crossing a bridge. Have the stages get progressively harder. Let there be three stages and let the heights of the bridges in each stage progress as 2m, 5m, 10m above ground or sea level."

    def __init__(self, world_name: str, scene_name: str, assets_folder: Optional[Path]=None, conductor_name: str="AcrophobiaConductor", conductor_system_prompt: str=Conductor.acrophobia_v1[MODEL], conductor_tools: List[function_tool]=[]):
        super().__init__(world_name, scene_name, assets_folder, conductor_name, conductor_system_prompt, conductor_tools)