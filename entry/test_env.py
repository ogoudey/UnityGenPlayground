import sys
import os
import time
from threading import Thread
from pathlib import Path
import asyncio
import json
import random
from agents import Runner
import asyncio

from tools import tools as instruments

from generating.worldgen import AcrophobiaWorldGen
from pprint import pformat

async_loop = None

class Test:
    def __init__(self, assets: str):
        assets_folder = Path(assets)

        if async_loop is None:
            raise Exception(f"No async loop started...")
        future = asyncio.run_coroutine_threadsafe(
            self.spin(assets_folder),
            async_loop
        )
        future.add_done_callback(
            lambda f: print("Worldgen:", f.result())
        )

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return pformat(self._conductor_tools, width=120, sort_dicts=False)
    
    async def spin(self, assets_folder: Path):
        wg = AcrophobiaWorldGen("test", "test_scene", assets_folder)
        await wg.load()
        self._conductor = wg.conductor
        self._conductor_tools = wg.conductor.tools
        self._funcs = {tool.name: tool for tool in wg.conductor.tools}
        print(self)

    def __getattr__(self, name):
        if name in self._funcs:
            func = self._funcs[name]

            def _call_tool(*args, **kwargs):
                
                try:
                    return func(*args, **kwargs)
                except Exception:
                    json_payload = json.dumps(kwargs)
                    asyncio.run_coroutine_threadsafe(
                        func.on_invoke_tool(None, json_payload),
                        async_loop
                    )
            return _call_tool

        raise AttributeError(f"{type(self).__name__} has no attribute {name}")
    
    def conductor(self, prompt: str):
        async def run_conductor(_prompt: str):
            await Runner.run(self._conductor, json.dumps(_prompt))

        payload = inject_world_model(prompt, instruments.core.world.model)
        asyncio.run_coroutine_threadsafe(
            run_conductor(payload),
            async_loop
        )

    def write(self):
        self.result.done_and_write(instruments.core.assets / "Generations" / instruments.core.world.scene.name)

    @property
    def result(self):
        return instruments.core.world
    

    ### TEST - should be elsewhere
def inject_world_model(prompt, world_model):
    return\
f"""
==== World Model ====
{world_model}

          .
==== User prompt ====
{prompt}
"""
