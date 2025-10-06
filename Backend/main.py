import sys
import os
import time
from threading import Thread

#from flask import Flask, send_from_directory, jsonify, request
#from flask_cors import CORS

import json
import random

import asyncio

import coordinator as agents
from enrichment import Therapist, Transducer, ClientFulfillment


from worldgen import AcrophobiaWorldGen

MODEL = (os.getenv("MODEL") or "o3-mini").strip() or "o3-mini"  


async def test_acrophobia_ideal():
    gen = AcrophobiaWorldGen()
    await gen.load()
    await gen.run(AcrophobiaWorldGen.ideal_prompt)
  
async def test_acrophobia_emulate():
    gen = AcrophobiaWorldGen()
    gen.load()
    prompt = gen.get_prompt()
    print("Prompt:", prompt)
    await gen.run(prompt)


test_dispatcher = {
    # = deprecated test
    "test_acro_id": test_acrophobia_ideal,
    "test_acro_em": test_acrophobia_emulate,
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


















