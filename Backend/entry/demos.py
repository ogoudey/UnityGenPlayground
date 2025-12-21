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

import Backend.agents.orchestra as agents

from Backend.generating.worldgen import AcrophobiaWorldGen, VRWorldGen, Acrophobia50mx50mWorldGen

MODEL = (os.getenv("MODEL") or "o3-mini").strip() or "o3-mini"  


async def test_acrophobia_bridge(ap=None):
    gen = Acrophobia50mx50mWorldGen() if ap is None else Acrophobia50mx50mWorldGen(ap)
    await gen.load()
    await gen.run(Acrophobia50mx50mWorldGen.bridge_prompt)

async def test_acrophobia_mountain(ap=None):
    gen = Acrophobia50mx50mWorldGen() if ap is None else Acrophobia50mx50mWorldGen(ap)
    await gen.load()
    await gen.run(AcrophobiaWorldGen.mountain_prompt)

async def test_acrophobia_skyscraper(ap=None):
    gen = Acrophobia50mx50mWorldGen() if ap is None else Acrophobia50mx50mWorldGen(ap)
    await gen.load()
    await gen.run(Acrophobia50mx50mWorldGen.skyscraper_prompt)

async def test_acrophobia_building(ap=None):
    gen = Acrophobia50mx50mWorldGen() if ap is None else Acrophobia50mx50mWorldGen(ap)
    await gen.load()
    await gen.run(Acrophobia50mx50mWorldGen.building_prompt)

async def test_acrophobia_roof(ap=None):
    gen = Acrophobia50mx50mWorldGen() if ap is None else Acrophobia50mx50mWorldGen(ap)
    await gen.load()
    await gen.run(Acrophobia50mx50mWorldGen.roof_prompt)

async def test_acrophobia_platform(ap=None):
    gen = Acrophobia50mx50mWorldGen() if ap is None else Acrophobia50mx50mWorldGen(ap)
    await gen.load()
    await gen.run(Acrophobia50mx50mWorldGen.platform_prompt)

async def test_acrophobia_bridge_regime(ap=None):
    gen = Acrophobia50mx50mWorldGen() if ap is None else Acrophobia50mx50mWorldGen(ap)
    await gen.load()
    await gen.regime(Acrophobia50mx50mWorldGen.bridge_regime_prompt)

async def test_acrophobia_bridge_pro(ap=None):
    gen = AcrophobiaWorldGen() if ap is None else AcrophobiaWorldGen(ap)
    await gen.load()
    await gen.run(AcrophobiaWorldGen.bridge_prompt)

async def test_acrophobia_mountain_pro(ap=None):
    gen = AcrophobiaWorldGen() if ap is None else AcrophobiaWorldGen(ap)
    await gen.load()
    await gen.run(AcrophobiaWorldGen.mountain_prompt)

async def test_acrophobia_skyscraper_pro(ap=None):
    gen = AcrophobiaWorldGen() if ap is None else AcrophobiaWorldGen(ap)
    await gen.load()
    await gen.run(AcrophobiaWorldGen.skyscraper_prompt)

async def test_acrophobia_building_pro(ap=None):
    gen = AcrophobiaWorldGen() if ap is None else AcrophobiaWorldGen(ap)
    await gen.load()
    await gen.run(AcrophobiaWorldGen.building_prompt)

async def test_acrophobia_roof_pro(ap=None):
    gen = AcrophobiaWorldGen() if ap is None else AcrophobiaWorldGen(ap)
    await gen.load()
    await gen.run(AcrophobiaWorldGen.roof_prompt)

async def test_acrophobia_platform_pro(ap=None):
    gen = AcrophobiaWorldGen() if ap is None else AcrophobiaWorldGen(ap)
    await gen.load()
    await gen.run(AcrophobiaWorldGen.platform_prompt)

async def test_acrophobia_bridge_regime_pro(ap=None):
    gen = AcrophobiaWorldGen() if ap is None else AcrophobiaWorldGen(ap)
    await gen.load()
    await gen.regime(AcrophobiaWorldGen.bridge_regime_prompt)

async def test_acrophobia_run(ap=None):
    gen = AcrophobiaWorldGen() if ap is None else AcrophobiaWorldGen(ap)
    await gen.load()
    await gen.run(input("\nPrompt:\n"))

async def test_acrophobia_regime(ap=None):
    gen = AcrophobiaWorldGen() if ap is None else AcrophobiaWorldGen(ap)
    await gen.load()
    await gen.run(input("\nPrompt:\n"))

### General test
async def test_acrophobia_emulate(ap=None):
    gen = AcrophobiaWorldGen() if ap is None else AcrophobiaWorldGen(ap)
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

    "test_acro_bridge_pro": test_acrophobia_bridge_pro,
    "test_acro_mountain_pro": test_acrophobia_mountain_pro,
    "test_acro_skyscraper_pro": test_acrophobia_skyscraper_pro,
    "test_acro_building_pro": test_acrophobia_building_pro,
    "test_acro_roof_pro": test_acrophobia_roof_pro,
    "test_acro_platform_pro": test_acrophobia_platform_pro,
    "test_regime_pro": test_acrophobia_bridge_regime_pro,
    "test_acro_run": test_acrophobia_run,
    "test_acro_regime": test_acrophobia_regime
}

if __name__ == "__main__":
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


















