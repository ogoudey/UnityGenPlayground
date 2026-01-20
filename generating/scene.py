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

        log(f"Writing meta for {prefab_path}")
        structural_changes.write_obj_meta(prefab_path, guid)
        log(f"Done writing meta for {prefab_path}")
        self.unity_file.add_orphan_prefab_instance(name, prefab_path, guid, location, rotation)

    def add_agent(self, name, location, rotation):
        self.unity_file.add_agent_cylinder(name, location, rotation)

    def add_destination(self, name, transform):
        self.unity_file.add_tf(name, transform)

    def add_ground(self, ground_name, ground_path, transform={"x":0.0, "y":0.0, "z":0.0}, rotation={"x":0.0, "y":0.0, "z":0.0}):
        log("Adding ground...")
        
        guid = uuid.uuid4().hex
        log(f"Proposition:  {ground_path}")
        ground_OBJ_rel_path = ground_path["Ground"]
        log(f"GUID: {guid}")
        log(f"Writing meta file to relative path:  {ground_OBJ_rel_path}")
        structural_changes.write_obj_meta(ground_OBJ_rel_path, guid)
        log(f"Done writing META {ground_OBJ_rel_path}.")
        log(f"Adding prefab instance to YAML")
        self.unity_file.add_ground_prefab_instance(ground_name, ground_path, guid, transform)
        log(f"Done adding prefab instance")
    
    def commit_scene(self, destination: Path):
        self.unity_file.to_unity_yaml(destination)
