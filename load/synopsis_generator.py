#############################################################################
#
#   Module responsible for loading the synopses, the summaries of the asset catalog
#
#############################################################################





import os
import json

from logger import log

from agents import Agent, Runner
import asyncio

MODEL = (os.getenv("MODEL") or "o3-mini").strip() or "o3-mini"

async def load(assets_folder, asset_catalog):
    try:
        with open(assets_folder / "synopsis_file.json", "r") as s:
            v = s.read()
            synopses = json.loads(v)
    except FileNotFoundError:
        found = ""
        for name in os.listdir(assets_folder):
            if not name.endswith(".meta"):
                found += f"\n\t{name}"
        raise FileNotFoundError(f"The specified Assets folder ({assets_folder}) has no synopses file:{found}\n\nIf you would like to generate one, make an empty `synopsis.json` there.")
    log(f"Synopsis file loaded with {len(synopses)} entries")
    active_synopses = await update_synopsis_file(assets_folder, asset_catalog, synopses)
    return active_synopses

async def update_synopsis_file(assets_folder, asset_catalog, synopses) -> dict[str, str]:
    i = 0
    updates_needed = len(asset_catalog) - len(synopses)
    for asset_path, asset_info in asset_catalog.items():
        found = False
        for synopsis, ante_asset_path in synopses.items():
            if ante_asset_path == asset_path:
                found = True
                break # on to next asset
        if found == True:
            continue
        else:
            print(asset_path, "not found in synopses...")
            print(f"Generating synopsis... {i}/{updates_needed}")
            i += 1
            new_synopsis = await generate_synopsis(asset_info)
            synopses[new_synopsis] = asset_path
            print(asset_info)
            print("------>", new_synopsis)
    print("Synopsis file up to date.")
    if updates_needed > 0:
        with open(assets_folder / "synopsis_file.json", "w") as s:
            output_str = json.dumps(synopses, indent=2)
            s.write(output_str)
            print("Synopsis file updated.")
    represented_assets = dict()
    unrepresented_assets = []
    for synopsis, ante_asset_path in synopses.copy().items():
        found = False
        for asset_path in list(asset_catalog.keys()):
            if ante_asset_path == asset_path:
                found = True
                represented_assets[synopsis] = ante_asset_path
        if not found:
            unrepresented_assets.append(ante_asset_path)
    if len(unrepresented_assets) > 0:
        legible1, legible2 = "", ""
        for asset in unrepresented_assets:
            legible1 += f"\n\t{asset}"
        for asset in list(asset_catalog.keys()):
            legible2 += f"\n\t{asset}"
        
        print(f"Annotated assets: {legible2}")
        print(f"The following asset are marked as irrelevant because the assets are not imported:\n{legible1}")
    return represented_assets
    # synopses updated


async def generate_synopsis(asset_info):
    synopsis_generator = Agent(
        name="SynopsisGenerator",
        instructions = "Give a brief description of the asset, given supplied info. Context: You are describing a .prefab asset for a Unity world. Later these synopses will be used to assist retrieval of the asset based on a new desired description. If you include measurement information in the synopsis, be sure its accurate. For example, later, something like 'a small rock with moss' will be passed to an agent who then looks at synopses like the one you are generating and returns the corresponding asset info. So keep it brief. Put your answer as a 'noun phrase' - no 'this object is...' but rather 'a rock with such and such...'",
        model=MODEL
    )
    prompt = {"Asset info": asset_info}
    result = await Runner.run(synopsis_generator, json.dumps(prompt))
    return result.final_output
