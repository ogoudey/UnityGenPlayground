import yaml as pyyaml
import math
import random

import re

from ruamel.yaml import YAML as ruamel_YAML
from ruamel.yaml.nodes import ScalarNode, MappingNode, SequenceNode

def node_to_python(node):
    if isinstance(node, ScalarNode):
        return node.value
    if isinstance(node, SequenceNode):
        values_to_objects = []
        for value in node.value:
            values_to_objects.append(node_to_python(value))
        return values_to_objects
    if isinstance(node, MappingNode):  
        map_dict = {}
        if hasattr(node, "tag") and "!UnityTag" in node.tag:
            map_dict["tag"] = node.tag.removeprefix("!UnityTag")    
        if hasattr(node, "anchor") and node.anchor:
            map_dict["anchor"] = node.anchor
        for mapping_duple in node.value:
            map_dict[node_to_python(mapping_duple[0])] = node_to_python(mapping_duple[1]) 
        return map_dict
    else:
        print("Weird node detected:", type(node))
        return None

class YAML:
    def __init__(self):
        yaml = ruamel_YAML(typ='rt')

        self.level0 = list(yaml.compose_all(preprocess_text(scene_init_text)))
        # self.level0 is a list of MappingNodes
        self.wrapped = [node_to_python(n) for n in self.level0]
        
        self.proposed_objects = dict()
        self.placed_assets = dict()
    
    def set_sun(self, length_of_day, time_of_day, sun_brightness):
        rot = (time_of_day / length_of_day) * 360
        rotation = {"x": rot, "y": 0, "z": 0}
        quaternion = euler_to_xyzw_quaternion(rotation)
        print("Setting sun in YAML...")
        yaml = ruamel_YAML(typ='rt')
        default = list(yaml.compose_all(preprocess_text(sun_init_text)))
        wrapped = [node_to_python(n) for n in default]
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

        sceneroots = self.get_doc("SceneRoots")
        sceneroots["m_Roots"].append({"fileID": father_id})
        print("\rSun added to YAML.")
            
        
    def set_skybox(self, name):
        print("Setting skybox...")
        
        mat_path = self.proposed_objects[name]
        guid = get_guid(mat_path + ".meta")
        try:
            render_settings = self.get_doc("RenderSettings")
            render_settings["m_SkyboxMaterial"] = {"fileID": "2100000", "guid": guid, "type": 2}
            print("\rSkybox set in YAML.")
        except Exception:
            print("\rFailed to set skybox.")
            
    def add_transform(self, guid: str, transform: dict):
        yaml = ruamel_YAML(typ='rt')
        default = list(yaml.compose_all(preprocess_text(transform_init_text)))[0]
        wrapped = node_to_python(default)
        
        wrapped, id_out = set_ID(wrapped) # setID to random ID
        
        main = wrapped["Transform"]
        main["m_LocalPosition"] = transform
        self.wrapped.append(wrapped)
        
        sceneroots = self.get_doc("SceneRoots")
        sceneroots["m_Roots"].append({"fileID": id_out})
        return id_out
    
    def add_game_object(self, guid, transform_id):
        """ Broken """
        yaml = ruamel_YAML(typ='rt')
        default = list(yaml.compose_all(preprocess_text(game_object_init_text)))
        old_anchor = default[0]
        new_anchor, id_out = set_ID(old_anchor) # to random ID
        
        body=default[1]
        components = body["m_Component"]
        for component in components:
            if "component" in component: # all of them
                component["component"]["fileID"] = transform_id

        self.level0.append([new_anchor, body])
        transform_body = self.get_element_by_id(transform_id)
        transform_body["Transform"]["m_GameObject"]["fileID"] = id_out
        return id_out      
    
    def add_ground_prefab_instance(self, name, metaguid, transform):
        print("Adding ground to YAML...")
        yaml = ruamel_YAML(typ='rt')
        default = list(yaml.compose_all(preprocess_text(prefab_init_text)))[0]
        
        wrapped = node_to_python(default)
        
        wrapped, id_out = set_ID(wrapped) # to random ID
        
        texture = None
        try:
            proposed_objects_entry = self.proposed_objects[name]
            print("Found", name, "in proposed_objects w entry", proposed_objects_entry)
            texture_path = proposed_objects_entry["Texture"]
            if not texture_path == "None":
                texture_metaguid = get_guid(texture_path + ".meta")
        except Exception(name + " not in proposed_objects, or " + texture_path):
            print("Lookup in proposed_objects has failed.")
        

        modifications = wrapped["PrefabInstance"]["m_Modification"]["m_Modifications"]
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
                    
        wrapped["PrefabInstance"]["m_SourcePrefab"]["guid"] = metaguid
        sceneroots = self.get_doc("SceneRoots")
        sceneroots["m_Roots"].append({"fileID": id_out})
        self.wrapped.append(wrapped)
        print("Asset added to YAML.")            
    
    def remove_prefab_instance_if_exists(self, name):
        for doc in self.wrapped:
            if "PrefabInstance" in doc:
                for mod in doc["PrefabInstance"]["m_Modification"]["m_Modifications"]:
                    if mod.get("propertyPath") == "m_Name":
                        if mod["target"]["value"] == name:
                            self.wrapped.remove(doc)
                            print("Removed prefab!")
                            sceneroots = self.get_doc("SceneRoots")
                            prefab_id = doc["anchor"]
                            sceneroots["m_Roots"].remove({"fileID": prefab_id})
                            print("Removed prefabID from scene root.")
                            return True
        sceneroots = self.get_doc("SceneRoots")
        sceneroots["m_Roots"].remove({"fileID": prefab_id})
        return False
        
    def set_vr_player(self, transform:str, rotation: str):
        yaml = ruamel_YAML(typ='rt')
        print("In YAMLING")
        default = list(yaml.compose_all(preprocess_text(vr_setup_init_text)))[0]
        wrapped = node_to_python(default)
        
        quaternion = euler_to_xyzw_quaternion(rotation)
        print("Parsing init YAML...")
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
        
        sceneroots = self.get_doc("SceneRoots")
        sceneroots["m_Roots"].append({"fileID": prefab_id})
        print("Init YAML succcessfully updated.")
        self.wrapped.append(wrapped)
        print("VR Player successfully added to YAML.")
        
        
    def add_prefab_instance(self, name, transform, rotation):
        yaml = ruamel_YAML(typ='rt')
        default = list(yaml.compose_all(preprocess_text(prefab_init_text)))[0]
        wrapped = node_to_python(default)
        wrapped, id_out = set_ID(wrapped) # to random ID
        
        try:
            prefab_path = self.proposed_objects[name]
            print("Found", name, "in proposed_objects w path", prefab_path)
        except KeyError(name + " not in proposed_objects"):
            print("Lookup in proposed_objects has failed.")
        try:
            print(prefab_path)
            father_ID = self.get_father_id_of_root_transform_of_prefab(prefab_path)
        except Exception:
            print("Could not find fatherID of root transform")
        try:    
            guid = get_guid(prefab_path + ".meta")
        except Exception:
            print("Could not get guid from .meta file:", prefab_path + ".meta")
        
        # find prefabs local filenames
        self.placed_assets[name] = {"transform": transform, "rotation": rotation}
        
        scale = 1.0
        
        quaternion = euler_to_xyzw_quaternion(rotation)
        print("Parsing init YAML...")
        modifications = wrapped["PrefabInstance"]["m_Modification"]["m_Modifications"]
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
                      
                      

                    
        wrapped["PrefabInstance"]["m_SourcePrefab"]["guid"] = guid
        sceneroots = self.get_doc("SceneRoots")
        sceneroots["m_Roots"].append({"fileID": id_out})
        print("\rInit YAML succcessfully updated.")
        self.wrapped.append(wrapped)
        print("Asset added to YAML.")
        
    def get_father_id_of_root_transform_of_prefab(self, prefab_path):
        with open(prefab_path, "r") as f:
            prefab_file = f.read()
        yaml = ruamel_YAML(typ='rt')
        default = list(yaml.compose_all(preprocess_text(prefab_file)))
        wrapped = [node_to_python(n) for n in default]
        for doc in wrapped:
            if "Transform" in doc.keys():
                if doc["Transform"]["m_Father"]["fileID"] == "0":
                    father_id = doc["anchor"]
        if not father_id:
            raise KeyError("The located prefab has no root transform")
        return father_id
    
    def to_unity_yaml(self, file_name="minimal.unity"):
        if not file_name.endswith(".unity"):
            file_name += ".unity"
        file_name = file_name
        print("Attempting to write to", file_name)
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
        print("YAML written to", file_name) 

    def dump(self, file_name="minimal.unity"):
        
        if not file_name.endswith(".unity"):
            file_name += ".unity"
            
        # Dump YAML content to a string first
        yaml_content = pyyaml.safe_dump_all(self.level0, sort_keys=False)
        yaml_content = pyyaml_content.replace("!UnityTag", "!u!")


        with open(file_name, "w") as f:
            f.write(full_content)

    def get_doc(self, top_key):
        """
        Return the value of a top-level key in any YAML document.
        Returns None if not found.
        """
        list_item = next((doc for doc in self.wrapped if top_key in doc.keys()), None)
        if list_item is None:
            return None
        return list_item[top_key]
        
    def get_element_by_id(id_):
        for doc_i in range(0, len(self.level0)):
            if "&" in self.level0[doc_i]:
                if self.level0[doc_i].split("&")[1] == id_:
                    return self.level0[doc_i + 1]

