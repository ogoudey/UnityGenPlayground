#############################################################################
#
#   Core world generation module. Contains the following class hierarchy:
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
from agents import Runner
from orchestra import instruments
import time
from typing import Any, Optional
import assets
import synopsis_generator
from orchestra import Checker, Reformer, Conductor
from tools import getGroundMatrix, proposeObject, positionObject, positionVRHumanPlayer, createSkybox, createGround, getContactPoints, createSun, populateHorizon, createSound, create50mx50mGround

from logger import log

from supertools import ConductorRunner

from world import UnityWorld

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
    def __init__(self, preexisting_world: Optional[Any]=None):
        if preexisting_world:
            # load preexising world or something - not really used in Phobia subclass
            pass
        self.preexisting_world = preexisting_world
        self.conductor = Conductor() # conductor has default tools

class UnityWorldGen(WorldGen):
    scene_name: str
    assets: Path
    def __init__(self, scene_name: str, assets_folder: Optional[Path]=None):
        super().__init__()

        if assets_folder is None:
            if ASSETS is None:
                raise EnvironmentError(f"Cannot locate Assets folder. Is {assets_folder} or {ASSETS}. Please set the ASSETS environment variable, or pass the Path as args.")
            assets_folder = ASSETS

        # Unity specific stuff below
        self.scene_name = scene_name
        instruments.world = UnityWorld(scene_name)  
        
        self.assets = assets_folder
        
        if self.assets.exists():
            log(f"Asset Project is \033[1m\033[36m{self.assets}\033[0m", scene_name)
        else:
            log(f"Could not find asset project {self.assets}!!", scene_name)
            if self.assets:
                print(f"Asset project with path {self.assets} does not exist.")
                raise FileNotFoundError(f"Asset project with path {self.assets} does not exist.")
            else:
                print("\033[1m\033[31mAsset project path does not exist or was not provided.\033[0m")
                raise FileNotFoundError("Asset project path does not exist or was not provided.")
        instruments.assets = self.assets

         

        self.conductor_runner = ConductorRunner(run_conductor_function=self.run)
        log("Worldgen constructed.", scene_name)

    async def load(self):
        instruments.asset_catalog = assets.load(self.assets, self.scene_name)
        instruments.synopses = await synopsis_generator.load(self.assets, instruments.asset_catalog,  self.scene_name)
        instruments.skybox_material_leaves =  assets.get_found(".mat", self.assets /"Skybox Materials",  scene_name_for_logging=self.scene_name)
        instruments.ground_material_leaves = assets.get_found(".mat", self.assets /"Ground Materials",  scene_name_for_logging=self.scene_name)
        instruments.sound_leaves = assets.get_found(".mp3", self.assets/ "Sounds",  scene_name_for_logging=self.scene_name)
        
    
    async def run(self, prompt):
        """
            prompt: prompt for Conductor agent to generate world. Example: Generate a fish tank.
        """
        print("\n>>>>>> ", prompt, "\n")
        result = await Runner.run(self.conductor, prompt, max_turns=20)
        print(f"Writing scene to {path}")
        scene_path = instruments.world.done_and_write(self.assets / "Generations" / self.scene_name)
        print(f"Scene @ {scene_path}")
        print(f"Conductor response: \n{result.final_output}")
        log(result.final_output, self.scene_name, wait_time=len(result.final_output)/10)


        return scene_path


    async def regime(self, regime_prompt):
        log("Starting regime", self.scene_name)

        print("\n>>>>>> ", regime_prompt, "\n")
        result = await Runner.run(self.conductor_runner, regime_prompt)
        print(f"Conductor manager response: \n{result.final_output}")
        log(result.final_output, self.scene_name)
        log("Done", self.scene_name)
        

class VRWorldGen(UnityWorldGen):
    
    def __init__(self, scene_name: str, assets_folder: Optional[Path]=None):
        super().__init__(scene_name, assets_folder)
        
    def init_conductor(self):
        # No instructions specified for generic VRWorldGen
        self.conductor.tools.extend([positionVRHumanPlayer, createGround, createSkybox, createSun, createSound, populateHorizon])
        
class AcrophobiaWorldGen(VRWorldGen):
    bridge_prompt="Generate a world that triggers acrophobia while crossing a bridge."
    mountain_prompt="Generate a world that triggers acrophobia on the summit of a mountain."
    skyscraper_prompt="Generate a world that triggers acrophobia on a tall skyscraper."
    building_prompt="Generate a world that triggers acrophobia on a medium-sized building - not too scary."
    roof_prompt="Generate a world that triggers a very sensitive acrophobia by placing a player on the roof of a low house/building."
    platform_prompt="Generate a world that triggers a very sensitive acrophobia by placing a player on a platform."
    bridge_regime_prompt="Generate multiple stages of worlds that trigger acrophobia while crossing a bridge. Have the stages get progressively harder. Let there be three stages and let the heights of the bridges in each stage progress as 2m, 5m, 10m above ground or sea level."

    def __init__(self, scene_name: Optional[str], assets_folder: Optional[Path]=None):
        if scene_name is None:
            scene_name = f"acrophobia_test_{MODEL}_{random.randint(100, 999)}"
        super().__init__(scene_name, assets_folder)
        self.init_conductor()
        log(f"{AcrophobiaWorldGen} initialized.", self.scene_name) 
    
    def init_conductor(self):
        super().init_conductor()
        log(f"Setting MODEL for Conductor to {MODEL}", self.scene_name)
        self.conductor.instructions = Conductor.acrophobia_v1[MODEL]
        # No further tool extensions

"""
Generator_Class_from_Asset_Project_Name = {
    "acrophobia_v1": AcrophobiaWorldGen,
    "acrophobia_u5": AcrophobiaWorldGen,
    "Acrophobia_VR_AI": AcrophobiaWorldGen,
    "acrophobia_u5_v1": AcrophobiaWorldGen,
}
 CHANGE TO ENV VARIABLE"""
