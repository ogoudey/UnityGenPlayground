import yaml 
from yaml import compose_all
import random

import re

# Custom loader
class UnityLoader(yaml.SafeLoader):
    pass

# Catch-all for any !u! tag
def unity_tag_constructor(loader, tag_suffix, node):
    # Convert the node to a Python dict
    return loader.construct_mapping(node)

# Register the catch-all constructor
UnityLoader.add_multi_constructor("!UnityTag", unity_tag_constructor)



class YAML:
    def __init__(self):
        self.level0 = list(yaml.compose_all(re.sub(r"!u!(\d+)", r"!UnityTag\1", scene_init_text), Loader=UnityLoader))
        #self.level0 = list(yaml.safe_compose_all(scene_init_text))
        
    def set_skybox(self, guid):
        print(self.level0)
        print("\n\n\n\n\n")
        render_settings = self.get_doc_key("RenderSettings")
        render_settings["m_SkyboxMaterial"]: {"fileID": "2100000", "guid": guid, "type": 2}
    
    def add_transform(self, guid: str, transform: dict):
        default = list(yaml.compose_all(re.sub(r"!u!(\d+)", r"!UnityTag\1", scene_init_text), Loader=UnityLoader))
        old_anchor = default[0]
        new_anchor, id_out = set_ID(old_anchor) # to random ID
        
        body = default[1]
        
        body["m_LocalPosition"] = transform
        self.level0.append([new_anchor, body])
        
        sceneroots = self.get_doc_key("SceneRoots")
        sceneroots["m_Roots"].append({"fileID": id_out})
        return id_out
    
    def add_game_object(self, guid, transform_id):
        default = list(yaml.compose_all(re.sub(r"!u!(\d+)", r"!UnityTag\1", scene_init_text), Loader=UnityLoader))
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
                
    
    def add_prefab_instance(self, guid, prefab_path, transform, transform_id=0):
        default = list(yaml.compose_all(re.sub(r"!u!(\d+)", r"!UnityTag\1", prefab_init_text), Loader=UnityLoader))
        old_anchor = default[0]
        new_anchor, id_out = set_ID(old_anchor) # to random ID
        
        # find prefabs local filenames
        
        
        body=default[1]
        modifications = body["PrefabInstance"]["m_Modification"]["m_Modifications"]
        for mod in modifications:
            if "target" in mod and "guid" in mod["target"]:
                if mod.get("propertyPath") == "m_Name":
                    mod["target"]["guid"] = 0 # Anything?
                else:
                    mod["target"]["guid"] = guid
                    if mod.get("propertyPath") == "m_LocalPosition.x":
                        mod["value"] = transform["x"]
                    if mod.get("propertyPath") == "m_LocalPosition.y":
                        mod["value"] = transform["y"]
                    if mod.get("propertyPath") == "m_LocalPosition.z":
                        mod["value"] = transform["z"]
                    
        body["PrefabInstance"]["m_Modification"]["m_TransformParent"] = transform_id
        body["PrefabInstance"]["m_SourcePrefab"]["guid"] = guid
        self.level0.append([new_anchor, body])
        
        
        
    def dump(self, file_name="minimal.unity"):
        if not file_name.endswith(".unity"):
            file_name += ".unity"
            
        # Dump YAML content to a string first
        yaml_content = yaml.safe_dump_all(self.level0, sort_keys=False)
        yaml_content = yaml_content.replace("!UnityTag", "!u!")
        # Prepend the Unity YAML header lines
        header = "%YAML 1.1\n%TAG !u! tag:unity3d.com,2011:\n"
        full_content = header + yaml_content

        with open(file_name, "w") as f:
            f.write(full_content)

    def get_doc_key(self, top_key):
        """
        Return the value of a top-level key in any YAML document.
        Returns None if not found.
        """
        list_item = next((doc for doc in self.level0 if top_key in doc.value), None)
        if list_item is None:
            return None
        return list_item[top_key]
        
    def get_element_by_id(id_):
        for doc_i in range(0, len(self.level0)):
            if "&" in self.level0[doc_i]:
                if self.level0[doc_i].split("&")[1] == id_:
                    return self.level0[doc_i + 1]
            

def set_ID(text: str, new_id: str=None) -> str:
    """ Changes the ID in the anchor line """
    text.anchor = new_id
    return new_id
    
    print(text)
    non_id = text.split("&")[0]
    if not new_id:
        new_id = str(random.int(1000000000, 9999999999))
    non_id += "&" + new_id
    return text.anchor, new_id


        
def get_guid(meta_file: str) -> str:
    """Returns the 'guid' property from a Unity .meta YAML file."""
    with open(meta_file, "r") as f:
        data = yaml.safe_load(f)
    
    # Ensure 'guid' exists
    if "guid" not in data:
        raise KeyError(f"'guid' not found in {meta_file}")
    
    return data["guid"]
        
scene_init_text = """

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
    - target: {fileID: 0}
      propertyPath: m_LocalPosition.x
      value: -1045.3981
      objectReference: {fileID: 0}
    - target: {fileID: 7746927824541037661, guid: 1f9036ec905b920479091aca9ba81305, type: 3}
      propertyPath: m_LocalPosition.y
      value: 2190.1765
      objectReference: {fileID: 0}
    - target: {fileID: 7746927824541037661, guid: 1f9036ec905b920479091aca9ba81305, type: 3}
      propertyPath: m_LocalPosition.z
      value: 3885.3948
      objectReference: {fileID: 0}
    - target: {fileID: 7746927824541037661, guid: 1f9036ec905b920479091aca9ba81305, type: 3}
      propertyPath: m_LocalRotation.w
      value: 1
      objectReference: {fileID: 0}
    - target: {fileID: 7746927824541037661, guid: 1f9036ec905b920479091aca9ba81305, type: 3}
      propertyPath: m_LocalRotation.x
      value: 0
      objectReference: {fileID: 0}
    - target: {fileID: 7746927824541037661, guid: 1f9036ec905b920479091aca9ba81305, type: 3}
      propertyPath: m_LocalRotation.y
      value: 0
      objectReference: {fileID: 0}
    - target: {fileID: 7746927824541037661, guid: 1f9036ec905b920479091aca9ba81305, type: 3}
      propertyPath: m_LocalRotation.z
      value: 0
      objectReference: {fileID: 0}
    - target: {fileID: 7746927824541037661, guid: 1f9036ec905b920479091aca9ba81305, type: 3}
      propertyPath: m_LocalEulerAnglesHint.x
      value: 0
      objectReference: {fileID: 0}
    - target: {fileID: 7746927824541037661, guid: 1f9036ec905b920479091aca9ba81305, type: 3}
      propertyPath: m_LocalEulerAnglesHint.y
      value: 0
      objectReference: {fileID: 0}
    - target: {fileID: 7746927824541037661, guid: 1f9036ec905b920479091aca9ba81305, type: 3}
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
