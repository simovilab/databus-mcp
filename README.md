# Databus MCP

**Databus MCP** is a Model Context Protocol (MCP) server that enables AI assistants and chatbots to access public transportation operational data through standardized interfaces.

It provides structured tools for:

- Public transport operational status  
- Fleet and route information  
- Service monitoring  
- Statistical indicators  
- Real-time and near real-time transit data  

The goal of Databus MCP is to expose transit data in a modular, AI-friendly format for operators, regulators, and intelligent systems.

---
## Repository Structure

This is a monorepo with two main components:
- **`client/`**: Client implementation (Not implemented yet)
- **`server/`**: Python-based MCP server implementation using FastMCP (primary focus)

All Python code and dependencies are in the `server/` directory.

### Server Directory Structure

```
server/
├── databus_server.py       # Main entry point - imports and composes subservers
└── topics/                 # Domain-specific subservers (modular architecture)
    ├── agencies.py         # Agency listing tools
    ├── routes.py           # Route information tools
    ├── stops.py            # Stop info and next trips (fully implemented)
    ├── trips.py            # Trip planning (planned)
    ├── alerts.py           # Service alerts (planned)
    └── Occupation.py       # (ADD)
```

---

## Development Environment

### Prerequisites

- Python 3.14 (specified in `server/.python-version`)
- `uv` package manager for Python dependency management

### Initial Setup

```bash
cd server
uv venv
source .venv/bin/activate  # On macOS/Linux
uv sync  # Install dependencies from uv.lock
```


### Running the MCP Server

The server runs using stdio transport for MCP communication:

```bash
# From project root
uv --directory server run databus_server.py

# Or from server directory
cd server
python databus_server.py
```
---

## Architecture

### FastMCP Modular Architecture

The project uses the **FastMCP** framework with a **modular subserver architecture**.


**Architecture Overview:**
- `server/databus_server.py`: Main server entry point that imports and composes domain-specific subservers
- `server/topics/`: Directory containing modular subservers, each focused on a specific domain 
- Each topic module defines an independent FastMCP server instance
- Subservers are imported into the main server using `mcp.import_server()`
- Each subserver is namespaced automatically


This allows tools to be grouped logically, for example: `agencies_info`, `routes_info`, `stops_next_trips`.

---

## Configuration

Configuration is handled via `python-decouple` which reads from environment variables or `.env` files:

- **`DATABUS_API_BASE`**: Base URL for Databus API (default: `http://localhost:8000/api`)
  - Each topic module that needs API access should define this constant
  - Production value will be defined in future deployments.

---

## Additional information
Additional implementation details and extended Databus MCP server documentation can be found in: 
[Server Documentation](server/README.md)

---