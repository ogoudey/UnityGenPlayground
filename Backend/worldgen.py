from pathlib import Path
import os
import random
from agents import Runner
from agents.extensions.visualization import draw_graph
from conductors import instruments
import time
from typing import Any
import assets
import synopsis_generator
from enrichment import Phobos
from conductors import Checker, Reformer, Conductor
from tools import getGroundMatrix, proposeObject, positionObject, positionVRHumanPlayer, createSkybox, createGround, getContactPoints, createSun, populateHorizon, createSound, create50mx50mGround

from logger import log

from supertools import ConductorRunner

from world import UnityWorld

MODEL = (os.getenv("MODEL") or "o3-mini").strip() or "o3-mini"
ASSET_LIB_PATH = (os.getenv("ASSET_LIB_PATH") or "../Resources/Asset Projects").strip() or "../Resources/Asset Projects"
DRAWING = True
if DRAWING:
    print(f"Will draw a graph for Conductor...")

class WorldGen:
    def __init__(self, preexisting_world):
        if preexisting_world:
            # load preexising world or something - not really used in Phobia subclass
            pass
        self.preexisting_world = preexisting_world
        pass

class UnityWorldGen(WorldGen):
    asset_project_path: Path
    def __init__(self, asset_project_path: str, scene_name: str, preexisting_world: Any = None, restriction: str | None = None):
        super().__init__(preexisting_world)
        self.asset_project_path = Path(asset_project_path)
        if asset_project_path and self.asset_project_path.exists():
            print(f"Asset Project is \033[1m\033[36m{asset_project_path}\033[0m")
        else:
            if asset_project_path:
                print(f"Asset project with path {asset_project_path} does not exist.")
                raise FileNotFoundError(f"Asset project with path {asset_project_path} does not exist.")
            else:
                print("\033[1m\033[31mAsset project path does not exist or was not provided.\033[0m")
                raise FileNotFoundError("Asset project path does not exist or was not provided.")
        instruments.asset_project = asset_project_path
        if not scene_name:
            scene_name = f"scene_{MODEL}_{random.randint(100, 999)}"
        self.scene_name = scene_name
        instruments.world = UnityWorld()   
        self.conductor = Conductor()
        if restriction:
            self.conductor.restriction = restriction
        self.conductor_runner = ConductorRunner(run_conductor_function=self.run)

    async def load(self):
        print("\n  ___Asset Catalog___")
        print("Catalog maps `path => object data`")
        instruments.asset_catalog = assets.load(self.asset_project_path)
        print("\n  ___Synopsis File___")
        print("Maps `synopsis of object data => asset path`")
        instruments.synopses = await synopsis_generator.load(instruments.asset_catalog)
        print("\n  ___Special Materials___")
        print("Curated collections of materials for special objects")
        instruments.skybox_material_leaves =  assets.get_found(".mat", asset_projects=ASSET_LIB_PATH, asset_project_path=self.asset_project_path / "Assets/Skybox Materials")
        instruments.ground_material_leaves = assets.get_found(".mat", asset_projects=ASSET_LIB_PATH, asset_project_path=self.asset_project_path / "Assets/Ground Materials")
        instruments.sound_leaves = assets.get_found(".mp3", asset_projects=ASSET_LIB_PATH, asset_project_path=self.asset_project_path / "Assets/Sounds")
        
    
    async def run(self, prompt):
        """
            prompt: prompt for Conductor agent to generate world. Example: Generate a fish tank.
        """
        print("\n>>>>>> ", prompt, "\n")
        result = await Runner.run(self.conductor, prompt, max_turns=20)
        path = str(self.asset_project_path / "Assets" / "Generations" / self.scene_name) # should stringify later?
        scene_path = instruments.world.done_and_write(path)
        print(f"Scene @ {scene_path}")
        print(f"Conductor response: \n{result.final_output}")
        log(result.final_output)
        log(f"World generated at {scene_path}", type="bold")

        if DRAWING:
            draw_graph(self.conductor, filename="conductor_graph")
        return path


    async def regime(self, regime_prompt):
        log("Starting regime")

        print("\n>>>>>> ", regime_prompt, "\n")
        result = await Runner.run(self.conductor_runner, regime_prompt)
        print(f"Conductor manager response: \n{result.final_output}")
        log(result.final_output)
        log("Done")
        

