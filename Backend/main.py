#
#       This main.py is reserved for the optimal use-case, a ChatGPT-integrated VR-Exposure-Therapy chatbot.
#
#       Would be developed from here and mcp_server.py, targetting the resources in ChatGPT and the data from there
#
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

    #                           #
    # have embedded-HTML resource runtime
    #

    #                           #

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
        # ??

    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if process:
            print("Stopping server...")
            process.terminate()