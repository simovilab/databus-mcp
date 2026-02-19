from fastmcp import FastMCP, Context
from mcp.types import ToolAnnotations
from utils.common import  filter_by_field, normalize_text
from utils.databus_client import get_client
from urllib.parse import urlparse

mcp = FastMCP("network")

async def get_routes_list(ctx: Context | None = None) -> dict:
    client = get_client()

    if ctx:
        await ctx.info("Fetching list of routes from API")
    
    routes = await client.get_api("route")

    if ctx:
        await ctx.info(f"Found {len(routes)} routes")

    return {
        "total_routes": len(routes),
        "routes": routes
    }

if __name__ == "__main__":
    mcp.run()
    
