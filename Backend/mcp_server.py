import random
import asyncio
import requests
from mcp.server.fastmcp import FastMCP

# Create server
mcp = FastMCP("AcroGen Server")


from tests import test_acrophobia_bridge

@mcp.tool()
async def endpoint1():
    await test_acrophobia_bridge()
    return "Done"


if __name__ == "__main__":
    mcp.run(transport="streamable-http")