import sys
import os
import time
from threading import Thread

#from flask import Flask, send_from_directory, jsonify, request
#from flask_cors import CORS

import json
import random

import asyncio
from agents import Runner
import coordinator as agents
from enrichment import Therapist, Transducer
from coordinator import Checker, Reformer, Coordinator
from tools import get_ground_matrix, planObject, placeObject, place_vr_human_player, planSkybox, placeSkybox, placeGround, get_contact_points, planGround, planandplaceSun

from scene import UnityFile

async def test_river_bridge(prompt="A 5m deep river cutting through a terrain with some foliage, and a bridge going over it connecting two banks."):
    scene_suffix = "draft1"
    scene_name = f"test_river_bridge{random.randint(100, 999)}{scene_suffix}"
    agents.tools.unity = UnityFile(scene_name)
    
    coordinator = Coordinator(tools=[get_contact_points, planSkybox, placeSkybox, planGround, placeGround, planObject, placeObject, planandplaceSun])
    prompt = {"Description of the scene": prompt}
    print("\n__Starting Coordinator___")
    await Runner.run(coordinator, json.dumps(prompt), max_turns=20)
    agents.tools.unity.done_and_write()
    
    
    scene_suffix = "draft2"
    scene_name = f"test_river_bridge{random.randint(100, 999)}{scene_suffix}"
    agents.tools.unity.name = scene_name
    print("\n\n__Checking__\nGoing through used assets:", agents.tools.unity.yaml.placed_assets)
    checker = Checker()
    feedback = {}
    for asset_name, placement in agents.tools.unity.yaml.placed_assets.items():
        print(f"Checking {asset_name}...")
        if asset_name in list(agents.tools.unity.yaml.used_assets.keys()):
            path = agents.tools.unity.yaml.used_assets[asset_name]
            reference_info = agents.tools.assets_info[path]
        elif "ground" in asset_name:
            reference_info = {"grid": agents.tools.unity.ground_matrix, "other info": "scaled by 5 and covering the -X +Z quadrant. 50m by 50m."}
        else:
            reference_info = None
            print(asset_name, "not in asset info sheet.")
        prompt = {"Reference info": reference_info, "Actual placement": placement}
        result = await Runner.run(checker, json.dumps(prompt), max_turns=10)
        check_status = result.final_output.check_status
        reason = result.final_output.reason
        if not check_status:
            feedback[asset_name] = reason
    print(feedback)

    reformer = Reformer()
    print("__Revising started__")
    print(f"Giving feedback on {len(feedback)} objects...")
    prompt = {"Feedback": feedback}
    result = await Runner.run(reformer, json.dumps(prompt), max_turns=10)
    print(f"{result.final_output}")
    agents.tools.unity.done_and_write()

async def test_river_bridge_vr(prompt="A 5m deep river cutting through a terrain with some foliage, and a bridge going over it connecting two banks."):
    scene_suffix = "draft1"
    scene_name = f"test_river_bridge_vr{random.randint(100, 999)}{scene_suffix}"
    agents.tools.unity = UnityFile(scene_name)
    
    coordinator = Coordinator(tools=[get_contact_points, planSkybox, placeSkybox, planGround, placeGround, planObject, placeObject, planandplaceSun, place_vr_human_player])
    prompt = {"Description of the scene": prompt}
    print("\n__Starting Coordinator___")
    await Runner.run(coordinator, json.dumps(prompt), max_turns=20)
    agents.tools.unity.done_and_write()


async def test_vr(prompt="Just try placing the player in 3D space"):
    scene_suffix = "draft1"
    scene_name = f"test_vr{random.randint(100, 999)}{scene_suffix}"
    agents.tools.unity = UnityFile(scene_name)
    
    coordinator = Coordinator(tools=[place_vr_human_player])
    prompt = {"Description of the scene": prompt}
    print("\n__Starting Coordinator___")
    await Runner.run(coordinator, json.dumps(prompt), max_turns=20)
    agents.tools.unity.done_and_write()
    

