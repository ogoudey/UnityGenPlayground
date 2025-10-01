import uuid

import yamling


class UnityFile:
    def __init__(self, name="testingtesting123"):
        self.name = name
        self.yaml = yamling.YAML()
        
        self.ground_matrix = []
        self.contact_points = dict()

    def add_skybox(self, skybox_name):
        self.yaml.set_skybox(skybox_name)
        
    def add_sun(self, length_of_day, time_of_day, sun_brightness):
        print({"length_of_day":length_of_day, "time_of_day":time_of_day, "sun_brightness":sun_brightness})
        self.yaml.set_sun(length_of_day, time_of_day, sun_brightness)
      
    def set_vr_player(self, location, rotation):\
        self.yaml.set_vr_player(location, rotation)
            
    def add_prefab(self, name, location, rotation):
        #if self.yaml.remove_prefab_instance_if_exists(name):
        #    print(f"Removed existing object {name} from YAML")
        self.yaml.add_prefab_instance(name, location, rotation)
         
              
    def add_ground(self, ground_name, transform={"x":0.0, "y":0.0, "z":0.0}):
        if self.yaml.remove_prefab_instance_if_exists(ground_name):
            print(f"Removed existing ground {ground_name} from YAML")
        guid = uuid.uuid4().hex
        yamling.write_obj_meta(self.yaml.used_assets[ground_name]["Ground"], guid)
        self.yaml.add_ground_prefab_instance(ground_name, guid, transform)
        
        
    def done_and_write(self, file_name=None):
        if not file_name:
            file_name = self.name
        self.yaml.to_unity_yaml(file_name)
