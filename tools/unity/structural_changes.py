#############################################################################
#
#   Module that contains the class that stands for the Unity scene file.
# 
#   Recommended test with 
#   `import structural_changes as s
#   x=s.UnityFile()
#   x.setup_keyboard_player() ...
#   x.
#   print(json.dumps(g, indent=2))
#
#############################################################################

from typing import List, Optional

import yaml as pyyaml

import math
import random
import os
import sys
from logger import log
from pathlib import Path

from utils.paths import RelativePath
from tools.unity.structural_utils import (
    load_structure,
    compose,
    node_to_python,
    get_doc,
    get_father_id_of_root_transform_of_prefab,
    set_ID,
    get_guid,
    euler_to_xyzw_quaternion,
    dict_to_yaml
)

UNITY_VERSION = (os.getenv("UNITY_VERSION") or "5").strip() or "5"
VR_HEADSET_TYPE = (os.getenv("VR_HEADSET_TYPE") or "Vive Focus 3").strip() or "Vive Focus 3"

print(f"\n[Unity scene file info] Generating world for Unity {UNITY_VERSION}.") # Use \033[1m\033[36mexport UNITY_VERSION='<5|6>'\033[0m")



class UnityFile:
    def __init__(self):
        if UNITY_VERSION == "6":
            scene_init_text = load_structure("sceneU6")
        elif UNITY_VERSION == "5":
            scene_init_text = load_structure("sceneU5")
        else:
            raise Exception("Must set Unity version.")
        self.reset

    def reset(self):
        # redund
        if UNITY_VERSION == "6":
            scene_init_text = load_structure("sceneU6")
        elif UNITY_VERSION == "5":
            scene_init_text = load_structure("sceneU5")
        else:
            raise Exception("Must set Unity version.")
        nodes = compose(scene_init_text)
        self.wrapped: List = [node_to_python(n) for n in nodes]
        self.placed_assets = dict()
        print(f"\t\tUnity YAML file cleared.")

    def set_sun(self, length_of_day: float, time_of_day: float, sun_brightness:float):
        rot = (time_of_day / length_of_day) * 360
        rotation = {"x": rot, "y": 0, "z": 0}
        quaternion = euler_to_xyzw_quaternion(rotation)

        sun_init_text = load_structure("directional_light")
        nodes = compose(sun_init_text)
        wrapped = [node_to_python(n) for n in nodes]
        for doc in wrapped:
            if "Transform" in doc.keys():
                if doc["Transform"]["m_Father"]["fileID"] == "0":
                    father_id = doc["anchor"]
                doc["m_LocalRotation"] = {"x": quaternion[0], "y": quaternion[1], "z": quaternion[2], "w": quaternion[3]}
            if "Light" in doc.keys():
                doc["m_Intensity"] = sun_brightness        
            # Edit parameters
            
            self.wrapped.append(doc)
        if not father_id:
            print("Failed to find root transform of Sun stuff:\n", wrapped)
            return
        if UNITY_VERSION == "5":
            print("Leaving before modifying sceneroots (Unity 5 thing).")
            return
        sceneroots = get_doc(self.wrapped, "SceneRoots")
        sceneroots["m_Roots"].append({"fileID": father_id})
        
    def set_skybox(self, name, mat_path):
        
        guid = get_guid(mat_path)
        try:
            render_settings = get_doc(self.wrapped, "RenderSettings")
            render_settings["m_SkyboxMaterial"] = {"fileID": "2100000", "guid": guid, "type": 2}
        except Exception:
            print("\rFailed to set skybox.")
            
    def add_ground_prefab_instance(self, name, proposal, metaguid, transform):
        log(f"Adding prefab instance {name}")
        prefab_init_text = load_structure("prefab_nav_surface")
        nodes = compose(prefab_init_text)
        wrapped = [node_to_python(n) for n in nodes]
        prefab = wrapped[0]
        log("Got init text for prefab")
        prefab, id_out = set_ID(prefab) # to random ID
        log("Set ID")
        try:
            log(f"Found proposed object {name} (keys: {list(proposal.keys())}")
            texture_path = proposal["Texture"].path
            log(f"Found proposal's path: {texture_path}")
            texture_metaguid = get_guid(texture_path)
        except Exception:
            log(f"Exception in getting texture GUID or getting proposal: {texture_path}")
            raise Exception(".meta lookup failed. File does not exist?")
        log("Making modifications...")
        modifications = prefab["PrefabInstance"]["m_Modification"]["m_Modifications"]
        for mod in modifications:
            if "target" in mod and "guid" in mod["target"]:
                mod["target"]["guid"] = metaguid
                if mod.get("propertyPath") == "m_Materials.Array.data[0]":
                    if not texture_path == "None":
                       mod["objectReference"]["guid"] = texture_metaguid
                elif mod.get("propertyPath") == "m_Name":
                    mod["target"]["fileID"] = "-8679921383154817045"
                    mod["target"]["value"] = name
                else:
                    mod["target"]["fileID"] = "-8679921383154817045"
                    if mod.get("propertyPath") == "m_LocalPosition.x":
                        mod["value"] = transform["x"]
                    if mod.get("propertyPath") == "m_LocalPosition.y":
                        mod["value"] = transform["y"]
                    if mod.get("propertyPath") == "m_LocalPosition.z":
                        mod["value"] = transform["z"]
                        
        for added_component in prefab["PrefabInstance"]["m_Modification"]["m_AddedComponents"]:
            added_component["targetCorrespondingSourceObject"]["guid"] = metaguid

        prefab["PrefabInstance"]["m_SourcePrefab"]["guid"] = metaguid

        game_object = wrapped[1]
        game_object["GameObject"]["m_PrefabInstance"]["fileID"] = id_out
        game_object["GameObject"]["m_CorrespondingSourceObject"]["guid"] = metaguid

        mesh_collider = wrapped[2]
        mesh_collider["MeshCollider"]["m_Mesh"]["guid"] = metaguid

        for wrap in wrapped:
            print(f"\tGround doc: {list(wrap.keys())[2:]}")
            self.wrapped.append(wrap)
        
        log("Modifications made, added to YAML.")
        if not UNITY_VERSION == "5":
            sceneroots = get_doc(self.wrapped, "SceneRoots")
            sceneroots["m_Roots"].append({"fileID": id_out})
            log("Scene roots modified.")        
    
    def remove_prefab_instance_if_exists(self, name):

        for doc in self.wrapped:
            if "PrefabInstance" in doc:
                for mod in doc["PrefabInstance"]["m_Modification"]["m_Modifications"]:
                    if mod.get("propertyPath") == "m_Name":
                        if name in mod["target"]["value"]: # A non-ideal way to detect if a ground is already in the YAML.
                            self.wrapped.remove(doc)
                            if UNITY_VERSION == "5":
                                return True
                            sceneroots = get_doc(self.wrapped, "SceneRoots")
                            prefab_id = doc["anchor"]
                            sceneroots["m_Roots"].remove({"fileID": prefab_id})
                            return True
        if UNITY_VERSION == "5":
            return False
        sceneroots = get_doc(self.wrapped, "SceneRoots")
        sceneroots["m_Roots"].remove({"fileID": prefab_id})
        return False

    def add_agent_cylinder(self, name, transform, rotation):
        # 1. Get relevant docs
        agent_init_text = load_structure("cylinder_nav_agent")
        composed = compose(agent_init_text)
        wrapped = [node_to_python(n) for n in composed]
        game_object_node = wrapped[0]
        transform_node = wrapped[4]
        # 2. Change name
        game_object_node["GameObject"]["m_Name"] = name
        # 3. Edit transform
        transform_node["Transform"]["m_LocalPosition"] = transform
        quaternion = euler_to_xyzw_quaternion(rotation)
        transform_node["Transform"]["m_LocalRotation"]["x"] = quaternion[0]
        transform_node["Transform"]["m_LocalRotation"]["y"] = quaternion[1]
        transform_node["Transform"]["m_LocalRotation"]["z"] = quaternion[2]
        transform_node["Transform"]["m_LocalRotation"]["w"] = quaternion[3]
        # 4. That's it
        for doc in wrapped: # could also use .extend(coll)
            self.wrapped.append(doc)

    def add_orphan_prefab_instance(self, name, prefab_path, metaguid, transform, rotation):
        """
        Creating a new asset. The scene needs a reference to an imported asset, so we manually import it, writing a .meta file.
        """
        prefab_init_text = load_structure("prefab")
        node = compose(prefab_init_text)[0]
        wrapped = node_to_python(node)
        wrapped, id_out = set_ID(wrapped) # to random ID
        
        try:
            
            print(f"Found {name} in proposed_objects w path {prefab_path}")
        except KeyError:
            print(name + " not in proposed_objects")
            raise KeyError

        self.placed_assets[name] = {"transform": transform, "rotation": rotation}

        quaternion = euler_to_xyzw_quaternion(rotation)

        modifications = wrapped["PrefabInstance"]["m_Modification"]["m_Modifications"]
        for mod in modifications:
            if "target" in mod and "guid" in mod["target"]:
                
                mod["target"]["guid"] = metaguid
                if mod.get("propertyPath") == "m_Name":
                    mod["target"]["value"] = name # Anything?
                elif mod.get("propertyPath") == "m_Materials.Array.data[0]":
                    mod["target"]["fileID"] = -7635826562936255635
                else:
                    mod["target"]["fileID"] = "-8679921383154817045"
                    if mod.get("propertyPath") == "m_LocalPosition.x":
                        mod["value"] = transform["x"]
                    if mod.get("propertyPath") == "m_LocalPosition.y":
                        mod["value"] = transform["y"]
                    if mod.get("propertyPath") == "m_LocalPosition.z":
                        mod["value"] = transform["z"]
                    if mod.get("propertyPath") == "m_LocalRotation.x":
                        mod["value"] = quaternion[0]
                    if mod.get("propertyPath") == "m_LocalRotation.y":
                        mod["value"] = quaternion[1]
                    if mod.get("propertyPath") == "m_LocalRotation.z":
                        mod["value"] = quaternion[2]
                    if mod.get("propertyPath") == "m_LocalRotation.w":
                        mod["value"] = quaternion[3]  
        wrapped["PrefabInstance"]["m_SourcePrefab"]["guid"] = metaguid
        self.wrapped.append(wrapped)
        if UNITY_VERSION == "5":
            return
        sceneroots = get_doc(self.wrapped, "SceneRoots")
        sceneroots["m_Roots"].append({"fileID": id_out})        

    def add_sound(self, name, sound_path):
        sound_init_text = load_structure("sound")
        nodes = compose(sound_init_text)
        sound_game_object = node_to_python(nodes[0])
        audio_source = node_to_python(nodes[1])
        sound_transform = node_to_python(nodes[2])
        try:
            
            print(f"Found {name} in proposed_objects w path {sound_path}")
        except KeyError:
            print(name + " not in proposed_objects")
            raise KeyError
        sound_game_object_id = str(random.randint(100000000, 999999999))
        sound_game_object["anchor"] = sound_game_object_id
        audio_source_id = str(random.randint(100000000, 999999999))
        transform_id = str(random.randint(100000000, 999999999))
        components = sound_game_object["GameObject"]["m_Component"]
        components.append(f"component: {{fileID: {transform_id}}}")
        components.append(f"component: {{fileID: {audio_source_id}}}")
        sound_game_object["GameObject"]["m_Name"] = name
        audio_source["anchor"] = audio_source_id
        metaguid = get_guid(sound_path)
        sound_transform["anchor"] = transform_id
        sound_transform["Transform"]["m_GameObject"]["fileID"] = sound_game_object_id
        # change position if sound is spatialized
        if not UNITY_VERSION == "5":
            audio_source["AudioSource"]["m_Resource"]["guid"] = metaguid # no m_Resource in Unity 5
            sceneroots = get_doc(self.wrapped, "SceneRoots")
            sceneroots["m_Roots"].append({"fileID": transform_id})
        else: # Unity 5
            audio_source["AudioSource"]["m_audioClip"] = f"{{fileID: 8300000, guid: {metaguid}, type: 3}}"
        self.wrapped.append(sound_transform)
        self.wrapped.append(audio_source)
        self.wrapped.append(sound_game_object)

    def add_prefab_instance(self, name, prefab_path, transform: dict, rotation: dict):
        """
        A preimported asset. Must identify the .meta file.
        """
        prefab_init_text = load_structure("prefab")
        composed = compose(prefab_init_text)
        objects: str = node_to_python(composed[0])
        objects, id_out = set_ID(objects) # to random ID
        #log(f"{name} in {self.proposed_objects.assets}?")
        try:
            father_ID = get_father_id_of_root_transform_of_prefab(prefab_path)
        except Exception:
            raise FileNotFoundError(f"Could not find fatherID of root transform {prefab_path}")
        try:    
            guid = get_guid(prefab_path)
        except Exception:
            print(f"Could not get guid from .meta file: {prefab_path}.meta")
            raise FileNotFoundError(f"Could not get guid from .meta file: {prefab_path}.meta")
        self.placed_assets[name] = {"transform": transform, "rotation": rotation}
        scale = 1.0
        quaternion = euler_to_xyzw_quaternion(rotation)
        modifications = objects["PrefabInstance"]["m_Modification"]["m_Modifications"]
        x_position_has_been_changed = False # marker for whether the 
        #log("Making modifications to init_yaml")
        for mod in modifications:
            if "target" in mod and "guid" in mod["target"]:
                mod["target"]["guid"] = guid
                if mod.get("propertyPath") == "m_Name":
                    mod["target"]["fileID"] = father_ID
                    mod["target"]["value"] = name # Anything?
                elif mod.get("propertyPath") == "m_Materials.Array.data[0]":
                    mod["target"]["fileID"] = -7635826562936255635
                else:
                    mod["target"]["fileID"] = father_ID
                    if mod.get("propertyPath") == "m_LocalPosition.x":
                        mod["value"] = transform["x"]
                        #log(f"x position set to {transform['x']}")
                    if mod.get("propertyPath") == "m_LocalPosition.y":
                        mod["value"] = transform["y"]
                    if mod.get("propertyPath") == "m_LocalPosition.z":
                        mod["value"] = transform["z"]
                    if not scale == 1.0:
                        if mod.get("propertyPath") == "m_LocalScale.x":
                            mod["value"] = scale
                        if mod.get("propertyPath") == "m_LocalScale.z":
                            mod["value"] = scale
                    if mod.get("propertyPath") == "m_LocalRotation.x":
                        mod["value"] = quaternion[0]
                    if mod.get("propertyPath") == "m_LocalRotation.y":
                        mod["value"] = quaternion[1]
                    if mod.get("propertyPath") == "m_LocalRotation.z":
                        mod["value"] = quaternion[2]
                    if mod.get("propertyPath") == "m_LocalRotation.w":
                        mod["value"] = quaternion[3]  
        objects["PrefabInstance"]["m_SourcePrefab"]["guid"] = guid
        if not UNITY_VERSION == "5":
            sceneroots = get_doc(self.wrapped, "SceneRoots")
            sceneroots["m_Roots"].append({"fileID": id_out})
        self.wrapped.append(objects)
        return True
    
    def set_vr_player(self, transform: dict, rotation: dict):
        """
        Dispatches to the various configurations of VR player. Either:
          a. VIVECameraRig/SteamVR: sufficient for Unity 6(+)
          b. SteamVRUnityPlugin/SteamVR + VIVESR: for data collection. Needs Unity 2019 (what I often refer to as Unity 5) Must consider movement (hopefully through SteamVR)
          c. SteamVRUnityPlugin/SteamVR: w/o data collection, Unity 5.    # Not needed I guess...
        """
        dispatcher = {
                        "6": {
                            "Vive Pro 2": self.setup_VIVE,
                            "No VR": self.setup_keyboard_player,
                            "Vive Focus 3": self.setup_vive_focus
                            },
                        "5": {
                            "Vive Pro 2": self.setup_data_collection,
                            "No VR": self.setup_keyboard_player
                            }
                    }
        try:
            dispatch = dispatcher[UNITY_VERSION][VR_HEADSET_TYPE]
        except KeyError:
            print(f"Could not place VR player! No structure for {VR_HEADSET_TYPE} in Unity {UNITY_VERSION}:\n{dispatcher}")

        log(f"Unity version {UNITY_VERSION} with {VR_HEADSET_TYPE} headset maps to low-level function `{dispatch.__name__}`")
        dispatch(transform, rotation)

    def setup_keyboard_player(self, transform: dict, rotation: dict):
        player = load_structure("player")
        nodes = compose(player)
        coll = [node_to_python(n) for n in nodes]
        
        transform_node = coll[10]

        transform_node["Transform"]["m_LocalPosition"] = transform
        quaternion = euler_to_xyzw_quaternion(rotation)
        transform_node["Transform"]["m_LocalRotation"]["x"] = quaternion[0]
        transform_node["Transform"]["m_LocalRotation"]["y"] = quaternion[1]
        transform_node["Transform"]["m_LocalRotation"]["z"] = quaternion[2]
        transform_node["Transform"]["m_LocalRotation"]["w"] = quaternion[3]
        for doc in coll: # could also use .extend(coll)
            self.wrapped.append(doc)

    def setup_vive_focus(self, transform: dict, rotation: dict):
        raise NotImplementedError("OOps! Must get the init text from Hector.")
        nodes = compose(Vision_and_Data_Collection_init_text)
        collection = [node_to_python(n) for n in nodes]

        # get camera to set its orientation.
        collection_root = collection[6] # its one of the members of the prefab collection

        if collection_root is None:
            print("Cannot find [what the root is] prefab in init text (??)")
        quaternion = euler_to_xyzw_quaternion(rotation)

        modifications = collection_root["PrefabInstance"]["m_Modification"]["m_Modifications"]
        for mod in modifications:
            if "target" in mod and "guid" in mod["target"]:
                if mod.get("propertyPath") == "m_LocalPosition.x":
                    mod["value"] = transform["x"]
                if mod.get("propertyPath") == "m_LocalPosition.y":
                    mod["value"] = transform["y"]
                if mod.get("propertyPath") == "m_LocalPosition.z":
                    mod["value"] = transform["z"]
                if mod.get("propertyPath") == "m_LocalRotation.x":
                    mod["value"] = quaternion[0]
                if mod.get("propertyPath") == "m_LocalRotation.y":
                    mod["value"] = quaternion[1]
                if mod.get("propertyPath") == "m_LocalRotation.z":
                    mod["value"] = quaternion[2]
                if mod.get("propertyPath") == "m_LocalRotation.w":
                    mod["value"] = quaternion[3]

        # Append the edited collection
        for doc in collection: # could also use .extend(coll)
            self.wrapped.append(doc)

    def setup_data_collection(self, transform: dict, rotation: dict):
        SRanipal_and_SteamVR_setup_init_text = load_structure("sranipal_vr")
        nodes = compose(SRanipal_and_SteamVR_setup_init_text)
        coll = [node_to_python(n) for n in nodes]
        camera_rig = coll[5]

        if camera_rig is None:
            print("Cannot find [CameraRig] prefab in init text (??)")
        quaternion = euler_to_xyzw_quaternion(rotation)

        modifications = camera_rig["PrefabInstance"]["m_Modification"]["m_Modifications"]
        for mod in modifications:
            if "target" in mod and "guid" in mod["target"]:
                if mod.get("propertyPath") == "m_LocalPosition.x":
                    mod["value"] = transform["x"]
                if mod.get("propertyPath") == "m_LocalPosition.y":
                    mod["value"] = transform["y"]
                if mod.get("propertyPath") == "m_LocalPosition.z":
                    mod["value"] = transform["z"]
                if mod.get("propertyPath") == "m_LocalRotation.x":
                    mod["value"] = quaternion[0]
                if mod.get("propertyPath") == "m_LocalRotation.y":
                    mod["value"] = quaternion[1]
                if mod.get("propertyPath") == "m_LocalRotation.z":
                    mod["value"] = quaternion[2]
                if mod.get("propertyPath") == "m_LocalRotation.w":
                    mod["value"] = quaternion[3]
        for doc in coll: # could also use .extend(coll)
            self.wrapped.append(doc)

    def setup_VIVE(self, transform: dict, rotation: dict):
        
        ViveCameraRig_setup_init_text = load_structure("vive_camera_rig")
        default = compose(ViveCameraRig_setup_init_text)[0]
        wrapped = node_to_python(default)
        
        quaternion = euler_to_xyzw_quaternion(rotation)
        modifications = wrapped["PrefabInstance"]["m_Modification"]["m_Modifications"]
        for mod in modifications:
            if "target" in mod and "guid" in mod["target"]:
                if mod.get("propertyPath") == "m_LocalPosition.x":
                    mod["value"] = transform["x"]
                if mod.get("propertyPath") == "m_LocalPosition.y":
                    mod["value"] = transform["y"]
                if mod.get("propertyPath") == "m_LocalPosition.z":
                    mod["value"] = transform["z"]
                if mod.get("propertyPath") == "m_LocalRotation.x":
                    mod["value"] = quaternion[0]
                if mod.get("propertyPath") == "m_LocalRotation.y":
                    mod["value"] = quaternion[1]
                if mod.get("propertyPath") == "m_LocalRotation.z":
                    mod["value"] = quaternion[2]
                if mod.get("propertyPath") == "m_LocalRotation.w":
                    mod["value"] = quaternion[3]
        
        prefab_id = wrapped["anchor"] # constant 1214490813
        
        sceneroots = get_doc(self.wrapped, "SceneRoots")
        sceneroots["m_Roots"].append({"fileID": prefab_id})
        self.wrapped.append(wrapped)
    
    def to_unity_yaml(self, path_to_write: Optional[Path]=None):
        if path_to_write is None:
            path_to_write = Path(os.environ.get("ASSETS", "UnityProject/Assets/Generations/test"))
        file_name = str(path_to_write)
        if file_name.endswith(".unity"):
            pass
        else:
            file_name += ".unity"
        out = ["%YAML 1.1", "%TAG !u! tag:unity3d.com,2011:"]
        for entry in self.wrapped:
            #tag = entry.pop("tag")
            #anchor = entry.pop("anchor")
            tag = entry["tag"]
            anchor = entry["anchor"]
            objname = list(entry.keys())[2]
            objdata = entry[objname]
            out.append(f"--- !u!{tag} &{anchor}")
            out.append(f"{objname}:")
            out.extend(dict_to_yaml(objdata, 2))
        out = "\n".join(out) + "\n"
        with open(file_name, "w") as f:
            f.write(out)
        print(f"Written to {file_name}") 
        return file_name
    
