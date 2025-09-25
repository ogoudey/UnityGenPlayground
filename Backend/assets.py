import subprocess
import os
import re
import pathlib
from collections import defaultdict

def load()
    with open("asset_info.json", "r") as f:
        j = f.read()
        assets_info = json.loads(j)
    print(f"\nAsset info sheet loaded with {len(assets_info)} entries")
    return assets_info


def get_tree(file_type=".prefab", folder="../Assets"):
    folder = "../Assets"

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

    # Split into list of file paths, strip whitespace
    files = [line.strip() for line in result.stdout.splitlines() if line.strip()]

    # Normalize paths (optional, makes everything consistent)
    files = [str(pathlib.Path(f).as_posix()) for f in files]
    print(f"\n\tThere are {len(files)} files of type {file_type} in this static library.")
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

list_of_important_metadata_dicts = parse_assets()


resources = str(list_of_important_metadata_dicts)




