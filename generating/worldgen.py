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
import json
import random
from agents import Runner, function_tool
from tools import tools as instruments
import time
from typing import Any, Optional, List
import load.assets as assets
import load.synopsis_generator as synopsis_generator
from llms.orchestra import Conductor
from tools.tools import getGroundMatrix, proposeObject, positionObject, positionVRHumanPlayer, createSkybox, createGround, getContactPoints, createSun, populateHorizon, createSound, createAgent, provideDestinationsForAgent, delete, positionStagePoints

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
    def __init__(self, input_world_name, output_world_name: Optional[Any]=None, conductor_name: str="WorldConductor", conductor_system_prompt: str = "", conductor_tools: List[function_tool]=[]):
        tools_to_add = [getGroundMatrix, proposeObject, positionObject]
        if input_world_name:
            self.preexisting_world_model_dict = self.open_world_model(input_world_name)
            if self.preexisting_world_model_dict:
                tools_to_add.append(delete)
                self.inject_world_model = True
            else:
                self.inject_world_model = False
        self.input_world_name = input_world_name

        self.conductor = Conductor(name=conductor_name, system_prompt=conductor_system_prompt, tools=conductor_tools + tools_to_add)

    @classmethod
    async def generate(cls):
        pass  

    async def load(self):
        pass

    async def run(self, prompt):
        if self.inject_world_model:
            prompt = f"{json.dumps(instruments.core.world.model)}\n=======USER PROMPT:=======\n{prompt}"
        result = await Runner.run(self.conductor, prompt)
        print(result.final_output)
        return result.final_output
    
    def open_world_model(self, input_world_name: str):
        
        supposed_path = Path("generating/models") / f"{input_world_name}.json"
        print(f"Checking {str(supposed_path)} for existing world model...")
        if supposed_path.exists():
            with open(supposed_path, "r") as f:
                j = f.read()
                print(f"... found existing world model.")
                return json.loads(j)
        else:
            return None
    
class UnityWorldGen(WorldGen):
    scene: str
    def __init__(self, input_world_name: str, output_world_name: str, scene_name: str, assets_folder: Optional[Path]=None, conductor_name: str="UnityWorldConductor", conductor_system_prompt: str="", conductor_tools: List[function_tool]=[]):
        super().__init__(input_world_name, output_world_name, conductor_name, conductor_system_prompt, conductor_tools + [createGround, createSkybox, createSun, createSound, populateHorizon])

        # Unity specific stuff below
                
        instruments.core.world = UnityWorld(input_world_name, output_world_name, scene_name, self.preexisting_world_model_dict) 
        try: 
            if self.preexisting_world_model_dict:
                instruments.core.world.open_build_instructions()
        except Exception:
            print("Failed to open build instructions, if any...")
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
        print("Worldgen initialized")

    async def load(self):
        print("Loading...")
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
        if self.inject_world_model:
            info_of_proposed_objects = {}
            for asset_name in list(instruments.core.world.proposed_objects.propositions.keys()):
                if asset_name in instruments.core.asset_catalog:
                    info_of_proposed_objects[asset_name] = instruments.core.asset_catalog[asset_name]

            prompt = f"======World Model:======\nThese things are already in the world, no need to position them again. If you wish to reposition (or if you want to erase from the world), use `delete()`.\n{instruments.core.world.model}\n\n======Proposed objects:======\n(For reference - refer to by exact name).\n{info_of_proposed_objects}\n\n=======USER PROMPT:=======\n{prompt}"
        result = await Runner.run(self.conductor, prompt, max_turns=20)
        try:
            scene_path = instruments.core.world.done_and_write(instruments.core.assets / "Generations" / instruments.core.world.scene.name)
            log(result.final_output)
            return scene_path
        except Exception as e:
            print(f"Did not write scene because {e}.")
            return f"Did not write scene:\n{result.final_output}."

    @classmethod
    async def generate(cls, input_world_name: str, output_world_name: str, multi_stage_mode: bool, assets_folder: Optional[Path], prompt: str):
        print("In Worldgen class method...")
        wg = cls(input_world_name, output_world_name, f"{output_world_name} initial scene", assets_folder)
        await wg.load()
        scene_path = await wg.run(prompt)
        return scene_path

    async def regime(self, regime_prompt):
        log("Starting regime")
        result = await Runner.run(self.conductor_runner, regime_prompt)
        log(result.final_output)
        log("Done")
        
# Class definitions and their tweaks
class VRWorldGen(UnityWorldGen):
    def __init__(self, input_world_name: str, output_world_name: str, scene_name: str, assets_folder: Optional[Path]=None, conductor_name: str="VRExperienceConductor", conductor_system_prompt: str="...", conductor_tools: List[function_tool]=[], ):
        if not os.getenv("VR_HEADSET_TYPE") == "No Player":
            conductor_tools.append(positionVRHumanPlayer)
            if os.getenv("MULTI_STAGE_MODE") == "MULTI":
                conductor_tools.append(positionStagePoints)
        super().__init__(input_world_name, output_world_name, scene_name, assets_folder, conductor_name, conductor_system_prompt, conductor_tools)
                
class AcrophobiaWorldGen(VRWorldGen):
    def __init__(self, input_world_name: str, output_world_name: str, scene_name: str, assets_folder: Optional[Path]=None, conductor_name: str="AcrophobiaConductor", conductor_system_prompt: str=Conductor.acrophobia_v2[MODEL], conductor_tools: List[function_tool]=[]):
        super().__init__(input_world_name, output_world_name, scene_name, assets_folder, conductor_name, conductor_system_prompt, conductor_tools)

class HRIWorldGen(VRWorldGen):
    def __init__(self, input_world_name: str, output_world_name: str, scene_name: str, assets_folder: Optional[Path]=None, conductor_name: str="HRIWorldConductor", conductor_system_prompt: str=Conductor.hri_v1[MODEL], conductor_tools: List[function_tool]=[]):
        super().__init__(input_world_name, output_world_name, scene_name, assets_folder, conductor_name, conductor_system_prompt, conductor_tools + [createAgent, provideDestinationsForAgent])