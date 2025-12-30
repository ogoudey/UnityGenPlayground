import sys
import uuid
from pathlib import Path
import tools.unity.yamling as yamling

from typing import List
from logger import log

from utils.paths import RelativePath, AssetsRelativePathStr

class Scene:
    pass

class UnityScene(Scene):
    unity_file: yamling.UnityFile
    name: str
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.unity_file = yamling.UnityFile()

    def add_skybox(self, skybox_name):
        self.unity_file.set_skybox(skybox_name)

    def add_sun(self, length_of_day, time_of_day, sun_brightness):
        print({"length_of_day":length_of_day, "time_of_day":time_of_day, "sun_brightness":sun_brightness})
        self.unity_file.set_sun(length_of_day, time_of_day, sun_brightness)

    def add_sound(self, sound_name):
        self.unity_file.add_sound(sound_name)

    def set_vr_player(self, location, rotation):
        self.unity_file.set_vr_player(location, rotation)
      
    def add_prefab(self, name, location: dict, rotation):
        #if self.unity_file.remove_prefab_instance_if_exists(name):
        #    print(f"Removed existing object {name} from YAML")
        self.unity_file.add_prefab_instance(name, location, rotation)

    def add_orphan_prefab(self, name, location, rotation):
        log(f"Writing meta (from world) for {name}")
        guid = uuid.uuid4().hex

        rel_path = self.get_asset(name)
        log(f"Writing meta for {rel_path}")
        yamling.write_obj_meta(rel_path, guid)
        log(f"Done writing meta for {rel_path}")
        self.unity_file.add_orphan_prefab_instance(name, guid, location, rotation)

    def add_ground(self, ground_name, transform={"x":0.0, "y":0.0, "z":0.0}, rotation={"x":0.0, "y":0.0, "z":0.0}):
        log("Adding ground...")
        if not self.ground_name == "":
            if self.unity_file.remove_prefab_instance_if_exists(self.ground_name):
                print(f"Removed existing ground {self.ground_name} from YAML")
            else:
                print("Ground exists in YAML - couldn't be removed.")
        guid = uuid.uuid4().hex
        log("Geting proposed asset...")
        ground_proposition = self.get_asset(ground_name)
        log(f"PRoposition:  {ground_proposition}")
        ground_OBJ_rel_path = ground_proposition["Ground"]
        log(f"GUID: {guid}")
        log(f"Writing meta file to relative path:  {ground_OBJ_rel_path}")
        yamling.write_obj_meta(ground_OBJ_rel_path, guid)
        log(f"Done writing META {ground_OBJ_rel_path}.")
        log(f"Adding prefab instance to YAML")
        self.unity_file.add_ground_prefab_instance(ground_name, guid, transform)
        log(f"Done adding prefab instance")