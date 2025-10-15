import random
import asyncio
import requests

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession

mcp = FastMCP(name="Example")


# Register tools with @mcp.tool