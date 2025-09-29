import subprocess
import os
import re
import pathlib
from collections import defaultdict
import json


def load():
    with open("asset_info.json", "r") as f:
        j = f.read()
        assets_info = json.loads(j)
    print(f"\n* Asset info sheet loaded with {len(assets_info)} entries")
    
    
    removed_count = 0
    for key in list(assets_info.keys()):
        if not os.path.exists(key):
            del assets_info[key]
            removed_count += 1

    if removed_count > 0:
        print(f"* Removed {removed_count} missing assets")
    else:
        print("* No missing assets found")

    return assets_info



def get_tree(file_type=".prefab", folder="../Assets"):

    result = subprocess.run(
        ["tree", "-P", "*" + file_type, folder],
        capture_output=True,
        text=True
    )

    assets = result.stdout

    return assets



def get_found(file_type=".prefab", folder="../Assets"):
    result = subprocess.run(
        ["find", folder, "-type", "f", "-name", f"*{file_type}"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0 or not result.stdout.strip():
        # Either the command failed or no files found
        print(f"* !! {folder} was not found. Consider adding to the file system.")
        return []
        
    # Split into list of file paths, strip whitespace
    files = [line.strip() for line in result.stdout.splitlines() if line.strip()]

    # Normalize paths (optional, makes everything consistent)
    files = [str(pathlib.Path(f).as_posix()) for f in files]
    print(f"\n* The library at {folder} has {len(files)} {file_type} assets.")
    return files






# List of metadata fields to extract
important_data = ["GUID", "fileID"]

def parse_assets(folder="../Assets/Proxy Games"):
    asset_metadata = defaultdict(lambda: {"GUID": None, "fileIDs": set()})

    for root, dirs, files in os.walk(folder):
        for file in files:
            file_path = os.path.join(root, file)

            if not (file.endswith(".meta") or file.endswith(".prefab") or file.endswith(".unity")):
                continue
            
            if "/Scenes/" in file_path.replace("\\", "/"):  # handle Windows paths too
                continue
            
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

                # GUIDs from .meta files
                if file.endswith(".meta"):
                    guid_match = re.search(r"guid: ([0-9a-f]{32})", content)
                    if guid_match:
                        try:
                            truncated_path = file_path.split("Stylized Nature Kit Lite/")[-1]
                        except IndexError:
                            truncated_path = file_path  # fallback
                        asset_metadata[truncated_path]["GUID"] = guid_match.group(1)

                # fileIDs from YAML files (.prefab or .unity)
                else:
                    fileid_matches = re.findall(r"fileID: (\d+)", content)
                    for fid in fileid_matches:
                        if fid != "0":  # ignore fileID=0
                            asset_metadata[file_path]["fileIDs"].add(fid)

    # Convert sets to lists for easier output
    final_metadata = []
    for file, data in asset_metadata.items():
        try:
            truncated_path = file_path.split("Stylized Nature Kit Lite/")[-1]
        except IndexError:
            truncated_path = file_path  # fallback
        final_metadata.append({
            "file": truncated_path,
            "GUID": data["GUID"],
            "fileIDs": list(data["fileIDs"])
        })

    return final_metadata

def describe_obj_bounding_box(obj_path: str) -> str:
    """
    Parses a .obj file and returns a phrase describing its bounding box.
    """
    min_x = min_y = min_z = float('inf')
    max_x = max_y = max_z = float('-inf')

    with open(obj_path, 'r') as f:
        for line in f:
            if line.startswith('v '):  # vertex line
                parts = line.strip().split()
                if len(parts) >= 4:
                    x, y, z = map(float, parts[1:4])
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    min_z = min(min_z, z)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)
                    max_z = max(max_z, z)

    if min_x == float('inf'):
        return "No vertex data found in the OBJ file."

    return (
        f"The bounding box is:\n"
        f"  X: {min_x:.3f} to {max_x:.3f}\n"
        f"  Y: {min_y:.3f} to {max_y:.3f}\n"
        f"  Z: {min_z:.3f} to {max_z:.3f}"
    )


list_of_important_metadata_dicts = parse_assets()


resources = str(list_of_important_metadata_dicts)




