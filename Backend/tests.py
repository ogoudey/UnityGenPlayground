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

from worldgen import AcrophobiaWorldGen, VRWorldGen, Acrophobia50mx50mWorldGen

MODEL = (os.getenv("MODEL") or "o3-mini").strip() or "o3-mini"  


async def test_acrophobia_bridge():
    gen = Acrophobia50mx50mWorldGen()
    await gen.load()
    await gen.run(Acrophobia50mx50mWorldGen.bridge_prompt)

async def test_acrophobia_mountain():
    gen = Acrophobia50mx50mWorldGen()
    await gen.load()
    await gen.run(AcrophobiaWorldGen.mountain_prompt)

async def test_acrophobia_skyscraper():
    gen = Acrophobia50mx50mWorldGen()
    await gen.load()
    await gen.run(Acrophobia50mx50mWorldGen.skyscraper_prompt)

async def test_acrophobia_building():
    gen = Acrophobia50mx50mWorldGen()
    await gen.load()
    await gen.run(Acrophobia50mx50mWorldGen.building_prompt)

async def test_acrophobia_roof():
    gen = Acrophobia50mx50mWorldGen()
    await gen.load()
    await gen.run(Acrophobia50mx50mWorldGen.roof_prompt)

async def test_acrophobia_platform():
    gen = Acrophobia50mx50mWorldGen()
    await gen.load()
    await gen.run(Acrophobia50mx50mWorldGen.platform_prompt)

async def test_acrophobia_bridge_regime():
    gen = Acrophobia50mx50mWorldGen()
    await gen.load()
    await gen.regime(Acrophobia50mx50mWorldGen.bridge_regime_prompt)

async def test_acrophobia_bridge_pro():
    gen = AcrophobiaWorldGen()
    await gen.load()
    await gen.run(AcrophobiaWorldGen.bridge_prompt)

async def test_acrophobia_mountain_pro():
    gen = AcrophobiaWorldGen()
    await gen.load()
    await gen.run(AcrophobiaWorldGen.mountain_prompt)

async def test_acrophobia_skyscraper_pro():
    gen = AcrophobiaWorldGen()
    await gen.load()
    await gen.run(AcrophobiaWorldGen.skyscraper_prompt)

async def test_acrophobia_building_pro():
    gen = AcrophobiaWorldGen()
    await gen.load()
    await gen.run(AcrophobiaWorldGen.building_prompt)

async def test_acrophobia_roof_pro():
    gen = AcrophobiaWorldGen()
    await gen.load()
    await gen.run(AcrophobiaWorldGen.roof_prompt)

async def test_acrophobia_platform_pro():
    gen = AcrophobiaWorldGen()
    await gen.load()
    await gen.run(AcrophobiaWorldGen.platform_prompt)

async def test_acrophobia_bridge_regime_pro():
    gen = AcrophobiaWorldGen()
    await gen.load()
    await gen.regime(AcrophobiaWorldGen.bridge_regime_prompt)

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
    "test_regime": test_acrophobia_bridge_regime,
}

if __name__ == "__main__":
    try:
        test = sys.argv[1]
        try:
            test_function = test_dispatcher[test]
        except Exception("Invalid test name. Choose from: " + str(list(test_dispatcher.keys()))):
            sys.exit(1)
        asyncio.run(test_function())   
    except IndexError:
        print("Please include test from:", list(test_dispatcher.keys()))


















