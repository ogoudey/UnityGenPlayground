from worldgen import AcrophobiaWorldGen, VRWorldGen, Acrophobia50mx50mWorldGen
from worldgen import Class_from_Asset_Project

import asyncio
from typing import List
import sys

async def process(arg_tuple: List[str]):
    asset_project = arg_tuple[0]
    Class = Class_from_Asset_Project[arg_tuple[0]]
    prompt = arg_tuple[1]
    scene_name = arg_tuple[2]
    if len(arg_tuple) > 3:
        prompt = arg_tuple[4]
    world_gen = Class(asset_project, False, scene_name)
    await world_gen.load()
    await world_gen.run(prompt)



def main():
    arg_tuple = sys.argv[1:]
    asyncio.run(process(arg_tuple))
    
    

if __name__ == "__main__":
    main()