from urllib.parse import urlparse

from . import mcp
from fastmcp import Context
from mcp.types import ToolAnnotations

from utils.common import format_timestamp
from utils.databus_client import get_client
from datetime import datetime


@mcp.tool(
    name="vehicle_occupancy",
    description="Get current occupancy information for a specific vehicle by its license plate.",
    tags={"fleet", "vehicles", "read-only"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_vehicle_occupancy(vehicle_input: str, ctx: Context | None = None) -> dict:
    """Fetch the current occupancy information for a specific vehicle by its license plate.

    arguments:
        - vehicle_input: The license plate of the vehicle to fetch occupancy information for.
        - ctx: Optional context for logging and additional information during execution.

    returns:
        - A dictionary containing the vehicle ID, occupancy status, occupancy percentage, and the timestamp of the last update.
        - If the vehicle is not found or an error occurs, an error message is included in the response.
    """
    try:
        client = get_client()

        vehicle_id = vehicle_input.strip()
        if ctx:
            await ctx.info(f"Fetching occupancy for vehicle ID: {vehicle_id}")

        feed = await client.get_feed("vehicle_positions")

        if not feed or "entity" not in feed:
            return {"error": "Vehicle positions feed not available"}

        for entity in feed["entity"]:
            vehicle_data = entity.get("vehicle", {})
            vehicle_info = vehicle_data.get("vehicle", {})

            if (
                vehicle_info.get("license_plate") == vehicle_id
                or vehicle_info.get("id") == vehicle_id
            ):
                return {
                    "vehicle_id": vehicle_data.get("vehicle", {}).get("id", "unknown"),
                    "vehicle_license_plate": vehicle_data.get("vehicle", {}).get(
                        "license_plate", "unknown"
                    ),
                    "occupancy_status": vehicle_data.get("occupancy_status", "unknown"),
                    "occupancy_percentage": vehicle_data.get(
                        "occupancy_percentage", "unknown"
                    ),
                    "timestamp": format_timestamp(
                        vehicle_data.get("timestamp", "unknown")
                    ),
                }
        return {
            "error": "Vehicle not found in positions feed",
            "vehicle_id": vehicle_id,
        }
    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching vehicle occupancy: {str(e)}")
        return {"error": str(e), "vehicle_id": vehicle_id}


@mcp.tool(
    name="vehicle_position",
    description="Get the current position of a specific vehicle by its license plate.",
    tags={"fleet", "vehicles", "realtime"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_vehicle_position(vehicle_input: str, ctx: Context | None = None) -> dict:
    """Fetch the current position of a specific vehicle by its license plate.

    arguments:
        - vehicle_input: The license plate of the vehicle to fetch position information for.
        - ctx: Optional context for logging and additional information during execution.

    returns:
        - A dictionary containing the vehicle ID, latitude, longitude, speed, and the timestamp of the last update.
        - If the vehicle is not found or an error occurs, an error message is included in the response.
    """
    try:
        client = get_client()
        vehicle_id = vehicle_input.strip()
        if ctx:
            await ctx.info(f"Fetching position for vehicle ID: {vehicle_id}")

        feed = await client.get_feed("vehicle_positions")

        if not feed or "entity" not in feed:
            return {"error": "Vehicle positions feed not available"}

        for entity in feed["entity"]:
            vehicle_data = entity.get("vehicle", {})
            vehicle_info = vehicle_data.get("vehicle", {})
            position = vehicle_data.get("position", {})
            if (
                vehicle_info.get("license_plate") == vehicle_id
                or vehicle_info.get("id") == vehicle_id
            ):

                return {
                    "vehicle_id": vehicle_data.get("vehicle", {}).get("id", "unknown"),
                    "vehicle_license_plate": vehicle_data.get("vehicle", {}).get(
                        "license_plate", "unknown"
                    ),
                    "latitude": position.get("latitude", "unknown"),
                    "longitude": position.get("longitude", "unknown"),
                    "speed_km": position.get("speed", "unknown"),
                    "timestamp": format_timestamp(vehicle_data.get("timestamp")),
                }
        return {
            "error": "Vehicle not found in positions feed",
            "vehicle_id": vehicle_id,
        }
    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching vehicle position: {str(e)}")
        return {"error": str(e), "vehicle_input": vehicle_input}


@mcp.tool(
    name="high_occupancy_vehicles",
    description="Get a list of vehicles that currently have high occupancy (e.g., over 80%).",
    tags={"fleet", "vehicles", "realtime"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_high_occupancy_vehicles(ctx: Context | None = None) -> dict:
    """Fetch a list of vehicles that currently have high occupancy (e.g., over 80%).

    arguments:
        - ctx: Optional context for logging and additional information during execution.

    returns:
        - A dictionary containing the total number of high occupancy vehicles and a list of vehicles with their ID, license plate, occupancy percentage, and timestamp.
        - If an error occurs or no high occupancy vehicles are found, an error message is included in the response.
    """
    try:
        client = get_client()

        if ctx:
            await ctx.info("Fetching vehicles with high occupancy")

        feed = await client.get_feed("vehicle_positions")

        if not feed or "entity" not in feed:
            return {"error": "Vehicle positions feed not available"}

        high_occupancy_vehicles = []
        for entity in feed["entity"]:
            vehicle_data = entity.get("vehicle", {})
            occupancy_percentage = vehicle_data.get("occupancy_percentage")
            try:
                occ_percent = float(occupancy_percentage)
            except (TypeError, ValueError):
                occ_percent = 0

            if occ_percent > 50:
                high_occupancy_vehicles.append(
                    {
                        "vehicle_id": vehicle_data.get("vehicle", {}).get(
                            "id", "unknown"
                        ),
                        "vehicle_license_plate": vehicle_data.get("vehicle", {}).get(
                            "license_plate", "unknown"
                        ),
                        "occupancy_percentage": occ_percent,
                        "timestamp": vehicle_data.get("timestamp", "unknown"),
                    }
                )

        return {
            "total_high_occupancy_vehicles": len(high_occupancy_vehicles),
            "high_occupancy_vehicles": high_occupancy_vehicles,
        }
    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching high occupancy vehicles: {str(e)}")
        return {"error": str(e)}


@mcp.tool(
    name="is_vehicle_moving",
    description="Check if a specific vehicle is currently active (i.e., has a recent position update).",
    tags={"fleet", "vehicles", "status"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def is_vehicle_moving(vehicle_input: str, ctx: Context | None = None) -> dict:
    """Check if a specific vehicle is currently active (i.e., has a recent position update).

    arguments:
        - vehicle_input: The license plate of the vehicle to check.
        - ctx: Optional context for logging and additional information during execution.

    returns:
        - A dictionary containing the vehicle ID and its active status, including trip ID, current status, position, and last position timestamp.
        - If the vehicle is not found or an error occurs, an appropriate message is included in the response.
    """
    try:
        client = get_client()
        vehicle_id = vehicle_input.strip()

        if ctx:
            await ctx.info(f"Checking if vehicle ID: {vehicle_input} is active")

        feed = await client.get_feed("vehicle_positions")

        if not feed or "entity" not in feed:
            return {"error": "Vehicle positions feed not available"}

        for entity in feed["entity"]:
            vehicle_data = entity.get("vehicle", {})
            vehicle_info = vehicle_data.get("vehicle", {})

            if (
                vehicle_info.get("id") == vehicle_id
                or vehicle_info.get("license_plate") == vehicle_id
            ):
                return {
                    "vehicle_id": vehicle_id,
                    "vehicle_license_plate": vehicle_info.get(
                        "license_plate", "unknown"
                    ),
                    "trip_id": vehicle_data.get("trip", {}).get("trip_id", "unknown"),
                    "current_status": vehicle_data.get("current_status", "unknown"),
                    "position": {
                        "latitude": vehicle_data.get("position", {}).get(
                            "latitude", "unknown"
                        ),
                        "longitude": vehicle_data.get("position", {}).get(
                            "longitude", "unknown"
                        ),
                    },
                    "last_position_timestamp": format_timestamp(
                        vehicle_data.get("timestamp")
                    ),
                }

        return {
            "vehicle_id": vehicle_id,
            "is_active": False,
            "message": "Vehicle not found in positions feed, assuming inactive",
        }

    except Exception as e:
        if ctx:
            await ctx.error(f"Error checking vehicle active status: {str(e)}")
        return {"error": str(e), "vehicle_input": vehicle_input}
