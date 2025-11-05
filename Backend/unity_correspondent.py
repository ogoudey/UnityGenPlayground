from worldgen import UnityWorldGen
from worldgen import Generator_Class_from_Asset_Project_Name
import os
from distutils.util import strtobool
import asyncio
from typing import List
import sys
from logger import done, log

async def process(arg_tuple: List[str]):
    asset_project = arg_tuple[0]
    Class = Generator_Class_from_Asset_Project_Name[arg_tuple[0]]
    prompt = arg_tuple[1]
    scene_name = arg_tuple[2]
    if len(arg_tuple) > 3:
        if not strtobool(arg_tuple[3]):
            Class = UnityWorldGen
    log(f"Arguments interpreted: {asset_project} {Class} {prompt} {scene_name}", scene_name)
    log(f"Python user: {os.getlogin()}", scene_name)
    log(f"CWD: {os.getcwd()}", scene_name)
    log("Beginning generation of Unity World...", scene_name)
    world_gen = Class(asset_project, scene_name)
    await world_gen.load()
    await world_gen.run(prompt)
    done(scene_name)

# bashArgs = $"\"{scriptPath}\" \"{assetProject}\" \"{promptText}\" \"{generationName}\" \"{use_asset_project_generator_class.ToString()}\"";

def main():
    arg_tuple = sys.argv[1:]
    asyncio.run(process(arg_tuple))
    
    

if __name__ == "__main__":
    main()