import os
import json

from agents import Agent, Runner
import asyncio

MODEL = (os.getenv("MODEL") or "o3-mini").strip() or "o3-mini"

def load(assets_info):
    with open("synopsis_file.json", "r") as s:
        v = s.read()
        synopses = json.loads(v)
    print(f"\n* Synopsis file loaded with {len(synopses)} entries")
    asyncio.run(update_synopsis_file(assets_info, synopses))
    return synopses

async def update_synopsis_file(assets_info, synopses):
    i = 1
    updates_needed = len(assets_info) - len(synopses)
    for asset_path, asset_info in assets_info.items():
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
    print("* Synopsis file up to date.")
    if updates_needed > 0:
        with open("synopsis_file.json", "w") as s:
            output_str = json.dumps(synopses, indent=2)
            s.write(output_str)
            print("Synopsis file updated.")
    unrepresented_assets = 0
    for synopsis, ante_asset_path in synopses.items():
        found = False
        for asset_path in list(assets_info.keys()):
            if ante_asset_path == asset_path:
                found = True
        if not found:
            unrepresented_assets += 1
            del synopses[synopsis]
    if unrepresented_assets > 0:
        print(f"{len(unrepresented_assets)} marked as irrelevant because the assets are not imported.")
        
    # synopses updated


async def generate_synopsis(asset_info):
    synopsis_generator = Agent(
        name="SynopsisGenerator",
        instructions = "Give a brief description of the asset, given supplied info. Context: You are describing a .prefab asset for a Unity world. Later these synopses will be used to assist retrieval of the asset based on a new desired description. For example, later, something like 'a small rock with moss' will be passed to an agent who then looks at synopses like the one you are generating and returns the corresponding asset info. So keep it brief. Put your answer as a 'noun phrase' - no 'this object is...' but rather 'a rock with such and such...'",
        model=MODEL
    )
    prompt = {"Asset info": asset_info}
    result = await Runner.run(synopsis_generator, json.dumps(prompt))
    return result.final_output
