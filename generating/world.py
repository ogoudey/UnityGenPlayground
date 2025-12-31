#############################################################################
#
#   Module for the API-like thing that the tools use. Interacts with the class stands for the unity file. Also stores propositions of objects (objects not yet positioned).
#
#############################################################################


import sys
import uuid
from pathlib import Path
import tools.unity.structural_changes as structural_changes

from typing import List
from logger import log

from utils.paths import RelativePath, AssetsRelativePathStr
    
from generating.scene import Scene, UnityScene
from generating.model import WorldModel, UnityWorldModel

from generating.write_utils import post_write, post_execute

class Propositions:
    """ A class that's storage for objects not yet placed in the scene. """
    propositions: dict[str, RelativePath | dict[str, RelativePath]]
    def __init__(self):
        self.propositions = dict()
        
    def add(self, name: str, proposition: RelativePath | dict):
        if isinstance(proposition, RelativePath):
            self.propositions[name] = proposition
            return name, proposition
        else:
            new_dict = dict()
            for pair in proposition.items():
                new_dict[pair[0]] = pair[1]
            proposition = new_dict
            self.propositions[name] = proposition
            return name, proposition

    def __getitem__(self, name: str):
        return self.propositions[name]
    
    def __contains__(self, name: str) -> bool:
        return name in self.propositions

class World:
    name:str
    def __init__(self, world_name):
        self.name = world_name
        self.proposed_objects: Propositions = Propositions()
        self.contact_points = dict()
        self.model = WorldModel()
    
    def add_data(self, object_data):
        self.model.update(object_data)

        
class UnityWorld(World):
    """
    Provides the "API" for the tools.
    Routes to scene (or other world components)
    Updates a Unity-style world model
    """
    scene: UnityScene
    ground_name: str
    ground_matrix: List[List[float]]
    ground_scale: float
    current_texture: str

    

    def __init__(self, world_name:str, scene: str):
        super().__init__(world_name)
        self.scene = UnityScene(scene)
        self.model = UnityWorldModel()
        self.ground_name = ""
        self.ground_matrix = []
        self.ground_scale = 5.0
        self.texture = ""

    def __repr__(self):
        return self.model.__repr__()

    def propose_object(self, name: str, asset: RelativePath | dict[str, RelativePath]):
        log(f"Proposing {name} as {asset}")
        name, asset = self.proposed_objects.add(name, asset)
        log(f"Proposed {name} as {asset}")
        return name, asset

    def get_asset(self, name: str) -> RelativePath | dict:
        return self.proposed_objects[name]

    def get_pathstr_relative_to_assets(self, name: str, assets: Path) -> str:
        rel_path: RelativePath = self.get_asset(name)
        log(f"Got {rel_path} from proposed objects.")
        relative_path = rel_path.path
        log(f"Converting {rel_path.path} to Path {relative_path}")
        assets_relative_path = relative_path.relative_to(assets)
        log(f"Converted relative Path to a Path relative to {assets.name}")
        return assets_relative_path.as_posix()

    def post(self):
        post_execute()

    def done_and_write(self, path_to_write: Path | str):
        self.scene.unity_file.reset()
        self.post()
        path = Path(path_to_write)
        if path.exists():
            return self.scene.commit_scene(path)
        else:
            print("Making parent directories")
            path.parent.mkdir(parents=True, exist_ok=True)
            return self.scene.commit_scene(path)
            raise Exception(f"Path {path} does not exist!")

    @post_write    
    def add_skybox(self, skybox_name):
        mat_path = self.proposed_objects[skybox_name].path
        self.scene.add_skybox(skybox_name, mat_path)

    @post_write
    def add_sun(self, length_of_day, time_of_day, sun_brightness):
        self.scene.add_sun(length_of_day, time_of_day, sun_brightness)

    @post_write
    def add_sound(self, sound_name):
        sound_path = self.proposed_objects[sound_name].path
        self.scene.add_sound(sound_name, sound_path)

    @post_write
    def set_vr_player(self, location, rotation):
        self.scene.set_vr_player(location, rotation)

    @post_write      
    def add_prefab(self, name, location: dict, rotation):
        prefab_path = self.proposed_objects[name].path
        self.scene.add_prefab(name, prefab_path, location, rotation)

    @post_write
    def add_orphan_prefab(self, name, location, rotation):
        prefab_path = self.proposed_objects[name].path
        self.scene.add_orphan_prefab(name, prefab_path, location, rotation)

    @post_write
    def add_ground(self, ground_name, transform={"x":0.0, "y":0.0, "z":0.0}, rotation={"x":0.0, "y":0.0, "z":0.0}):
        if not self.ground_name == "":
            if self.scene.unity_file.remove_prefab_instance_if_exists(self.ground_name):
                print(f"Removed existing ground {self.ground_name} from YAML")
            else:
                print("Ground exists in YAML - couldn't be removed.")
        proposal = self.proposed_objects[ground_name]
        self.scene.add_ground(ground_name, proposal, transform, rotation)