async def test_light_and_texture(prompt="A blue sky with a bright sun high in the skynoon over a ground with any texture."):
    scene_suffix = "draft1"
    scene_name = f"test_light_and_texture{random.randint(100, 999)}{scene_suffix}"
    agents.tools.unity = UnityFile(scene_name)
    
    
    coordinator = Coordinator(instructions="You are generating a Unity world given the prompt. Use the tool planGround to generate a heightmap with a description of the ground, and place the ground with placeGround. Then, place the sun with the planandplaceSun tool. Simply describe the desired Sun theme. Call each tool once.", tools=[planGround, placeGround, planandplaceSun])
    prompt = {"Description of the scene": prompt}
    print("\n__Starting Coordinator___")
    t = time.time()
    await Runner.run(coordinator, json.dumps(prompt), max_turns=20)
    print(coordinator.name + ":", time.time() - t, "seconds.")
    agents.tools.unity.done_and_write()

async def test_therapist(prompt="I'm scared of heights over 5m. I just can't do bridges."):
    scene_suffix = "draft1"
    scene_name = f"test_therapist{random.randint(100, 999)}{scene_suffix}"
    #agents.tools.unity = UnityFile(scene_name)
    
    therapist = Therapist()
    print("__Starting Therapist__")
    result = await Runner.run(therapist, prompt, max_turns=2)
    #agents.tools.unity.done_and_write()
    print(result.final_output)
    
async def test_transduction(prompt="I'm scared of heights over 5m. I just can't do bridges."):
    scene_suffix = "draft1"
    scene_name = f"test_transduction{random.randint(100, 999)}{scene_suffix}"
    #agents.tools.unity = UnityFile(scene_name)
    
    therapist = Therapist()
    print("__Starting Therapist__")
    result = await Runner.run(therapist, prompt, max_turns=2)
    transducer = Transducer()
    print("__Starting Transducer__")
    result = await Runner.run(transducer, result.final_output, max_turns=2)
    #agents.tools.unity.done_and_write()
    print(result.final_output)

async def test_cumulative(prompt="I'm scared of heights over 5m. I just can't do bridges."):
    scene_suffix = "draft1"
    scene_name = f"test_cumulative{random.randint(100, 999)}{scene_suffix}"
    #agents.tools.unity = UnityFile(scene_name)
    
    therapist = Therapist()
    print("__Starting Therapist__")
    result = await Runner.run(therapist, prompt, max_turns=2)
    transducer = Transducer()
    print("__Starting Transducer__")
    result = await Runner.run(transducer, result.final_output, max_turns=2)
    #agents.tools.unity.done_and_write()
    scene_generating_plan = result.final_output
    
    agents.tools.unity = UnityFile(scene_name)
    coordinator = Coordinator() # all the tools
    prompt = {"Plan": scene_generating_plan}
    print("__Starting Coordinator___")
    await Runner.run(coordinator, json.dumps(prompt), max_turns=20)
    agents.tools.unity.done_and_write()    

test_dispatcher = {
    # = deprecated test
    "test_river_bridge": test_river_bridge, # outputs 2 drafts
    "test_light_and_texture": test_light_and_texture,
    "test_therapist": test_therapist,
    "test_transduction": test_transduction,
    "test_cumulative": test_cumulative,
    #"test_vr": test_river_bridge_vr,
    "test_river_bridge_vr": test_river_bridge_vr,
    "test_vr": test_vr,
}

if __name__ == "__main__":
    if sys.argv[1]:
        try:
            test_function = test_dispatcher[sys.argv[1]]
        except KeyError("Invalid test name. Choose from: " + str(list(test_dispatcher.keys()))):
            sys.exit(1)
        asyncio.run(test_function())   
    else:
        print("Please include test from:", list(test_dispatcher.keys()))


