class VRWorldGen(UnityWorldGen):
    
    def __init__(self, asset_project_path: str, scene_name: str, restriction: str):
        super().__init__(asset_project_path, scene_name, None, restriction)
        instruments.asset_project = asset_project_path
        self.conductor.tools.extend([positionVRHumanPlayer, createGround, createSkybox, createSun, createSound, populateHorizon])
        self.conductor.instructions = Conductor.phobia_v1[MODEL]
        self.patient = Phobos() 

    
        
class AcrophobiaWorldGen(VRWorldGen):
    bridge_prompt="Generate a world that triggers acrophobia while crossing a bridge."
    mountain_prompt="Generate a world that triggers acrophobia on the summit of a mountain."
    skyscraper_prompt="Generate a world that triggers acrophobia on a tall skyscraper."
    building_prompt="Generate a world that triggers acrophobia on a medium-sized building - not too scary."
    roof_prompt="Generate a world that triggers a very sensitive acrophobia by placing a player on the roof of a low house/building."
    platform_prompt="Generate a world that triggers a very sensitive acrophobia by placing a player on a platform."
    
    bridge_regime_prompt="Generate multiple stages of worlds that trigger acrophobia while crossing a bridge. Have the stages get progressively harder. Let there be three stages and let the heights of the bridges in each stage progress as 2m, 5m, 10m above ground or sea level."

    def __init__(self, asset_project_path: str="acrophobia_u5", restricted: bool = False, scene_name: str | None = None):
        if scene_name is None:
            scene_name = f"acro_50_{MODEL}_{random.randint(100, 999)}"
        asset_project_path = Path(ASSET_LIB_PATH) / asset_project_path
        instruments.asset_project = asset_project_path
        restriction = f"These are the assets the system is restricted to:\n{[key.split('/')[-1] for key in list(instruments.asset_catalog.keys())]}" if restricted else ""
        super().__init__(asset_project_path, f"acro_{MODEL}_{random.randint(100, 999)}", restriction)
        self.conductor.instructions = Conductor.acrophobia_v1[MODEL]

    async def get_prompt(self):
        print("Getting prompt from patient...")
        result = await Runner.run(self.patient, self.patient.acrophobia)
        return result.final_output

class Acrophobia50mx50mWorldGen(VRWorldGen):
    bridge_prompt="Generate a world that triggers acrophobia while crossing a bridge."
    mountain_prompt="Generate a world that triggers acrophobia on the summit of a mountain."
    skyscraper_prompt="Generate a world that triggers acrophobia on a tall skyscraper."
    building_prompt="Generate a world that triggers acrophobia on a medium-sized building - not too scary."
    roof_prompt="Generate a world that triggers a very sensitive acrophobia by placing a player on the roof of a low house/building."
    platform_prompt="Generate a world that triggers a very sensitive acrophobia by placing a player on a platform."
    
    bridge_regime_prompt="Generate multiple stages of worlds that trigger acrophobia while crossing a bridge. Have the stages get progressively harder. Let there be three stages and let the heights of the bridges in each stage progress as 2m, 5m, 10m above ground or sea level."

    def __init__(self, asset_project_path: str="acrophobia_v1", restricted: bool = False, scene_name: str | None = None):
        restriction = f"These are the assets the system is restricted to:\n{[key.split('/')[-1] for key in list(instruments.asset_catalog.keys())]}" if restricted else ""
        if scene_name is None:
            scene_name = f"acro_50_{MODEL}_{random.randint(100, 999)}"
        
        asset_project_path = Path(ASSET_LIB_PATH) / asset_project_path
        instruments.asset_project = asset_project_path
        super().__init__(asset_project_path, scene_name, restriction)
        self.conductor.instructions = Conductor.acrophobia_v1[MODEL]
        self.conductor.tools.remove(createGround)
        self.conductor.tools.remove(populateHorizon)
        self.conductor.tools.extend([create50mx50mGround])

    async def get_prompt(self):
        print("Getting prompt from patient...")
        result = await Runner.run(self.patient, self.patient.acrophobia)
        return result.final_output   
    
    
        

