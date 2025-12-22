
import os
import json
import asyncio
from pathlib import Path
import time
from flask import Flask, request, jsonify
import sys
print(f"{__name__}: {sys.path}")
from generating.worldgen import AcrophobiaWorldGen

import asyncio
import threading

app = Flask(__name__)


async_loop = asyncio.new_event_loop()

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
    scene_name = request.args["scene_name"]
    prompt = request.args["prompt"]
    assets_folder = Path(request.args["assets"])

    future = asyncio.run_coroutine_threadsafe(
        AcrophobiaWorldGen.generate(scene_name, assets_folder, prompt),
        async_loop
    )

    # OPTIONAL: attach callbacks / logging
    future.add_done_callback(
        lambda f: print("Worldgen:", f.result())
    )

    return jsonify({"started": True})



if __name__ == "__main__": 
   

    app.run(debug=True) # 