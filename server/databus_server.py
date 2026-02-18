from fastmcp import FastMCP

from topics import vehicles, operations

mcp = FastMCP("DatabusMCPServer")
mcp.mount(vehicles.mcp, namespace="vehiclesMCPProvider")
mcp.mount(operations.mcp, namespace="operationsMCPProvider")

if __name__ == "__main__":
    mcp.run()

