from pathlib import Path
import os
import random
from agents import Runner
from agents.extensions.visualization import draw_graph
from orchestra import instruments
import time
from typing import Any
import assets
import synopsis_generator
from enrichment import Phobos
from orchestra import Checker, Reformer, Conductor
from tools import getGroundMatrix, proposeObject, positionObject, positionVRHumanPlayer, createSkybox, createGround, getContactPoints, createSun, populateHorizon, createSound, create50mx50mGround

from logger import log

from supertools import ConductorRunner

from world import UnityWorld



MODEL = (os.getenv("MODEL") or "o3-mini").strip() or "o3-mini"
ASSET_PROJECTS: Path = Path("../Resources/Asset Projects")

DRAWING = False
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
    def __init__(self, asset_project_name: str, scene_name: str, preexisting_world: Any = None, restriction: str | None = None):
        super().__init__(preexisting_world)
        self.asset_project_path = ASSET_PROJECTS / Path(asset_project_name)
        instruments.asset_project = self.asset_project_path

        if self.asset_project_path.exists():
            print(f"Asset Project is \033[1m\033[36m{self.asset_project_path}\033[0m")
        else:
            if self.asset_project_path:
                print(f"Asset project with path {self.asset_project_path} does not exist.")
                raise FileNotFoundError(f"Asset project with path {self.asset_project_path} does not exist.")
            else:
                print("\033[1m\033[31mAsset project path does not exist or was not provided.\033[0m")
                raise FileNotFoundError("Asset project path does not exist or was not provided.")
        instruments.asset_project = self.asset_project_path
        if not scene_name:
            print(f"Scene name {scene_name} not given!")
            scene_name = f"scene_{MODEL}_{random.randint(100, 999)}"
        self.scene_name = scene_name
        instruments.world = UnityWorld(scene_name)   
        self.conductor = Conductor()
        if restriction:
            self.conductor.restriction = restriction
        self.conductor_runner = ConductorRunner(run_conductor_function=self.run)

    async def load(self):
        print("\n  ___Asset Catalog___")
        log("Catalog mapping local paths to annotations.", self.scene_name)
        instruments.asset_catalog = assets.load(self.asset_project_path, self.scene_name)
        print("\n  ___Synopsis File___")
        log("Synopses of annotations mapping to local paths.", self.scene_name)
        instruments.synopses = await synopsis_generator.load(instruments.asset_catalog,  self.scene_name)
        print("\n  ___Special Materials___")
        print("Curated collections of materials for special objects")
        instruments.skybox_material_leaves =  assets.get_found(".mat", asset_project_path=self.asset_project_path / "Assets"/"Skybox Materials",  scene_name_for_logging=self.scene_name)
        instruments.ground_material_leaves = assets.get_found(".mat", asset_project_path=self.asset_project_path / "Assets"/"Ground Materials",  scene_name_for_logging=self.scene_name)
        instruments.sound_leaves = assets.get_found(".mp3", asset_project_path=self.asset_project_path / "Assets" / "Sounds",  scene_name_for_logging=self.scene_name)
        
    
    async def run(self, prompt):
        """
            prompt: prompt for Conductor agent to generate world. Example: Generate a fish tank.
        """
        print("\n>>>>>> ", prompt, "\n")
        result = await Runner.run(self.conductor, prompt, max_turns=20)
        path = str(self.asset_project_path / "Assets" / "Generations" / self.scene_name) # should stringify later?
        print(f"Writing scene to {path}")
        scene_path = instruments.world.done_and_write(path)
        print(f"Scene @ {scene_path}")
        print(f"Conductor response: \n{result.final_output}")
        log(result.final_output, self.scene_name, wait_time=len(result.final_output)/10)

        if DRAWING:
            draw_graph(self.conductor, filename=f"{self.conductor.name}_graph")
        return path


    async def regime(self, regime_prompt):
        log("Starting regime", self.scene_name)

        print("\n>>>>>> ", regime_prompt, "\n")
        result = await Runner.run(self.conductor_runner, regime_prompt)
        print(f"Conductor manager response: \n{result.final_output}")
        log(result.final_output, self.scene_name)
        log("Done", self.scene_name)
        

class VRWorldGen(UnityWorldGen):
    
    def __init__(self, asset_project_name: str, scene_name: str, restriction: str):
        super().__init__(asset_project_name, scene_name, None, restriction)
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

    def __init__(self, asset_project_name: str="acrophobia_u5", scene_name: str | None = None, restricted: bool = False):
        if scene_name is None:
            scene_name = f"acro_50_{MODEL}_{random.randint(100, 999)}"
        restriction = f"These are the assets the system is restricted to:\n{[key.split('/')[-1] for key in list(instruments.asset_catalog.keys())]}" if restricted else ""
        super().__init__(asset_project_name, scene_name, restriction)
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

    def __init__(self, asset_project_name: str="acrophobia_v1", scene_name: str | None = None, restricted: bool = False):
        restriction = f"These are the assets the system is restricted to:\n{[key.split('/')[-1] for key in list(instruments.asset_catalog.keys())]}" if restricted else ""
        if scene_name is None:
            scene_name = f"acro_50_{MODEL}_{random.randint(100, 999)}"        
        super().__init__(asset_project_name, scene_name, restriction)
        self.conductor.instructions = Conductor.acrophobia_v1[MODEL]
        self.conductor.tools.remove(createGround)
        self.conductor.tools.remove(populateHorizon)
        self.conductor.tools.extend([create50mx50mGround])

    async def get_prompt(self):
        print("Getting prompt from patient...")
        result = await Runner.run(self.patient, self.patient.acrophobia)
        return result.final_output   
    
Generator_Class_from_Asset_Project_Name = {
    "acrophobia_v1": AcrophobiaWorldGen,
    "acrophobia_u5": AcrophobiaWorldGen,
    "Acrophobia_VR_AI": AcrophobiaWorldGen,
    "acrophobia_u5_v1": AcrophobiaWorldGen,
}

