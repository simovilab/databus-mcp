from fastmcp import FastMCP

from topics import vehicles, operations

mcp = FastMCP("DatabusMCPServer")
mcp.mount(vehicles.mcp, namespace="vehicles")
mcp.mount(operations.mcp, namespace="operations")


if __name__ == "__main__":
    mcp.run()

