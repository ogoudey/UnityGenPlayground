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
        
        self.used_assets = dict()
        self.placed_assets = dict()
        
    def set_skybox(self, name):
        print("Setting skybox...")
        
        mat_path = self.used_assets[name]
        guid = get_guid(mat_path + ".meta")
        try:
            render_settings = self.get_doc("RenderSettings")
            render_settings["m_SkyboxMaterial"] = {"fileID": "2100000", "guid": guid, "type": 2}
            print("Skybox set in YAML.")
        except Exception:
            print("Failed to set skybox.")
            
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
    
    def add_ground_prefab_instance(self, metaguid, transform):
        yaml = ruamel_YAML(typ='rt')
        default = list(yaml.compose_all(preprocess_text(prefab_init_text)))[0]
        
        wrapped = node_to_python(default)
        
        wrapped, id_out = set_ID(wrapped) # to random ID
        
            
        modifications = wrapped["PrefabInstance"]["m_Modification"]["m_Modifications"]
        for mod in modifications:
            if "target" in mod and "guid" in mod["target"]:
                mod["target"]["fileID"] = "-8679921383154817045"
                mod["target"]["guid"] = metaguid
                if mod.get("propertyPath") == "m_Name":
                    mod["target"]["value"] = "Name of object here" # Anything?
                else:
                    if mod.get("propertyPath") == "m_LocalPosition.x":
                        mod["value"] = transform["x"]
                    if mod.get("propertyPath") == "m_LocalPosition.y":
                        mod["value"] = transform["y"]
                    if mod.get("propertyPath") == "m_LocalPosition.z":
                        mod["value"] = transform["z"]
        """
        If you set the fileID to -8679921383154817045 you can change the transform.
        """
                    
        wrapped["PrefabInstance"]["m_SourcePrefab"]["guid"] = metaguid
        sceneroots = self.get_doc("SceneRoots")
        sceneroots["m_Roots"].append({"fileID": id_out})
        self.wrapped.append(wrapped)
        print("Asset added to YAML.")            
    
    def add_prefab_instance(self, name, transform, rotation):
        yaml = ruamel_YAML(typ='rt')
        default = list(yaml.compose_all(preprocess_text(prefab_init_text)))[0]
        wrapped = node_to_python(default)
        wrapped, id_out = set_ID(wrapped) # to random ID
        
        try:
            prefab_path = self.used_assets[name]
            print("Found", name, "in used_assets w path", prefab_path)
        except KeyError(name + " not in used_assets"):
            print("Lookup in used_assets has failed.")
        try:
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
                    mod["target"]["value"] = "Name of object here" # Anything?
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
                      
                      
                -7635826562936255635  
                    
        wrapped["PrefabInstance"]["m_SourcePrefab"]["guid"] = guid
        sceneroots = self.get_doc("SceneRoots")
        sceneroots["m_Roots"].append({"fileID": id_out})
        print("Init YAML succcessfully updated.")
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
        file_name = "../Assets/Scenes/" + file_name
        print("Attempting to write to", file_name)
        out = ["%YAML 1.1", "%TAG !u! tag:unity3d.com,2011:"]
        for entry in self.wrapped:
            tag = entry.pop("tag")
            anchor = entry.pop("anchor")
            # remaining single top-level key is the object name
            [(objname, objdata)] = entry.items()
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
    m_RemovedComponents: []
    m_RemovedGameObjects: []
    m_AddedGameObjects: []
    m_AddedComponents: []
  m_SourcePrefab: {fileID: 100100000, guid: 1f9036ec905b920479091aca9ba81305, type: 3}
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
