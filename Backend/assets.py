"""import subprocess

def parse_resources():

    folder = "../Assets/Proxy Games"

    result = subprocess.run(
        ["tree", folder],
        capture_output=True,
        text=True
    )

    resources = result.stdout
    return resources

resources = parse_resources()
"""

import os
import re

from collections import defaultdict

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
print(f"Found {len(list_of_important_metadata_dicts)} entries:")
for entry in list_of_important_metadata_dicts:
    print(entry)

resources = str(list_of_important_metadata_dicts)