def get_texture_meta(meta_path):
    with open(meta_path, "r") as f:
        data = pyyaml.safe_load(f)

def euler_to_xyzw_quaternion(rotation):
    print("Rotation:", rotation)
    x_deg, y_deg, z_deg = rotation["x"], rotation["y"], rotation["z"]

    # Convert degrees to radians
    x = math.radians(x_deg)
    y = math.radians(y_deg)
    z = math.radians(z_deg)

    cx = math.cos(x/2)
    sx = math.sin(x/2)
    cy = math.cos(y/2)
    sy = math.sin(y/2)
    cz = math.cos(z/2)
    sz = math.sin(z/2)

    # Unity's convention: Quaternion = (x, y, z, w)
    # Order of rotations: Z, X, Y (same as Unity's inspector)
    qw = cz*cx*cy + sz*sx*sy
    qx = cz*sx*cy - sz*cx*sy
    qy = cz*cx*sy + sz*sx*cy
    qz = sz*cx*cy - cz*sx*sy
    print("Calculation of quaternion done:", (qx, qy, qz, qw))
    return (qx, qy, qz, qw)            

def set_ID(text: str, new_id: str=None) -> str:
    """ Changes the ID in the anchor line """
    if not new_id:
        new_id = str(random.randint(1000000000, 9999999999))
    if "anchor" in text.keys():
        text["anchor"] = new_id
    else:
        raise ValueError("No anchor to be set!")
    return text, new_id


        
