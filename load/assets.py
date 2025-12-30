#############################################################################
#
#   Responsible for loading the assets from the asset catalog.
#
#############################################################################

import subprocess
import os
import fnmatch
import re
from pathlib import Path
from collections import defaultdict
import json
from typing import List
from logger import log

def load(assets_folder: Path) -> dict[str, str]:
    try:
        name_of_asset_catalog = "asset_catalog.json"
        with open(assets_folder / name_of_asset_catalog, "r") as f:
            j = f.read()
            asset_catalog = json.loads(j)
    except FileNotFoundError:
        found = ""
        for name in os.listdir(assets_folder):
            if not name.endswith(".meta"):
                found += f"\n\t{name}"
        raise FileNotFoundError(f"The specified Assets folder ({assets_folder}) has no asset catalog:{found}\n\nYou must provide an `asset_catalog.json` there.")
    print(f"In asset project folder {assets_folder}")
    log(f"In asset project folder {assets_folder}, asset catalog loaded with {len(asset_catalog)} entries")
    
    removed_count = 0
    for assets_relative_str_path in list(asset_catalog.keys()):
        if not os.path.exists(assets_folder / assets_relative_str_path):
            print(f"Removing {assets_relative_str_path} because {assets_folder / assets_relative_str_path} does not exist")
            del asset_catalog[assets_relative_str_path]
            removed_count += 1

    if removed_count > 0:
        print(f"Removed {removed_count} missing assets")
    else:
        print("All asset catalog entries accounted for in folders.")

    return asset_catalog

def get_found(file_type:str, assets: Path) -> List[str]:
    print(f"Looking in {assets} for {file_type}...")
    if os.name == 'nt':
        matches = []
        for root, _, files in os.walk(asset_project_path):
            for name in files:
                if fnmatch.fnmatch(name, f"*{file_type}"):
                    matches.append(os.path.join(root, name))
    elif os.name == 'posix':
        result = subprocess.run(
            ["find", assets.as_posix(), "-type", "f", "-name", f"*{file_type}"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0 or not result.stdout.strip():
            # Either the command failed or no files found
            #print(f"!! {assets} was not found. Consider adding to the file system.")
            raise FileNotFoundError(f"\nThe world generator has requested a special folder, but the specified folder ({assets}) could not be found, OR no {file_type}-s could be found in them.\nYou must add this folder to Assets, and add at least one {file_type} to the folder, or change the environment variables or use another generator class.\nNote: if the materials are pink, go to Window>Rendering>Render Pipeline Converter>Material Upgrade>Initialize and Convert.")
        
        # Split into list of file paths, strip whitespace
        matches = [line.strip() for line in result.stdout.splitlines() if line.strip()]

    # Normalize paths (optional, makes everything consistent)
    files = [Path(f).as_posix() for f in matches]
    if len(files) > 0:
        log(f"The folder at {assets} has {len(files)} {file_type} assets.")
    else:
        log(f"The folder at {assets} has no files of type {file_type}!")
        print(f"\033[1m\033[31mThe folder at {assets} has no files of type {file_type}!\033[0m")
    return files

def get_tree(file_type=".prefab", folder="../Assets"):
    if os.name == 'nt':
        return "..."
    result = subprocess.run(
        ["tree", "-P", "*" + file_type, folder],
        capture_output=True,
        text=True
    )

    assets = result.stdout

    return assets






def describe_obj_bounding_box(obj_path: str) -> str:
    """
    Parses a .obj file and returns a phrase describing its bounding box. Not currently used.
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