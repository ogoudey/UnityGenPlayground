from pathlib import Path
import os
import random
from agents import Runner
from agents.extensions.visualization import draw_graph
import coordinator as agents
import time

import assets
import synopsis_generator
from enrichment import Phobos
from coordinator import Checker, Reformer, Coordinator
from tools import getGroundMatrix, proposeObject, positionObject, positionVRHumanPlayer, createSkybox, createGround, getContactPoints, createSun, populateHorizon, createSound, create50mx50mGround

from logger import log

from supertools import CoordinatorRunner

from scene import World

MODEL = (os.getenv("MODEL") or "o3-mini").strip() or "o3-mini"
ASSET_LIB_PATH = (os.getenv("ASSET_LIB_PATH") or "../Resources/Asset Projects").strip() or "../Resources/Asset Projects"
DRAWING = True
if DRAWING:
    print(f"Will draw a graph for coordinator...")
class WorldGen:
    
    def __init__(self, asset_project_path: Path = None, scene_name: str = None, preexisting_world: str = None, restriction: str = None):
        self.asset_project_path = asset_project_path
        if asset_project_path and asset_project_path.exists():
            print(f"Asset Project is \033[1m\033[36m{asset_project_path}\033[0m")
        else:
            if asset_project_path:
                print(f"Asset project with path {asset_project_path} does not exist.")
                raise FileNotFoundError(f"Asset project with path {asset_project_path} does not exist.")
            else:
                print("\033[1m\033[31mAsset project path does not exist or was not provided.\033[0m")
                raise FileNotFoundError("Asset project path does not exist or was not provided.")
        agents.tools.asset_project = asset_project_path
        
        if preexisting_world:
            # load preexising world or something - not really used in Phobia subclass
            pass
        
        if not scene_name:
            scene_name = f"scene_{MODEL}_{random.randint(100, 999)}"
        self.scene_name = scene_name
        agents.tools.unity = World(scene_name)
            
        self.coordinator = Coordinator() # default
        if restriction:
            self.coordinator.restriction = restriction

        self.coordinator_runner = CoordinatorRunner(run_coordinator_function=self.run) # default

    async def load(self):
        print("\n  ___Asset Catalog___")
        print("Catalog maps `path => object data`")
        agents.tools.asset_catalog = assets.load(self.asset_project_path)
        print("\n  ___Synopsis File___")
        print("Maps `synopsis of object data => asset path`")
        agents.tools.synopses = await synopsis_generator.load(agents.tools.asset_catalog)
        print("\n  ___Special Materials___")
        print("Curated collections of materials for special objects")
        agents.tools.skybox_material_leaves =  assets.get_found(".mat", asset_projects=ASSET_LIB_PATH, asset_project_path=str(self.asset_project_path / "Assets/Skybox Materials"))
        agents.tools.ground_material_leaves = assets.get_found(".mat", asset_projects=ASSET_LIB_PATH, asset_project_path=str(self.asset_project_path / "Assets/Ground Materials"))
        agents.tools.sound_leaves = assets.get_found(".mp3", asset_projects=ASSET_LIB_PATH, asset_project_path=str(self.asset_project_path / "Assets/Sounds"))
        
    
    async def run(self, prompt):
        """
            prompt: prompt for Coordinator agent to generate world. Example: Generate a fish tank.
        """
        print("\n>>>>>> ", prompt, "\n")
        result = await Runner.run(self.coordinator, prompt, max_turns=20)
        path = str(self.asset_project_path / "Assets" / "Scenes" / self.scene_name) # should stringify later?
        scene_path = agents.tools.unity.done_and_write(path)
        print(f"Scene @ {scene_path}")
        print(f"Coordinator response: \n{result.final_output}")
        log(result.final_output)
        log(f"World generated at {scene_path}", type="bold")

        if DRAWING:
            draw_graph(self.coordinator, filename="coordinator_graph")
        return path


    async def regime(self, regime_prompt):
        log("Starting regime")

        print("\n>>>>>> ", regime_prompt, "\n")
        result = await Runner.run(self.coordinator_runner, regime_prompt)
        print(f"Coordinator manager response: \n{result.final_output}")
        log(result.final_output)
        log("Done")
        

class VRWorldGen(WorldGen):
    
    def __init__(self, asset_project_path: Path = None, scene_name: str = None, restriction: str = None):
        super().__init__(asset_project_path, scene_name, None, restriction)
        agents.tools.asset_project = asset_project_path
        self.coordinator.tools.extend([positionVRHumanPlayer, createGround, createSkybox, createSun, createSound, populateHorizon])
        self.coordinator.instructions = Coordinator.phobia_v1[MODEL]
        self.patient = Phobos() 

    
        
class AcrophobiaWorldGen(VRWorldGen):
    bridge_prompt="Generate a world that triggers acrophobia while crossing a bridge."
    mountain_prompt="Generate a world that triggers acrophobia on the summit of a mountain."
    skyscraper_prompt="Generate a world that triggers acrophobia on a tall skyscraper."
    building_prompt="Generate a world that triggers acrophobia on a medium-sized building - not too scary."
    roof_prompt="Generate a world that triggers a very sensitive acrophobia by placing a player on the roof of a low house/building."
    platform_prompt="Generate a world that triggers a very sensitive acrophobia by placing a player on a platform."
    
    bridge_regime_prompt="Generate multiple stages of worlds that trigger acrophobia while crossing a bridge. Have the stages get progressively harder. Let there be three stages and let the heights of the bridges in each stage progress as 2m, 5m, 10m above ground or sea level."

    def __init__(self, asset_project_path: str="acrophobia_u5", restricted: bool = False):
        asset_project_path = Path(ASSET_LIB_PATH) / asset_project_path
        agents.tools.asset_project = asset_project_path
        restriction = f"These are the assets the system is restricted to:\n{[key.split('/')[-1] for key in list(agents.tools.asset_catalog.keys())]}" if restricted else ""
        super().__init__(asset_project_path, f"acro_{MODEL}_{random.randint(100, 999)}", restriction)
        self.coordinator.instructions = Coordinator.acrophobia_v1[MODEL]

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

    def __init__(self, asset_project_path: str="acrophobia_v1", restricted: bool = False):
        asset_project_path = Path(ASSET_LIB_PATH) / asset_project_path
        agents.tools.asset_project = asset_project_path
        restriction = f"These are the assets the system is restricted to:\n{[key.split('/')[-1] for key in list(agents.tools.asset_catalog.keys())]}" if restricted else ""
        super().__init__(asset_project_path, f"acro_50_{MODEL}_{random.randint(100, 999)}", restriction)
        self.coordinator.instructions = Coordinator.acrophobia_v1[MODEL]
        self.coordinator.tools.remove(createGround)
        self.coordinator.tools.remove(populateHorizon)
        self.coordinator.tools.extend([create50mx50mGround])

    async def get_prompt(self):
        print("Getting prompt from patient...")
        result = await Runner.run(self.patient, self.patient.acrophobia)
        return result.final_output   
    
    
        