def get_guid(meta_file: str) -> str:
    """Returns the 'guid' property from a Unity .meta YAML file."""
    with open(meta_file, "r") as f:
        data = pyyaml.safe_load(f)
    
    # Ensure 'guid' exists
    if "guid" not in data:
        raise KeyError(f"'guid' not found in {meta_file}")
    
    return data["guid"]

def try_number(val):
    """Convert to int/float if it's a 'safe' number, else keep string."""
    if isinstance(val, str):
        # Don't convert if it has leading zeros (unless it's exactly "0")
        if val.isdigit() and not (val.startswith("0") and val != "0"):
            return int(val)
        try:
            # Convert floats, but not scientific/strange formats
            if "." in val and not val.startswith("0"):
                return float(val)
        except ValueError:
            return val
        return val
    return val

def is_unity_inline_dict(d: dict) -> bool:
    keys = set(d.keys())
    # Object refs
    if keys <= {"fileID", "guid", "type"}:
        return True
    # Vector3 / Quaternion style
    if keys in ({"x", "y", "z"}, {"x", "y", "z", "w"}):
        return True
    if keys <= {"r", "g", "b", "a"}:
        return True
    
    return False

def dict_to_yaml(d, indent=0):
    """Recursively turn dict into Unity-style YAML lines."""
    lines = []
    for k, v in d.items():
        if isinstance(v, dict):
            if is_unity_inline_dict(v):
                inner = ", ".join(f"{ik}: {try_number(iv)}" for ik, iv in v.items())
                lines.append(" " * indent + f"{k}: {{{inner}}}")
            else:
                lines.append(" " * indent + f"{k}:")
                lines.extend(dict_to_yaml(v, indent + 2))
        elif isinstance(v, list):
            if not v:
                lines.append(" " * indent + f"{k}: []")
            else:
                lines.append(" " * indent + f"{k}:")
                for item in v:
                    if isinstance(item, dict):
                        if is_unity_inline_dict(item):
                            inner = ", ".join(f"{ik}: {try_number(iv)}" for ik, iv in item.items())
                            lines.append(" " * (indent + 2) + f"- {{{inner}}}")
                        else:
                            # Multi-key dict: dash + first key on same line
                            first_key, first_val = next(iter(item.items()))
                            if isinstance(first_val, dict) and is_unity_inline_dict(first_val):
                                inner = ", ".join(f"{ik2}: {try_number(iv2)}" for ik2, iv2 in first_val.items())
                                lines.append(" " * (indent + 2) + f"- {first_key}: {{{inner}}}")
                            elif isinstance(first_val, dict):
                                lines.append(" " * (indent + 2) + f"- {first_key}:")
                                lines.extend(dict_to_yaml(first_val, indent + 4))
                            else:
                                lines.append(" " * (indent + 2) + f"- {first_key}: {try_number(first_val)}")

                            # Remaining keys indented 2 spaces relative to dash
                            for ik, iv in list(item.items())[1:]:
                                if isinstance(iv, dict) and is_unity_inline_dict(iv):
                                    inner = ", ".join(f"{ik2}: {try_number(iv2)}" for ik2, iv2 in iv.items())
                                    lines.append(" " * (indent + 4) + f"{ik}: {{{inner}}}")
                                elif isinstance(iv, dict):
                                    lines.append(" " * (indent + 4) + f"{ik}:")
                                    lines.extend(dict_to_yaml(iv, indent + 6))
                                else:
                                    lines.append(" " * (indent + 4) + f"{ik}: {try_number(iv)}")
                    else:
                        lines.append(" " * (indent + 2) + f"- {try_number(item)}")
        else:
            lines.append(" " * indent + f"{k}: {try_number(v)}")
    return lines

def convert_numbers(obj):
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

