import uuid

import yamling


class World:
    def __init__(self, name="testingtesting123"):
        self.name = name
        self.yaml = yamling.YAML()
        
        self.ground_matrix = []
        self.contact_points = dict()
        self.objects = []
        self.ground = None

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
        if self.ground:
            if self.yaml.remove_prefab_instance_if_exists(self.ground):
                print(f"Removed existing ground {self.ground} from YAML")
            else:
                print("Ground exists in YAML - couldn't be removed.")
        guid = uuid.uuid4().hex
        yamling.write_obj_meta(self.yaml.proposed_objects[ground_name]["Ground"], guid)
        self.yaml.add_ground_prefab_instance(ground_name, guid, transform)
        self.ground = ground_name

    def add_data(self, object_data):
        self.objects.append(object_data)

        
    def done_and_write(self, file_name=None):
        print("\nObjects:\n", self.objects)
        if not file_name:
            file_name = self.name
        self.yaml.to_unity_yaml(file_name)
