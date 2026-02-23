from fastmcp import FastMCP

from topics import vehicles, operations, network

mcp = FastMCP("DatabusMCPServer")
#mcp.mount(vehicles.mcp, namespace="vehicles")
#mcp.mount(operations.mcp, namespace="operations")
mcp.mount(network.mcp, namespace="network")


if __name__ == "__main__":
    mcp.run()