def write_obj_meta(obj_path, guid):
    yaml = ruamel_YAML(typ='rt')
    default = list(yaml.compose_all(obj_meta_init_text))[0]

    wrapped = node_to_python(default)
    wrapped["guid"] = guid

    

    reformatted = convert_numbers(wrapped)
    
    yaml_str = pyyaml.dump(
        reformatted, 
        default_flow_style=False, 
        sort_keys=False
    )
    
    with open(obj_path + ".meta", "w") as f:
        f.write(yaml_str)
        
    print("Meta file with updated GUID written")

camera_init_text = """--- !u!1 &934428583
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  serializedVersion: 6
  m_Component:
  - component: {fileID: 934428587}
  - component: {fileID: 934428586}
  - component: {fileID: 934428585}
  - component: {fileID: 934428584}
  m_Layer: 0
  m_Name: Camera
  m_TagString: Untagged
  m_Icon: {fileID: 0}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
--- !u!114 &934428584
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_GameObject: {fileID: 934428583}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {fileID: 11500000, guid: a79441f348de89743a2939f4d699eac1, type: 3}
  m_Name: 
  m_EditorClassIdentifier: Unity.RenderPipelines.Universal.Runtime::UnityEngine.Rendering.Universal.UniversalAdditionalCameraData
  m_RenderShadows: 1
  m_RequiresDepthTextureOption: 2
  m_RequiresOpaqueTextureOption: 2
  m_CameraType: 0
  m_Cameras: []
  m_RendererIndex: -1
  m_VolumeLayerMask:
    serializedVersion: 2
    m_Bits: 1
  m_VolumeTrigger: {fileID: 0}
  m_VolumeFrameworkUpdateModeOption: 2
  m_RenderPostProcessing: 0
  m_Antialiasing: 0
  m_AntialiasingQuality: 2
  m_StopNaN: 0
  m_Dithering: 0
  m_ClearDepth: 1
  m_AllowXRRendering: 1
  m_AllowHDROutput: 1
  m_UseScreenCoordOverride: 0
  m_ScreenSizeOverride: {x: 0, y: 0, z: 0, w: 0}
  m_ScreenCoordScaleBias: {x: 0, y: 0, z: 0, w: 0}
  m_RequiresDepthTexture: 0
  m_RequiresColorTexture: 0
  m_TaaSettings:
    m_Quality: 3
    m_FrameInfluence: 0.1
    m_JitterScale: 1
    m_MipBias: 0
    m_VarianceClampScale: 0.9
    m_ContrastAdaptiveSharpening: 0
  m_Version: 2
--- !u!81 &934428585
AudioListener:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_GameObject: {fileID: 934428583}
  m_Enabled: 1
--- !u!20 &934428586
Camera:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_GameObject: {fileID: 934428583}
  m_Enabled: 1
  serializedVersion: 2
  m_ClearFlags: 1
  m_BackGroundColor: {r: 0.19215687, g: 0.3019608, b: 0.4745098, a: 0}
  m_projectionMatrixMode: 1
  m_GateFitMode: 2
  m_FOVAxisMode: 0
  m_Iso: 200
  m_ShutterSpeed: 0.005
  m_Aperture: 16
  m_FocusDistance: 10
  m_FocalLength: 50
  m_BladeCount: 5
  m_Curvature: {x: 2, y: 11}
  m_BarrelClipping: 0.25
  m_Anamorphism: 0
  m_SensorSize: {x: 36, y: 24}
  m_LensShift: {x: 0, y: 0}
  m_NormalizedViewPortRect:
    serializedVersion: 2
    x: 0
    y: 0
    width: 1
    height: 1
  near clip plane: 0.3
  far clip plane: 1000
  field of view: 60
  orthographic: 0
  orthographic size: 5
  m_Depth: 0
  m_CullingMask:
    serializedVersion: 2
    m_Bits: 4294967295
  m_RenderingPath: -1
  m_TargetTexture: {fileID: 0}
  m_TargetDisplay: 0
  m_TargetEye: 3
  m_HDR: 1
  m_AllowMSAA: 1
  m_AllowDynamicResolution: 0
  m_ForceIntoRT: 0
  m_OcclusionCulling: 1
  m_StereoConvergence: 10
  m_StereoSeparation: 0.022
--- !u!4 &934428587
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_GameObject: {fileID: 934428583}
  serializedVersion: 2
  m_LocalRotation: {x: -0.08717229, y: 0.89959055, z: -0.21045254, w: -0.3726226}
  m_LocalPosition: {x: 8.335457, y: 11.953455, z: 16.25771}
  m_LocalScale: {x: 1, y: 1, z: 1}
  m_ConstrainProportionsScale: 0
  m_Children: []
  m_Father: {fileID: 0}
  m_LocalEulerAnglesHint: {x: 0, y: 0, z: 0}
"""
sun_init_text = """
--- !u!1 &786546698
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  serializedVersion: 6
  m_Component:
  - component: {fileID: 786546699}
  - component: {fileID: 786546700}
  m_Layer: 0
  m_Name: Directional Light
  m_TagString: Untagged
  m_Icon: {fileID: 0}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
--- !u!4 &786546699
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_GameObject: {fileID: 786546698}
  serializedVersion: 2
  m_LocalRotation: {x: 0.668346, y: -0.12872267, z: -0.119008936, w: 0.7228977}
  m_LocalPosition: {x: 15.31607, y: 9.356531, z: 8.9202175}
  m_LocalScale: {x: 1, y: 1, z: 1}
  m_ConstrainProportionsScale: 0
  m_Children: []
  m_Father: {fileID: 1629422138}
  m_LocalEulerAnglesHint: {x: 90, y: 0, z: 0}
--- !u!108 &786546700
Light:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_GameObject: {fileID: 786546698}
  m_Enabled: 1
  serializedVersion: 11
  m_Type: 1
  m_Color: {r: 1, g: 1, b: 1, a: 1}
  m_Intensity: 1
  m_Range: 10
  m_SpotAngle: 30
  m_InnerSpotAngle: 21.80208
  m_CookieSize: 10
  m_Shadows:
    m_Type: 0
    m_Resolution: -1
    m_CustomResolution: -1
    m_Strength: 1
    m_Bias: 0.05
    m_NormalBias: 0.4
    m_NearPlane: 0.2
    m_CullingMatrixOverride:
      e00: 1
      e01: 0
      e02: 0
      e03: 0
      e10: 0
      e11: 1
      e12: 0
      e13: 0
      e20: 0
      e21: 0
      e22: 1
      e23: 0
      e30: 0
      e31: 0
      e32: 0
      e33: 1
    m_UseCullingMatrixOverride: 0
  m_Cookie: {fileID: 0}
  m_DrawHalo: 0
  m_Flare: {fileID: 0}
  m_RenderMode: 0
  m_CullingMask:
    serializedVersion: 2
    m_Bits: 4294967295
  m_RenderingLayerMask: 1
  m_Lightmapping: 4
  m_LightShadowCasterMode: 0
  m_AreaSize: {x: 1, y: 1}
  m_BounceIntensity: 1
  m_ColorTemperature: 6570
  m_UseColorTemperature: 0
  m_BoundingSphereOverride: {x: 0, y: 0, z: 0, w: 0}
  m_UseBoundingSphereOverride: 0
  m_UseViewFrustumForShadowCasterCull: 1
  m_ForceVisible: 0
  m_ShadowRadius: 0
  m_ShadowAngle: 0
  m_LightUnit: 1
  m_LuxAtDistance: 1
  m_EnableSpotReflector: 1
--- !u!1 &1629422137
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  serializedVersion: 6
  m_Component:
  - component: {fileID: 1629422138}
  m_Layer: 0
  m_Name: GameObject
  m_TagString: Untagged
  m_Icon: {fileID: 0}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
--- !u!4 &1629422138
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_GameObject: {fileID: 1629422137}
  serializedVersion: 2
  m_LocalRotation: {x: 0, y: 0, z: 0, w: 1}
  m_LocalPosition: {x: 0, y: 0, z: 0}
  m_LocalScale: {x: 1, y: 1, z: 1}
  m_ConstrainProportionsScale: 0
  m_Children:
  - {fileID: 786546699}
  m_Father: {fileID: 0}
  m_LocalEulerAnglesHint: {x: 0, y: 0, z: 0}
"""

