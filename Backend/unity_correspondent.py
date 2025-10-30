from worldgen import UnityWorldGen
from worldgen import Generator_Class_from_Asset_Project_Name

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
    log("Beginning generation of Unity World...", scene_name)
    if strtobool(arg_tuple[3]):
        print(f"{Class} is generating scene {scene_name}")
        world_gen = Class(asset_project, False, scene_name)
    else:
        print(f"{Class} is generating scene {scene_name}")
        world_gen = UnityWorldGen(asset_project, scene_name)
    await world_gen.load()
    await world_gen.run(prompt)
    done(scene_name)

# bashArgs = $"\"{scriptPath}\" \"{assetProject}\" \"{promptText}\" \"{generationName}\" \"{use_asset_project_generator_class.ToString()}\"";

def main():
    arg_tuple = sys.argv[1:]
    asyncio.run(process(arg_tuple))
    
    

if __name__ == "__main__":
    main()