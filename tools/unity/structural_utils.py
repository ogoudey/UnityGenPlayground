from pathlib import Path
import re
from typing import List, Any

import random
import yaml as pyyaml
import math

from ruamel.yaml import YAML as ruamel_YAML
from ruamel.yaml.nodes import ScalarNode, MappingNode, SequenceNode

##### In pipeline #######

def load_structure(structure_type: str) -> str:
    p = Path("tools/unity/structures") / structure_type
    return p.with_suffix(".yaml").read_text()

def compose(initializing_text: str) -> List[MappingNode]:
    """ Then parse the structure into a composition of nodes. """
    def preprocess_text(text: str) -> str:
        return re.sub(r"!u!(\d+)", r"!UnityTag\1", text)

    yaml = ruamel_YAML(typ='rt')
    return list(yaml.compose_all(preprocess_text(initializing_text)))

def node_to_python(node: MappingNode) -> Any:
    """ Then turn the composition into a usable arrangement of Python objects """
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
        print(f"Weird node detected: {type(node)}")
        print(node)
        return None

#### Helpers ####

def get_doc(wrapped, top_key):
        """
        Return the value of a top-level key self.wrapped.
        Returns None if not found.
        """
        list_item = next((doc for doc in wrapped if top_key in doc.keys()), None)
        if list_item is None:
            return None
        return list_item[top_key]

def get_guid(file: Path) -> str:
    """Returns the 'guid' property from a file."""
    meta_file = file.with_suffix(file.suffix + ".meta")
    #log(f"Converting {file} to {meta_file}. Opening META...")
    with open(meta_file, "r") as f:
        data = pyyaml.safe_load(f)
    #log(f"Opened {meta_file} and returning guid")    # Ensure 'guid' exists
    if "guid" not in data:
        raise KeyError(f"'guid' not found in {meta_file}")
    return data["guid"]

def get_father_id_of_root_transform_of_prefab(prefab_path: str):
        with open(prefab_path, "r") as f:
            prefab_file = f.read()
        nodes = compose(prefab_file)
        wrapped = [node_to_python(n) for n in nodes]
        for doc in wrapped:
            if "Transform" in doc.keys():
                if doc["Transform"]["m_Father"]["fileID"] == "0":
                    father_id = doc["anchor"]
        if not father_id:
            raise KeyError("The located prefab has no root transform")
        return father_id

def set_ID(text: MappingNode, new_id: str="") -> tuple[MappingNode, str]:
    """ Changes the ID in the anchor line """
    if new_id == "":
        new_id = str(random.randint(1000000000, 9999999999))
    if "anchor" in text.keys():
        text["anchor"] = new_id
    else:
        raise ValueError("No anchor to be set!")
    return text, new_id

def euler_to_xyzw_quaternion(rotation: dict) -> tuple:
    x_deg, y_deg, z_deg = rotation["x"], rotation["y"], rotation["z"]

    # Convert degrees to radians
    x = math.radians(float(x_deg))
    y = math.radians(float(y_deg))
    z = math.radians(float(z_deg))

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
    #print("Calculation of quaternion done:", (qx, qy, qz, qw))
    return (qx, qy, qz, qw)      



##### Out pipeline #####



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