vr_setup_init_text = """
--- !u!1001 &1214490813
PrefabInstance:
  m_ObjectHideFlags: 0
  serializedVersion: 2
  m_Modification:
    serializedVersion: 3
    m_TransformParent: {fileID: 0}
    m_Modifications:
    - target: {fileID: 175660, guid: cb3370c18187bb444b240cfb08dcc02f, type: 3}
      propertyPath: m_Name
      value: ViveCameraRig
      objectReference: {fileID: 0}
    - target: {fileID: 463184, guid: cb3370c18187bb444b240cfb08dcc02f, type: 3}
      propertyPath: m_RootOrder
      value: 1
      objectReference: {fileID: 0}
    - target: {fileID: 463184, guid: cb3370c18187bb444b240cfb08dcc02f, type: 3}
      propertyPath: m_LocalPosition.x
      value: 0
      objectReference: {fileID: 0}
    - target: {fileID: 463184, guid: cb3370c18187bb444b240cfb08dcc02f, type: 3}
      propertyPath: m_LocalPosition.y
      value: 0
      objectReference: {fileID: 0}
    - target: {fileID: 463184, guid: cb3370c18187bb444b240cfb08dcc02f, type: 3}
      propertyPath: m_LocalPosition.z
      value: 0
      objectReference: {fileID: 0}
    - target: {fileID: 463184, guid: cb3370c18187bb444b240cfb08dcc02f, type: 3}
      propertyPath: m_LocalRotation.w
      value: 1
      objectReference: {fileID: 0}
    - target: {fileID: 463184, guid: cb3370c18187bb444b240cfb08dcc02f, type: 3}
      propertyPath: m_LocalRotation.x
      value: 0
      objectReference: {fileID: 0}
    - target: {fileID: 463184, guid: cb3370c18187bb444b240cfb08dcc02f, type: 3}
      propertyPath: m_LocalRotation.y
      value: 0
      objectReference: {fileID: 0}
    - target: {fileID: 463184, guid: cb3370c18187bb444b240cfb08dcc02f, type: 3}
      propertyPath: m_LocalRotation.z
      value: 0
      objectReference: {fileID: 0}
    - target: {fileID: 463184, guid: cb3370c18187bb444b240cfb08dcc02f, type: 3}
      propertyPath: m_LocalEulerAnglesHint.x
      value: 0
      objectReference: {fileID: 0}
    - target: {fileID: 463184, guid: cb3370c18187bb444b240cfb08dcc02f, type: 3}
      propertyPath: m_LocalEulerAnglesHint.y
      value: 0
      objectReference: {fileID: 0}
    - target: {fileID: 463184, guid: cb3370c18187bb444b240cfb08dcc02f, type: 3}
      propertyPath: m_LocalEulerAnglesHint.z
      value: 0
      objectReference: {fileID: 0}
    m_RemovedComponents: []
    m_RemovedGameObjects: []
    m_AddedGameObjects: []
    m_AddedComponents: []
  m_SourcePrefab: {fileID: 100100000, guid: cb3370c18187bb444b240cfb08dcc02f, type: 3}
 """

