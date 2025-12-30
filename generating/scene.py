import sys
import uuid
from pathlib import Path
import tools.unity.structural_changes as structural_changes

from typing import List
from logger import log

from utils.paths import RelativePath, AssetsRelativePathStr

class Scene:
    pass

class UnityScene(Scene):
    unity_file: structural_changes.UnityFile
    name: str
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.unity_file = structural_changes.UnityFile()

    def add_skybox(self, skybox_name, skybox_path):
        self.unity_file.set_skybox(skybox_name, skybox_path)

    def add_sun(self, length_of_day, time_of_day, sun_brightness):
        print({"length_of_day":length_of_day, "time_of_day":time_of_day, "sun_brightness":sun_brightness})
        self.unity_file.set_sun(length_of_day, time_of_day, sun_brightness)

    def add_sound(self, sound_name, sound_path):
        self.unity_file.add_sound(sound_name, sound_path)

    def set_vr_player(self, location, rotation):
        self.unity_file.set_vr_player(location, rotation)
      
    def add_prefab(self, name, prefab_path, location: dict, rotation):
        #if self.unity_file.remove_prefab_instance_if_exists(name):
        #    print(f"Removed existing object {name} from YAML")
        self.unity_file.add_prefab_instance(name, prefab_path, location, rotation)

    def add_orphan_prefab(self, name, prefab_path, location, rotation):
        log(f"Writing meta (from world) for {name}")
        guid = uuid.uuid4().hex

        rel_path = self.get_asset(name)
        log(f"Writing meta for {rel_path}")
        structural_changes.write_obj_meta(rel_path, guid)
        log(f"Done writing meta for {rel_path}")
        self.unity_file.add_orphan_prefab_instance(name, prefab_path, guid, location, rotation)

    def add_ground(self, ground_name, ground_path, transform={"x":0.0, "y":0.0, "z":0.0}, rotation={"x":0.0, "y":0.0, "z":0.0}):
        log("Adding ground...")
        
        guid = uuid.uuid4().hex
        log("Geting proposed asset...")
        ground_proposition = self.get_asset(ground_name)
        log(f"PRoposition:  {ground_proposition}")
        ground_OBJ_rel_path = ground_proposition["Ground"]
        log(f"GUID: {guid}")
        log(f"Writing meta file to relative path:  {ground_OBJ_rel_path}")
        structural_changes.write_obj_meta(ground_OBJ_rel_path, guid)
        log(f"Done writing META {ground_OBJ_rel_path}.")
        log(f"Adding prefab instance to YAML")
        self.unity_file.add_ground_prefab_instance(ground_name, ground_path, guid, transform)
        log(f"Done adding prefab instance")
    
    def commit_scene(self, destination: Path):
        self.unity_file.to_unity_yaml(destination)
