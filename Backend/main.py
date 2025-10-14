import sys
import os
import time
from threading import Thread
from pathlib import Path

#from flask import Flask, send_from_directory, jsonify, request
#from flask_cors import CORS

import json
import random

import asyncio

import coordinator as agents



from worldgen import AcrophobiaWorldGen, VRWorldGen

MODEL = (os.getenv("MODEL") or "o3-mini").strip() or "o3-mini"  


async def test_acrophobia_bridge():
    gen = AcrophobiaWorldGen()
    await gen.load()
    await gen.run(AcrophobiaWorldGen.bridge_prompt)

async def test_acrophobia_mountain():
    gen = AcrophobiaWorldGen()
    await gen.load()
    await gen.run(AcrophobiaWorldGen.mountain_prompt)

async def test_acrophobia_skyscraper():
    gen = AcrophobiaWorldGen()
    await gen.load()
    await gen.run(AcrophobiaWorldGen.skyscraper_prompt)

async def test_acrophobia_building():
    gen = AcrophobiaWorldGen()
    await gen.load()
    await gen.run(AcrophobiaWorldGen.building_prompt)

async def test_acrophobia_roof():
    gen = AcrophobiaWorldGen()
    await gen.load()
    await gen.run(AcrophobiaWorldGen.roof_prompt)

async def test_acrophobia_platform():
    gen = AcrophobiaWorldGen()
    await gen.load()
    await gen.run(AcrophobiaWorldGen.platform_prompt)

### General test
async def test_acrophobia_emulate():
    gen = AcrophobiaWorldGen()
    await gen.load()
    prompt = gen.get_prompt()
    print("Prompt:", prompt)
    await gen.run(prompt)
###

### Shap-E Test
async def test_shap_e():
    gen = VRWorldGen(asset_project_path=Path("../Resources/Asset Projects/Shap-E"), scene_name=f"acro_{MODEL}_{random.randint(100, 999)}", )
    await gen.run(input("\n\tPrompt: "))
###


test_dispatcher = {
    # = deprecated test
    "test_acro_bridge": test_acrophobia_bridge,
    "test_acro_mountain": test_acrophobia_mountain,
    "test_acro_skyscraper": test_acrophobia_skyscraper,
    "test_acro_building": test_acrophobia_building,
    "test_acro_roof": test_acrophobia_roof,
    "test_acro_platform": test_acrophobia_platform,
    "test_acro_em": test_acrophobia_emulate,
    "test_shap_e": test_shap_e,
}

if __name__ == "__main__":
    if sys.argv[1]:
        try:
            test_function = test_dispatcher[sys.argv[1]]
        except Exception("Invalid test name. Choose from: " + list(test_dispatcher.keys())):
            sys.exit(1)
        asyncio.run(test_function())   
    else:
        print("Please include test from:", list(test_dispatcher.keys()))


