obj_meta_init_text = """
fileFormatVersion: 2
guid: d52b4c2576141d6e284af00db4ba39ac
ModelImporter:
  serializedVersion: 24200
  internalIDToNameTable: []
  externalObjects: {}
  materials:
    materialImportMode: 2
    materialName: 0
    materialSearch: 1
    materialLocation: 1
  animations:
    legacyGenerateAnimations: 4
    bakeSimulation: 0
    resampleCurves: 1
    optimizeGameObjects: 0
    removeConstantScaleCurves: 0
    motionNodeName: 
    animationImportErrors: 
    animationImportWarnings: 
    animationRetargetingWarnings: 
    animationDoRetargetingWarnings: 0
    importAnimatedCustomProperties: 0
    importConstraints: 0
    animationCompression: 1
    animationRotationError: 0.5
    animationPositionError: 0.5
    animationScaleError: 0.5
    animationWrapMode: 0
    extraExposedTransformPaths: []
    extraUserProperties: []
    clipAnimations: []
    isReadable: 0
  meshes:
    lODScreenPercentages: []
    globalScale: 1
    meshCompression: 0
    addColliders: 0
    useSRGBMaterialColor: 1
    sortHierarchyByName: 1
    importPhysicalCameras: 1
    importVisibility: 1
    importBlendShapes: 1
    importCameras: 1
    importLights: 1
    nodeNameCollisionStrategy: 1
    fileIdsGeneration: 2
    swapUVChannels: 0
    generateSecondaryUV: 0
    useFileUnits: 1
    keepQuads: 0
    weldVertices: 1
    bakeAxisConversion: 0
    preserveHierarchy: 0
    skinWeightsMode: 0
    maxBonesPerVertex: 4
    minBoneWeight: 0.001
    optimizeBones: 1
    generateMeshLods: 0
    meshLodGenerationFlags: 0
    maximumMeshLod: -1
    meshOptimizationFlags: -1
    indexFormat: 0
    secondaryUVAngleDistortion: 8
    secondaryUVAreaDistortion: 15.000001
    secondaryUVHardAngle: 88
    secondaryUVMarginMethod: 1
    secondaryUVMinLightmapResolution: 40
    secondaryUVMinObjectScale: 1
    secondaryUVPackMargin: 4
    useFileScale: 1
    strictVertexDataChecks: 0
  tangentSpace:
    normalSmoothAngle: 60
    normalImportMode: 0
    tangentImportMode: 3
    normalCalculationMode: 4
    legacyComputeAllNormalsFromSmoothingGroupsWhenMeshHasBlendShapes: 0
    blendShapeNormalImportMode: 1
    normalSmoothingSource: 0
  referencedClips: []
  importAnimation: 1
  humanDescription:
    serializedVersion: 3
    human: []
    skeleton: []
    armTwist: 0.5
    foreArmTwist: 0.5
    upperLegTwist: 0.5
    legTwist: 0.5
    armStretch: 0.05
    legStretch: 0.05
    feetSpacing: 0
    globalScale: 1
    rootMotionBoneName: 
    hasTranslationDoF: 0
    hasExtraRoot: 0
    skeletonHasParents: 1
  lastHumanDescriptionAvatarSource: {instanceID: 0}
  autoGenerateAvatarMappingIfUnspecified: 1
  animationType: 2
  humanoidOversampling: 1
  avatarSetup: 0
  addHumanoidExtraRootOnlyWhenUsingAvatar: 1
  importBlendShapeDeformPercent: 1
  remapMaterialsIfMaterialImportModeIsNone: 0
  additionalBone: 0
  userData: 
  assetBundleName: 
  assetBundleVariant: 
"""
 
