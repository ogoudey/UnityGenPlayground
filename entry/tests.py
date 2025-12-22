import sys
import os
import time
from threading import Thread
from pathlib import Path

import json
import random

import asyncio
from logger import log
from generating.world import UnityWorld
from generating.worldgen import AcrophobiaWorldGen, VRWorldGen, Acrophobia50mx50mWorldGen
from llms.orchestra import Conductor
from llms.orchestra import instruments
from agents import Runner

MODEL = (os.getenv("MODEL") or "o3-mini").strip() or "o3-mini"  

if __name__ == "__main__":    
    path = str(self.asset_project_path / "Assets" / "Scenes" / self.scene_name) # should stringify later?
    scene_path = instruments.unity.done_and_write(path)
    print(f"Scene @ {scene_path}")
    print(f"Coordinator response: \n{result.final_output}")
    log(result.final_output)
    log(f"World generated at {scene_path}", type="bold")

    try:
        test = sys.argv[1]
        try:
            test_function = test_dispatcher[test]
        except KeyError:
            raise KeyError(f"Invalid test name. Choose from:\n{list(test_dispatcher.keys())}")
            sys.exit(1)
        if len(sys.argv) > 2:
            asset_project = sys.argv[2]
            asyncio.run(test_function(asset_project))
        else:
            asyncio.run(test_function())  # default per WorldGen subclass
    except IndexError:
        print("Please include test from:", list(test_dispatcher.keys()))