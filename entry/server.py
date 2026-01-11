import os
import asyncio
from pathlib import Path
from flask import Flask, request, jsonify
import sys
from typing import Optional
print(f"sys.path for {__name__}:\n{sys.path}")

# common
os.environ["MODEL"] = "o4-mini"

# class type
os.environ["WORLD_CLASS"] = "UNITY"
os.environ["LOG"] = "tbd"

# Unity configs
os.environ["UNITY_WORLD_TYPE"] = "UNITY_TWO_STEP"
os.environ["UNITY_VERSION"] = "6"
os.environ["SKYBOX_MATERIALS"] = "Skybox Materials"
os.environ["GROUND_MATERIALS"] = "Ground Materials"
os.environ["SOUNDS"] = "Sounds"

# Unity subclass configs
os.environ["VR_HEADSET_TYPE"] = "Vive Focus 3"

from generating.worldgen import AcrophobiaWorldGen

# For testing
from entry import test_env


from entry.test_env import Test


import asyncio
import threading

app = Flask(__name__)


async_loop = asyncio.new_event_loop()
test_env.async_loop = async_loop

def start_event_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

threading.Thread(
    target=start_event_loop,
    args=(async_loop,),
    daemon=True
).start()

@app.route('/generate')
def generate():
    world_name = request.args["world_name"]
    prompt = request.args["prompt"]
    assets_folder = Path(request.args["assets"])

    os.environ["LOG"] = f"{world_name}"

    future = asyncio.run_coroutine_threadsafe(
        AcrophobiaWorldGen.generate(world_name, assets_folder, prompt),
        async_loop
    )

    future.add_done_callback(
        lambda f: print("Worldgen:", f.result())
    )

    return jsonify({"started": True})

def dummy(world_name: str, prompt: str, assets: Optional[str] = None):
    if assets:
        assets_folder = Path(assets)
    else:
        str_path = os.environ.get("ASSETS", None)
        assets_folder = Path(str_path) if str_path else None
    future = asyncio.run_coroutine_threadsafe(
        AcrophobiaWorldGen.generate(world_name, assets_folder, prompt),
        async_loop
    )

    future.add_done_callback(
        lambda f: print("Worldgen:", f.result())
    )

    return jsonify({"started": True})

if __name__ == "__main__": 
   

    app.run(debug=True) # 