import asyncio
import os
import sys
import subprocess
import time
from typing import Any

from agents import Agent, Runner, gen_trace_id, trace, ItemHelpers
from agents.mcp import MCPServer, MCPServerStreamableHttp
from agents.model_settings import ModelSettings


async def run(mcp_server: MCPServer):
    # Generic agent in runtime  #

    agent = Agent(
        name="Assistant",
        instructions="Use the tools assist the user.",
        mcp_servers=[mcp_server],
        model_settings=ModelSettings(tool_choice="required"),
    )

    #                           #

    #
    # have embedded-HTML resource runtime
    #



<<<<<<< Updated upstream
    result = Runner.run_streamed(starting_agent=agent, input="Run endpoint1. If it fails, give me the error.")
    async for event in result.stream_events():
        # Each 'event' corresponds to one 'yield' from the server
        if event.type == 'run_item_stream_event':
                # Streaming yet to be provided. Check Apps SDK and MCP
                pass        
=======
from worldgen import AcrophobiaWorldGen, VRWorldGen, WorldGen

MODEL = (os.getenv("MODEL") or "o3-mini").strip() or "o3-mini"  
>>>>>>> Stashed changes



<<<<<<< Updated upstream
async def main():
    async with MCPServerStreamableHttp(
        name="Streamable Python Server",
        params={
            "url": "http://localhost:8000/mcp",
        },
    ) as server:
        trace_id = gen_trace_id()
        with trace(workflow_name="SSE Example", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}\n")
            await run(server)
=======
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

async def test_acrophobia_bridge_regime():
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
    gen = WorldGen(asset_project_path=Path("../Resources/Asset Projects/Shap-E"), scene_name=f"acro_{MODEL}_{random.randint(100, 999)}", )
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
>>>>>>> Stashed changes

if __name__ == "__main__":
    process = None
    try:
        this_dir = os.path.dirname(os.path.abspath(__file__))
        server_file = os.path.join(this_dir, "mcp_server.py")

        print("Starting Streamable HTTP server at http://localhost:8000/mcp ...")


        process = subprocess.Popen([sys.executable, server_file])

        time.sleep(3)

        print("MCPServerStreamableHttp server started. Running example...\n\n")

        # Now run generic agent runtime.
        asyncio.run(main())

    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if process:
            print("Stopping server...")
            process.terminate()