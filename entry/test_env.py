import sys
import os
import time
from threading import Thread
from pathlib import Path
import asyncio
import json
import random

import asyncio

from tools import tools as instruments

from generating.worldgen import AcrophobiaWorldGen
from pprint import pprint
async_loop = None

class Test:
    def __init__(self, assets: str):
        assets_folder = Path(assets)

        if async_loop is None:
            raise Exception(f"No async loop started...")
        future = asyncio.run_coroutine_threadsafe(
            self.run(assets_folder),
            async_loop
        )
        future.add_done_callback(
            lambda f: print("Worldgen:", f.result())
        )

    def __repr__(self):
        return json.dumps(self.conductor_tools, indent=4, sort_keys=False)

    async def run(self, assets_folder: Path):
        wg = AcrophobiaWorldGen("test", "test_scene", assets_folder)
        await wg.load()
        self.conductor_tools = wg.conductor.tools
        self._funcs = {tool.name: tool for tool in wg.conductor.tools}
        print(self)

    def __getattr__(self, name):
        if name in self._funcs:
            func = self._funcs[name]

            def _call_tool(*args, **kwargs):
                
                try:
                    return func(*args, **kwargs)  # or tool.invoke(...)
                except Exception:
                    json_payload = json.dumps(kwargs)
                    asyncio.run_coroutine_threadsafe(
                        func.on_invoke_tool(None, json_payload),
                        async_loop
                    )
            return _call_tool

        raise AttributeError(f"{type(self).__name__} has no attribute {name}")
    
    @property
    def result(self):
        return instruments.core.world