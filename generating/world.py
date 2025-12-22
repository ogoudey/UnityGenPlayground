#############################################################################
#
#   Module for the API-like thing that the tools use. Interacts with the class stands for the unity file. Also stores propositions of objects (objects not yet positioned).
#
#############################################################################


import sys
import uuid
from pathlib import Path
import tools.unity.yamling as yamling

from typing import List
from logger import log

from utils.paths import RelativePath, AssetsRelativePathStr
    

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
    scene_name:str
    def __init__(self, scene_name):
        self.scene_name = scene_name
        self.objects = []
        self.proposed_objects: Propositions = Propositions()
        self.contact_points = dict()
        pass

        
class UnityScene(World):
    """ Provides the "API" for the tools """
    unity_file: yamling.UnityFile
    ground_name: str
    ground_matrix: List[List[float]]
    ground_scale: float
    current_texture: str

    def __init__(self, scene_name:str | None = None):
        super().__init__(scene_name)
        self.unity_file = yamling.UnityFile()
        self.ground_name = ""
        self.ground_matrix = []
        self.ground_scale = 5.0
        self.texture = ""

    def propose_object(self, name: str, asset: RelativePath | dict[str, RelativePath], scene_name_for_logging):
        log(f"Proposing {name} as {asset}", scene_name_for_logging)
        name, asset = self.proposed_objects.add(name, asset)
        log(f"Proposed {name} as {asset}", scene_name_for_logging)
        return name, asset

    def get_asset(self, name: str) -> RelativePath | dict:
        return self.proposed_objects[name]

    def get_pathstr_relative_to_asset_project(self, name: str, asset_project_path: Path) -> str:
        rel_path: RelativePath = self.get_asset(name)
        log(f"Got {rel_path} from proposed objects.", self.scene_name)
        relative_path = rel_path.path
        log(f"Converting {rel_path.path} to Path {relative_path}", self.scene_name)
        assets_relative_path = relative_path.relative_to(asset_project_path)
        log(f"Converted relative Path to a Path relative to {asset_project_path.name}", self.scene_name)
        return assets_relative_path.as_posix()

    
    def add_skybox(self, skybox_name):
        self.unity_file.set_skybox(skybox_name)

     
    def add_sun(self, length_of_day, time_of_day, sun_brightness):
        print({"length_of_day":length_of_day, "time_of_day":time_of_day, "sun_brightness":sun_brightness})
        self.unity_file.set_sun(length_of_day, time_of_day, sun_brightness)

    
    def add_sound(self, sound_name):
        self.unity_file.add_sound(sound_name)

    
    def set_vr_player(self, location, rotation):
        self.unity_file.set_vr_player(location, rotation, self.scene_name)

           
    def add_prefab(self, name, location: dict, rotation):
        #if self.unity_file.remove_prefab_instance_if_exists(name):
        #    print(f"Removed existing object {name} from YAML")
        self.unity_file.add_prefab_instance(name, location, rotation)

    
    def add_orphan_prefab(self, name, location, rotation):
        log(f"Writing meta (from world) for {name}", self.scene_name)
        guid = uuid.uuid4().hex

        rel_path = self.get_asset(name)
        log(f"Writing meta for {rel_path}", self.scene_name)
        yamling.write_obj_meta(rel_path, guid)
        log(f"Done writing meta for {rel_path}", self.scene_name)
        self.unity_file.add_orphan_prefab_instance(name, guid, location, rotation, self.scene_name)

    
    def add_ground(self, ground_name, transform={"x":0.0, "y":0.0, "z":0.0}, rotation={"x":0.0, "y":0.0, "z":0.0}):
        log("Adding ground...", self.scene_name)
        if not self.ground_name == "":
            if self.unity_file.remove_prefab_instance_if_exists(self.ground_name):
                print(f"Removed existing ground {self.ground_name} from YAML")
            else:
                print("Ground exists in YAML - couldn't be removed.")
        guid = uuid.uuid4().hex
        log("Geting proposed asset...", self.scene_name)
        ground_proposition = self.get_asset(ground_name)
        log(f"PRoposition:  {ground_proposition}", self.scene_name)
        ground_OBJ_rel_path = ground_proposition["Ground"]
        log(f"GUID: {guid}", self.scene_name)
        log(f"Writing meta file to relative path:  {ground_OBJ_rel_path}", self.scene_name)
        yamling.write_obj_meta(ground_OBJ_rel_path, guid, self.scene_name)
        log(f"Done writing META {ground_OBJ_rel_path}.", self.scene_name)
        log(f"Adding prefab instance to YAML", self.scene_name)
        self.unity_file.add_ground_prefab_instance(ground_name, guid, transform, self.scene_name)
        log(f"Done adding prefab instance", self.scene_name)
        self.ground_name = ground_name

    def add_data(self, object_data):
        self.objects.append(object_data)

        
    def done_and_write(self, path_to_write: Path): 
        log(f"{len(self.objects)} objects generated.", self.scene_name)
        if path_to_write.exists():
            return self.unity_file.to_unity_yaml(path_to_write)
        else:
            log(f"Path {path_to_write} does not exist!", self.scene_name)
            raise Exception(f"Path {path_to_write} does not exist!")