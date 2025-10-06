from pathlib import Path
import os
import random
from agents import Runner
import coordinator as agents

import assets
import synopsis_generator
from enrichment import Phobos
from coordinator import Checker, Reformer, Coordinator
from tools import get_ground_matrix, planObject, placeObject, place_vr_human_player, planSkybox, placeSkybox, planandplaceGround, get_contact_points, planandplaceSun

from scene import World

MODEL = (os.getenv("MODEL") or "o3-mini").strip() or "o3-mini"
ASSET_LIB_PATH = (os.getenv("ASSET_LIB_PATH") or "../Resources/Asset Projects").strip() or "../Resources/Asset Projects"  

class WorldGen:
    
    def __init__(self, asset_project_path: Path = None, scene_name: str = None, preexisting_world: str = None, restriction: str = None):
        self.asset_project_path = asset_project_path
        
        
        if preexisting_world:
            # load preexising world or something - not really used in Phobia subclass
            pass
        
        if not scene_name:
            scene_name = f"scene_{MODEL}_{random.randint(100, 999)}"
        agents.tools.unity = World(scene_name)
            
        self.coordinator = Coordinator() # default
        if restriction:
            self.coordinator.restriction = restriction

    async def load(self):
        agents.tools.assets_info = assets.load(self.asset_project_path)
        agents.tools.synopses = await synopsis_generator.load(agents.tools.assets_info)
        agents.tools.material_leaves =  assets.get_found(".mat", folder=self.asset_project_path)
        agents.tools.screened_material_leaves = assets.get_found(file_type=".mat", folder=self.asset_project_path / "Assets/Ground Materials")
        
    
    async def run(self, prompt):
        print("\n>>>>>> ", prompt)
        await Runner.run(self.coordinator, prompt, max_turns=20)
        agents.tools.unity.done_and_write()

class PhobiaWorldGen(WorldGen):
    
    def __init__(self, asset_project_path: Path = None, scene_name: str = None, restriction: str = None):
        super().__init__(asset_project_path, scene_name, None, restriction)
        self.coordinator.tools.extend([place_vr_human_player, planSkybox, placeSkybox, planandplaceSun])
        self.coordinator.instructions = Coordinator.phobia_v1[MODEL]
        self.patient = Phobos() 

    async def get_prompt(self):
        print("Getting prompt from patient...")
        result = await Runner.run(self.patient, self.patient.acrophobia)
        return result.final_output
        
class AcrophobiaWorldGen(PhobiaWorldGen):
    ideal_prompt="Generate a world that triggers acrophobia while crossing a bridge."
    def __init__(self, restricted: bool = False):
        asset_project_path = Path(ASSET_LIB_PATH) / "Acrophobia"
        
        restriction = f"These are the assets the system is restricted to:\n{[key.split('/')[-1] for key in list(agents.tools.assets_info.keys())]}"
        super().__init__(asset_project_path, f"acro_{MODEL}_{random.randint(100, 999)}", restriction)
        self.coordinator.instructions = Coordinator.acrophobia_v1[MODEL]
        
        