scene_init_text = """
%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!29 &1
OcclusionCullingSettings:
  m_ObjectHideFlags: 0
  serializedVersion: 2
  m_OcclusionBakeSettings:
    smallestOccluder: 5
    smallestHole: 0.25
    backfaceThreshold: 100
  m_SceneGUID: 00000000000000000000000000000000
  m_OcclusionCullingData: {fileID: 0}
--- !u!104 &2
RenderSettings:
  m_ObjectHideFlags: 0
  serializedVersion: 10
  m_Fog: 0
  m_FogColor: {r: 0.5, g: 0.5, b: 0.5, a: 1}
  m_FogMode: 3
  m_FogDensity: 0.01
  m_LinearFogStart: 0
  m_LinearFogEnd: 300
  m_AmbientSkyColor: {r: 0.212, g: 0.227, b: 0.259, a: 1}
  m_AmbientEquatorColor: {r: 0.114, g: 0.125, b: 0.133, a: 1}
  m_AmbientGroundColor: {r: 0.047, g: 0.043, b: 0.035, a: 1}
  m_AmbientIntensity: 1
  m_AmbientMode: 3
  m_SubtractiveShadowColor: {r: 0.42, g: 0.478, b: 0.627, a: 1}
  m_SkyboxMaterial: {fileID: 0}
  m_HaloStrength: 0.5
  m_FlareStrength: 1
  m_FlareFadeSpeed: 3
  m_HaloTexture: {fileID: 0}
  m_SpotCookie: {fileID: 10001, guid: 0000000000000000e000000000000000, type: 0}
  m_DefaultReflectionMode: 0
  m_DefaultReflectionResolution: 128
  m_ReflectionBounces: 1
  m_ReflectionIntensity: 1
  m_CustomReflection: {fileID: 0}
  m_Sun: {fileID: 0}
  m_UseRadianceAmbientProbe: 0
--- !u!157 &3
LightmapSettings:
  m_ObjectHideFlags: 0
  serializedVersion: 13
  m_BakeOnSceneLoad: 0
  m_GISettings:
    serializedVersion: 2
    m_BounceScale: 1
    m_IndirectOutputScale: 1
    m_AlbedoBoost: 1
    m_EnvironmentLightingMode: 0
    m_EnableBakedLightmaps: 0
    m_EnableRealtimeLightmaps: 0
  m_LightmapEditorSettings:
    serializedVersion: 12
    m_Resolution: 2
    m_BakeResolution: 40
    m_AtlasSize: 1024
    m_AO: 0
    m_AOMaxDistance: 1
    m_CompAOExponent: 1
    m_CompAOExponentDirect: 0
    m_ExtractAmbientOcclusion: 0
    m_Padding: 2
    m_LightmapParameters: {fileID: 0}
    m_LightmapsBakeMode: 1
    m_TextureCompression: 1
    m_ReflectionCompression: 2
    m_MixedBakeMode: 2
    m_BakeBackend: 1
    m_PVRSampling: 1
    m_PVRDirectSampleCount: 32
    m_PVRSampleCount: 512
    m_PVRBounces: 2
    m_PVREnvironmentSampleCount: 256
    m_PVREnvironmentReferencePointCount: 2048
    m_PVRFilteringMode: 1
    m_PVRDenoiserTypeDirect: 1
    m_PVRDenoiserTypeIndirect: 1
    m_PVRDenoiserTypeAO: 1
    m_PVRFilterTypeDirect: 0
    m_PVRFilterTypeIndirect: 0
    m_PVRFilterTypeAO: 0
    m_PVREnvironmentMIS: 1
    m_PVRCulling: 1
    m_PVRFilteringGaussRadiusDirect: 1
    m_PVRFilteringGaussRadiusIndirect: 1
    m_PVRFilteringGaussRadiusAO: 1
    m_PVRFilteringAtrousPositionSigmaDirect: 0.5
    m_PVRFilteringAtrousPositionSigmaIndirect: 2
    m_PVRFilteringAtrousPositionSigmaAO: 1
    m_ExportTrainingData: 0
    m_TrainingDataDestination: TrainingData
    m_LightProbeSampleCountMultiplier: 4
  m_LightingDataAsset: {fileID: 20201, guid: 0000000000000000f000000000000000, type: 0}
  m_LightingSettings: {fileID: 0}
--- !u!196 &4
NavMeshSettings:
  serializedVersion: 2
  m_ObjectHideFlags: 0
  m_BuildSettings:
    serializedVersion: 3
    agentTypeID: 0
    agentRadius: 0.5
    agentHeight: 2
    agentSlope: 45
    agentClimb: 0.4
    ledgeDropHeight: 0
    maxJumpAcrossDistance: 0
    minRegionArea: 2
    manualCellSize: 0
    cellSize: 0.16666667
    manualTileSize: 0
    tileSize: 256
    buildHeightMesh: 0
    maxJobWorkers: 0
    preserveTilesOutsideBounds: 0
    debug:
      m_Flags: 0
  m_NavMeshData: {fileID: 0}
--- !u!1660057539 &9223372036854775807
SceneRoots:
  m_ObjectHideFlags: 0
  m_Roots: []
""" # end init text

