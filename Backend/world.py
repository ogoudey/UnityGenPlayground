import uuid
from pathlib import Path
import yamling
from subagents import RelativePath, AssetsRelativePathStr
from typing import List
from logger import log

class World:
    scene_name:str
    def __init__(self):
        pass
    def propose_object(self, name, asset):
        print("Propose object called on underspecified world")
        return name, asset
    def get_path_relative_to_asset_project(self, name, asset_project_path):
        return AssetsRelativePathStr()
        
        
class UnityWorld(World):
    
    ground_matrix: List[List[float]]
    current_texture: str
    ground_scale: float

    def __init__(self, scene_name:str | None = None):
        super().__init__()
        self.unity_file = yamling.UnityFile()
        self.ground_matrix = []
        self.ground_scale = 5.0
        self.current_texture = ""
        self.contact_points = dict()
        self.objects = []
        self.ground = None
        if scene_name is not None:
            self.scene_name = scene_name

    def propose_object(self, name: str, path_str: RelativePath | dict[str, RelativePath]):
        return self.unity_file.propose_object(name, path_str)

    def get_pathstr_relative_to_asset_project(self, name: str, asset_project_path: Path) -> str:
        rel_path: RelativePath = self.unity_file.get_asset(name)
        log(f"Got {rel_path} from proposed objects.", self.scene_name)
        print(f"(propositions?)")
        relative_path = rel_path.path
        log(f"Converting {rel_path.path} to Path {relative_path}", self.scene_name)
        assets_relative_path = relative_path.relative_to(asset_project_path)
        log(f"Converted relative Path to a Path relative to {asset_project_path.name}", self.scene_name)
        print(f"Converted {relative_path} to {assets_relative_path}.")
        print(f"Converted {assets_relative_path} to {str(assets_relative_path)}.")
        return str(assets_relative_path)

    
    def add_skybox(self, skybox_name):
        self.unity_file.set_skybox(skybox_name)

     
    def add_sun(self, length_of_day, time_of_day, sun_brightness):
        print({"length_of_day":length_of_day, "time_of_day":time_of_day, "sun_brightness":sun_brightness})
        self.unity_file.set_sun(length_of_day, time_of_day, sun_brightness)

    
    def add_sound(self, sound_name):
        self.unity_file.add_sound(sound_name)

    
    def set_vr_player(self, location, rotation):
        self.unity_file.set_vr_player(location, rotation, self.scene_name)

           
    def add_prefab(self, name, location, rotation):
        #if self.unity_file.remove_prefab_instance_if_exists(name):
        #    print(f"Removed existing object {name} from YAML")
        self.unity_file.add_prefab_instance(name, location, rotation)

    
    def add_orphan_prefab(self, name, location, rotation):
        guid = uuid.uuid4().hex
        asset = self.unity_file.get_asset(name)
        yamling.write_obj_meta(asset, guid)
        self.unity_file.add_orphan_prefab_instance(name, guid, location, rotation)

    
    def add_ground(self, ground_name, transform={"x":0.0, "y":0.0, "z":0.0}, rotation={"x":0.0, "y":0.0, "z":0.0}):
        log("Adding ground...", self.scene_name)
        if self.ground:
            if self.unity_file.remove_prefab_instance_if_exists(self.ground):
                print(f"Removed existing ground {self.ground} from YAML")
            else:
                print("Ground exists in YAML - couldn't be removed.")
        guid = uuid.uuid4().hex
        log("Geting proposed asset...", self.scene_name)
        ground_proposition = self.unity_file.get_asset(ground_name)
        log(f"PRoposition:  {ground_proposition}", self.scene_name)
        ground_OBJ_rel_path = ground_proposition["Ground"]
        log(f"relative path:  {ground_OBJ_rel_path}", self.scene_name)
        print("Groudn OBJ rel path:", ground_OBJ_rel_path)
        log(f"Writing meta file to relative path:  {ground_OBJ_rel_path}", self.scene_name)
        yamling.write_obj_meta(ground_OBJ_rel_path, guid)
        log(f"Done writing META {ground_OBJ_rel_path}.", self.scene_name)
        log(f"Adding prefab instance to YAML", self.scene_name)
        self.unity_file.add_ground_prefab_instance(ground_name, guid, transform, self.scene_name)
        log(f"Done adding prefab instance", self.scene_name)
        self.ground = ground_name

    def add_data(self, object_data):
        self.objects.append(object_data)

        
    def done_and_write(self, file_name=None): # filename is always used
        print("\nObjects:\n", self.objects)
        log(f"{len(self.objects)} generated.", self.scene_name)
        if not file_name:
            file_name = "Unknown"
        return self.unity_file.to_unity_yaml(file_name)