def convert_numbers(obj):
    """ Helper """
    if isinstance(obj, dict):
        return {k: convert_numbers(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numbers(v) for v in obj]
    elif isinstance(obj, str):
        try:
            if '.' in obj:
                return float(obj)
            else:
                return int(obj)
        except ValueError:
            return obj  # keep string if not a number
    else:
        return obj

def write_obj_meta(rel_path: RelativePath, guid: str = "writing_meta"):
    #log(f"Writing OBJ meta")
    obj_meta_init_text = load_structure("orphan_meta")
    path = rel_path.path
    node = compose(obj_meta_init_text)[0]
    wrapped = node_to_python(node)
    
    wrapped["guid"] = guid
    #log("GUID set")
    reformatted = convert_numbers(wrapped)
    #log("Dumping YAML...")
    yaml_str = pyyaml.dump(
        reformatted, 
        default_flow_style=False, 
        sort_keys=False
    )
    #log("YAML dumped")
    #log("Writing YAML...")
    new_path = path.with_name(path.name + ".meta")
    #log(f"Writing YAML to {new_path}")
    #log(f"repr(path) {repr(new_path)}")
    with open(new_path, "w") as f:
        f.write(yaml_str)
    #log(f"YAML written {new_path}")
    







      


        









Vision_and_Data_Collection_init_text = """


>>> PASTE HERE <<<


"""