prefab_init_text = """
--- !u!1001 &1434556948
PrefabInstance:
  m_ObjectHideFlags: 0
  serializedVersion: 2
  m_Modification:
    serializedVersion: 3
    m_TransformParent: {fileID: 0}
    m_Modifications:
    - target: {fileID: 0, guid: 1f9036ec905b920479091aca9ba81305, type: 3}
      propertyPath: m_Name
      value: Spruce 1
      objectReference: {fileID: 0}
    - target: {fileID: 6, guid: 1f9036ec905b920479091aca9ba81305, type: 3}
      propertyPath: m_LocalPosition.x
      value: -1045.3981
      objectReference: {fileID: 0}
    - target: {fileID: 6, guid: 1f9036ec905b920479091aca9ba81305, type: 3}
      propertyPath: m_LocalPosition.y
      value: 2190.1765
      objectReference: {fileID: 0}
    - target: {fileID: 6, guid: 1f9036ec905b920479091aca9ba81305, type: 3}
      propertyPath: m_LocalPosition.z
      value: 3885.3948
      objectReference: {fileID: 0}
    - target: {fileID: 6, guid: 1f9036ec905b920479091aca9ba81305, type: 3}
      propertyPath: m_LocalRotation.w
      value: 1
      objectReference: {fileID: 0}
    - target: {fileID: 6, guid: 1f9036ec905b920479091aca9ba81305, type: 3}
      propertyPath: m_LocalRotation.x
      value: 0
      objectReference: {fileID: 0}
    - target: {fileID: 6, guid: 1f9036ec905b920479091aca9ba81305, type: 3}
      propertyPath: m_LocalRotation.y
      value: 0
      objectReference: {fileID: 0}
    - target: {fileID: 6, guid: 1f9036ec905b920479091aca9ba81305, type: 3}
      propertyPath: m_LocalRotation.z
      value: 0
      objectReference: {fileID: 0}
    - target: {fileID: 6, guid: 1f9036ec905b920479091aca9ba81305, type: 3}
      propertyPath: m_LocalEulerAnglesHint.x
      value: 0
      objectReference: {fileID: 0}
    - target: {fileID: 6, guid: 1f9036ec905b920479091aca9ba81305, type: 3}
      propertyPath: m_LocalEulerAnglesHint.y
      value: 0
      objectReference: {fileID: 0}
    - target: {fileID: 6, guid: 1f9036ec905b920479091aca9ba81305, type: 3}
      propertyPath: m_LocalEulerAnglesHint.z
      value: 0
      objectReference: {fileID: 0}
    - target: {fileID: -7635826562936255635, guid: 2c2afc1a4f0c4d298e6b04d7c4babd1a, type: 3}
      propertyPath: 'm_Materials.Array.data[0]'
      value: 
      objectReference: {fileID: 2100000, guid: 94ea32e4f0f6cab4e98928aadb7d9992, type: 2}

    m_RemovedComponents: []
    m_RemovedGameObjects: []
    m_AddedGameObjects: []
    m_AddedComponents: []
  m_SourcePrefab: {fileID: 100100000, guid: 1f9036ec905b920479091aca9ba81305, type: 3}
"""

"""
    - target: {fileID: -7635826562936255635, guid: a973d619bfe74a0ea69f55314cf2a8f9, type: 3}
      propertyPath: 'm_Materials.Array.data[0]'
      value: 
      objectReference: {fileID: 2100000, guid: 45eb7efec0c8f504285b382733758e52, type: 2}
"""

game_object_init_text = """
--- !u!1 &2134185226
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  serializedVersion: 6
  m_Component:
  - component: {fileID: 2134185227}
  m_Layer: 0
  m_Name: GameObject
  m_TagString: Untagged
  m_Icon: {fileID: 0}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
"""

transform_init_text = """
--- !u!4 &2134185227
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_GameObject: {fileID: 2134185226}
  serializedVersion: 2
  m_LocalRotation: {x: 0, y: 0, z: 0, w: 1}
  m_LocalPosition: {x: -1045.6066, y: 2196.2122, z: 3885.3037}
  m_LocalScale: {x: 1, y: 1, z: 1}
  m_ConstrainProportionsScale: 0
  m_Children:
  - {fileID: 134496795}
  m_Father: {fileID: 0}
  m_LocalEulerAnglesHint: {x: 0, y: 0, z: 0}
"""

def preprocess_text(text):
    return re.sub(r"!u!(\d+)", r"!UnityTag\1", text)
