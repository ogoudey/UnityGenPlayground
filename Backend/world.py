import uuid
from pathlib import Path
import yamling
from subagents import AssetPath

def unity(func):
    func.unity = True  # attach metadata
    func.writes_to_YAML_object = True
    return func

class World:
    def __init__(self, name:str):
        self.name = name
class UnityWorld(World):
    def __init__(self, name:str):
        super().__init__(name)
        self.unity_file = yamling.UnityFile()
        self.ground_matrix = []
        self.ground_scale = 5.0
        self.current_texture = ""
        self.contact_points = dict()
        self.objects = []
        self.ground = None

    def propose_object(self, name: str, asset_path: AssetPath | dict[str, AssetPath]):
        self.unity_file.propose_object(name, asset_path)

    def get_asset_path(self, name: str, asset_project_path: Path) -> AssetPath:
        asset_path = self.unity_file.get_asset_path(name)
        path = Path(asset_path)
        print(path)      
        relativized_path = path.relative_to(asset_project_path)
        print(relativized_path)
        return AssetPath(relativized_path)

    @unity
    def add_skybox(self, skybox_name):
        self.unity_file.set_skybox(skybox_name)

    @unity 
    def add_sun(self, length_of_day, time_of_day, sun_brightness):
        print({"length_of_day":length_of_day, "time_of_day":time_of_day, "sun_brightness":sun_brightness})
        self.unity_file.set_sun(length_of_day, time_of_day, sun_brightness)

    @unity
    def add_sound(self, sound_name):
        self.unity_file.add_sound(sound_name)

    @unity
    def set_vr_player(self, location, rotation):\
        self.unity_file.set_vr_player(location, rotation)

    @unity       
    def add_prefab(self, name, location, rotation):
        #if self.unity_file.remove_prefab_instance_if_exists(name):
        #    print(f"Removed existing object {name} from YAML")
        self.unity_file.add_prefab_instance(name, location, rotation)

    @unity
    def add_orphan_prefab(self, name, location, rotation):
        guid = uuid.uuid4().hex
        yamling.write_obj_meta(Path(self.unity_file.proposed_objects[name]), guid)     
        self.unity_file.add_orphan_prefab_instance(name, guid, location, rotation)

    @unity
    def add_ground(self, ground_name, transform={"x":0.0, "y":0.0, "z":0.0}, rotation={"x":0.0, "y":0.0, "z":0.0}):
        if self.ground:
            if self.unity_file.remove_prefab_instance_if_exists(self.ground):
                print(f"Removed existing ground {self.ground} from YAML")
            else:
                print("Ground exists in YAML - couldn't be removed.")
        guid = uuid.uuid4().hex
        print("before writing meta")
        posix_path: AssetPath = self.unity_file.proposed_objects[ground_name]["Ground"]
        yamling.write_obj_meta(Path(posix_path), guid)
        print("meta written")
        self.unity_file.add_ground_prefab_instance(ground_name, guid, transform)
        print("back from add_gnd_prefab_instance")
        self.ground = ground_name

    def add_data(self, object_data):
        self.objects.append(object_data)

        
    def done_and_write(self, file_name=None):
        print("\nObjects:\n", self.objects)
        if not file_name:
            file_name = self.name
        return self.unity_file.to_unity_yaml(file_name)