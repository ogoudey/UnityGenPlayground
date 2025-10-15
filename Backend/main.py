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

    result = Runner.run_streamed(starting_agent=agent, input="Run endpoint1. If it fails, give me the error.")
    async for event in result.stream_events():
        # Each 'event' corresponds to one 'yield' from the server
        if event.type == 'run_item_stream_event':
                # Streaming yet to be provided. Check Apps SDK and MCP
                pass        



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