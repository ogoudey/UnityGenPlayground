from worldgen import UnityWorldGen
from worldgen import Class_from_Asset_Project

from distutils.util import strtobool
import asyncio
from typing import List
import sys

async def process(arg_tuple: List[str]):
    asset_project = arg_tuple[0]
    Class = Class_from_Asset_Project[arg_tuple[0]]
    prompt = arg_tuple[1]
    scene_name = arg_tuple[2]
    if strtobool(arg_tuple[3]):
        world_gen = Class(asset_project, False, scene_name)
    else:
        world_gen = UnityWorldGen(asset_project, scene_name)
    await world_gen.load()
    await world_gen.run(prompt)


# bashArgs = $"\"{scriptPath}\" \"{assetProject}\" \"{promptText}\" \"{generationName}\" \"{use_asset_project_generator_class.ToString()}\"";

def main():
    arg_tuple = sys.argv[1:]
    asyncio.run(process(arg_tuple))
    
    

if __name__ == "__main__":
    main()