from urllib.parse import urlparse

from . import mcp
from fastmcp import Context
from mcp.types import ToolAnnotations

from utils.common import format_timestamp
from utils.databus_client import get_client
from datetime import datetime


@mcp.tool(
    name="vehicle_current_info",
    description="Get comprehensive current information about a specific vehicle by its license plate, including static details and realtime status.",
    tags={"fleet", "vehicles", "comprehensive"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_vehicle_current_info(
    vehicle_input: str, ctx: Context | None = None
) -> dict:
    """Fetch comprehensive current information about a specific vehicle by its license plate, including static details and realtime status.

    arguments:
        - vehicle_input: The license plate of the vehicle to fetch information for.
        - ctx: Optional context for logging and additional information during execution.

    returns:
        - A dictionary containing comprehensive information about the vehicle, including static details, realtime status, and run information.
        - If the vehicle is not found or an error occurs, an error message is included in the response.
    """
    try:
        client = get_client()
        vehicle_id = vehicle_input.strip()
        if ctx:
            await ctx.info(f"Fetching full info for vehicle ID: {vehicle_id}")

        # Static Info
        try:
            vehicle_static = await client.get_api(f"vehicle/{vehicle_id}")
            static_found = bool(vehicle_static)
        except Exception as e:
            vehicle_static = {}
            static_found = False

        # Realtime info
        feed = await client.get_feed("vehicle_positions")
        realtime_found = False
        vehicle_realtime = {}
        if feed and "entity" in feed:
            for entity in feed["entity"]:
                vehicle_data = entity.get("vehicle", {})
                vehicle_info = vehicle_data.get("vehicle", {})
                if vehicle_info.get("license_plate") == vehicle_id:
                    realtime_found = True
                    position = vehicle_data.get("position", {})
                    vehicle_realtime = {
                        "latitude": position.get("latitude") or "unknown",
                        "longitude": position.get("longitude") or "unknown",
                        "speed": position.get("speed") or "unknown",
                        "occupancy_status": vehicle_data.get("occupancy_status")
                        or "unknown",
                        "occupancy_percentage": vehicle_data.get("occupancy_percentage")
                        or "unknown",
                        "timestamp": (
                            format_timestamp(vehicle_data.get("timestamp"))
                            if vehicle_data.get("timestamp")
                            else "unknown"
                        ),
                        "current_status": vehicle_data.get("current_status")
                        or "unknown",
                        "congestion_level": vehicle_data.get("congestion_level")
                        or "unknown",
                    }
                    break
        # run info
        run_info = await client.get_api("run")
        run_status = "unassigned"
        assignment = None
        if run_info:
            for run in run_info:
                if (
                    run.get("vehicle") == vehicle_id
                    and run.get("run_status") == "IN_PROGRESS"
                ):
                    run_status = run.get("run_status", "unknown")
                    url = run.get("url", "unknown")
                    parsed = urlparse(url)
                    path_parts = parsed.path.rstrip("/").split("/")
                    run_id = path_parts[-1]
                    assignment = {
                        "run_id": run_id,
                        "route_id": run.get("route_id", "unknown"),
                        "operator": run.get("operator", "unknown"),
                        "trip_id": run.get("trip_id", "unknown"),
                        "start_time": run.get("start_time", "unknown"),
                        "start_date": run.get("start_date", "unknown"),
                        "run_status": run.get("run_status", "unknown"),
                    }

        # Merge static and realtime info
        result = {
            "vehicle_id": vehicle_id,
            "label": vehicle_static.get("label")
            or vehicle_realtime.get("label", "unknown"),
            "license_plate": vehicle_static.get("license_plate") or vehicle_id,
            "status": vehicle_static.get("status", "unknown"),
            "company": vehicle_static.get("company", "unknown"),
            "route_id": vehicle_static.get("route_id")
            or vehicle_realtime.get("route_id", "unknown"),
            "latitude": vehicle_realtime.get("latitude", "unknown"),
            "longitude": vehicle_realtime.get("longitude", "unknown"),
            "speed": vehicle_realtime.get("speed", "unknown"),
            "occupancy_status": vehicle_realtime.get("occupancy_status", "unknown"),
            "occupancy_percentage": vehicle_realtime.get(
                "occupancy_percentage", "unknown"
            ),
            "timestamp": vehicle_realtime.get("timestamp", "unknown"),
            "current_status": vehicle_realtime.get("current_status", "unknown"),
            "congestion_level": vehicle_realtime.get("congestion_level", "unknown"),
            "run_status": run_status,
            "assignment": assignment,
        }

        if not static_found and not realtime_found:
            return {
                "error": "Vehicle not found in both static and realtime data",
                "vehicle_id": vehicle_id,
            }
        elif not static_found:
            result["warning"] = (
                "Vehicle not found in static data, only realtime info available"
            )
        elif not realtime_found:
            result["warning"] = (
                "Vehicle not found in realtime feed, only static info available"
            )

        return {"vehicle_id": vehicle_id, "full_info": result}

    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching vehicle full info: {str(e)}")
        return {"error": str(e), "vehicle_input": vehicle_input}


@mcp.tool(
    name="vehicle_full_info",
    description="Get full current information about a specific vehicle, including static details, realtime status, and assignment/run info.",
    tags={"fleet", "vehicles", "comprehensive"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_vehicle_full_info(vehicle_input: str, ctx: Context | None = None) -> dict:
    """Fetch full current information about a specific vehicle, including static details, realtime status, and assignment/run info.

    arguments:
        - vehicle_input: The license plate of the vehicle to fetch information for.
        - ctx: Optional context for logging and additional information during execution.

    returns:
        - A dictionary containing comprehensive information about the vehicle, including static details, realtime status, and assignment/run info.
        - If the vehicle is not found or an error occurs, an error message is included in the response.
    """
    try:
        client = get_client()
        vehicle_id = vehicle_input.strip()
        if ctx:
            await ctx.info(f"Fetching full info for vehicle ID: {vehicle_id}")

        # Static info
        try:
            vehicle_static = await client.get_api(f"vehicle/{vehicle_id}")
            static_found = bool(vehicle_static)
        except Exception:
            vehicle_static = {}
            static_found = False

        vehicles_list = await client.get_api("vehicle")
        vehicle_extra = next(
            (v for v in vehicles_list if v.get("license_plate") == vehicle_id), {}
        )

        # Realtime info
        realtime_found = False
        feed = await client.get_feed("vehicle_positions")
        vehicle_realtime = {}
        if feed and "entity" in feed:
            for entity in feed["entity"]:
                vehicle_data = entity.get("vehicle", {})
                vehicle_info = vehicle_data.get("vehicle", {})
                if vehicle_info.get("license_plate") == vehicle_id:
                    position = vehicle_data.get("position", {})
                    vehicle_realtime = {
                        "latitude": position.get("latitude", "unknown"),
                        "longitude": position.get("longitude", "unknown"),
                        "speed": position.get("speed", "unknown"),
                        "occupancy_status": vehicle_data.get(
                            "occupancy_status", "unknown"
                        ),
                        "occupancy_percentage": vehicle_data.get(
                            "occupancy_percentage", "unknown"
                        ),
                        "timestamp": (
                            format_timestamp(vehicle_data.get("timestamp"))
                            if vehicle_data.get("timestamp")
                            else "unknown"
                        ),
                        "current_status": vehicle_data.get("current_status", "unknown"),
                        "congestion_level": vehicle_data.get(
                            "congestion_level", "unknown"
                        ),
                    }
                    realtime_found = True
                    break

        # Assignment/run info
        run_info = await client.get_api("run")
        assignment = None
        if run_info:
            for run in run_info:
                if (
                    run.get("vehicle") == vehicle_id
                    and run.get("run_status") == "IN_PROGRESS"
                ):
                    url = run.get("url", "unknown")
                    parsed = urlparse(url)
                    path_parts = parsed.path.rstrip("/").split("/")
                    run_id = path_parts[-1]
                    assignment = {
                        "run_id": run_id,
                        "route_id": run.get("route_id", "unknown"),
                        "operator": run.get("operator", "unknown"),
                        "trip_id": run.get("trip_id", "unknown"),
                        "start_time": run.get("start_time", "unknown"),
                        "start_date": run.get("start_date", "unknown"),
                        "run_status": run.get("run_status", "unknown"),
                    }
                    break

        # Merge all info
        result = {
            "vehicle_id": vehicle_id,
            "label": vehicle_static.get("label")
            or vehicle_extra.get("label", "unknown"),
            "license_plate": vehicle_static.get("license_plate") or vehicle_id,
            "company": vehicle_static.get("company", "unknown"),
            "status": vehicle_static.get(
                "status", vehicle_extra.get("status", "unknown")
            ),
            "wheelchair_accessible": vehicle_extra.get(
                "wheelchair_accessible", "unknown"
            ),
            "wifi": vehicle_extra.get("wifi", "unknown"),
            "air_conditioning": vehicle_extra.get("air_conditioning", "unknown"),
            "mobile_charging": vehicle_extra.get("mobile_charging", "unknown"),
            "bike_rack": vehicle_extra.get("bike_rack", "unknown"),
            "has_screen": vehicle_extra.get("has_screen", False),
            "has_headsign_screen": vehicle_extra.get("has_headsign_screen", False),
            "has_audio": vehicle_extra.get("has_audio", False),
            "latitude": vehicle_realtime.get("latitude", "unknown"),
            "longitude": vehicle_realtime.get("longitude", "unknown"),
            "speed": vehicle_realtime.get("speed", "unknown"),
            "occupancy_status": vehicle_realtime.get("occupancy_status", "unknown"),
            "occupancy_percentage": vehicle_realtime.get(
                "occupancy_percentage", "unknown"
            ),
            "timestamp": vehicle_realtime.get("timestamp", "unknown"),
            "current_status": vehicle_realtime.get("current_status", "unknown"),
            "congestion_level": vehicle_realtime.get("congestion_level", "unknown"),
            "assignment": assignment,
        }

        if not static_found and not realtime_found:
            return {
                "error": "Vehicle not found in both static and realtime data",
                "vehicle_id": vehicle_id,
            }
        elif not static_found:
            result["warning"] = (
                "Vehicle not found in static data, only realtime info available"
            )
        elif not realtime_found:
            result["warning"] = (
                "Vehicle not found in realtime feed, only static info available"
            )

        return {"vehicle_id": vehicle_id, "full_info": result}
    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching vehicle full info: {str(e)}")
        return {"error": str(e), "vehicle_input": vehicle_input}


@mcp.tool(
    name="vehicle_current_assignment",
    description="Get the current assignment (route, operator, etc.) for a specific vehicle by its ID.",
    tags={"fleet", "vehicles", "assignment"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_vehicle_current_assignment(
    vehicle_input: str, ctx: Context | None = None
) -> dict:
    """Fetch the current assignment (route, operator, etc.) for a specific vehicle by its ID.

    arguments:
        - vehicle_input: The license plate of the vehicle to fetch assignment information for.
        - ctx: Optional context for logging and additional information during execution.

    returns:
        - A dictionary containing the vehicle ID and its current assignment details, including route ID, operator, trip ID, start time, and start date.
        - If no active assignment is found or an error occurs, an appropriate message is included in the response.
    """
    try:
        client = get_client()
        if ctx:
            await ctx.info(
                f"Fetching current assignment for vehicle ID: {vehicle_input}"
            )

        vehicle_input = vehicle_input.strip()
        run_info = await client.get_api("run")

        if run_info and not "error" in run_info:
            for run in run_info:
                if (
                    run.get("vehicle") == vehicle_input
                    and run.get("run_status") == "IN_PROGRESS"
                ):
                    url = run.get("url", "unknown")
                    parsed = urlparse(url)
                    path_parts = parsed.path.rstrip("/").split("/")
                    run_id = path_parts[-1]
                    assigment = {
                        "run_id": run_id,
                        "route_id": run.get("route_id", "unknown"),
                        "start_time": run.get("start_time", "unknown"),
                        "start_date": run.get("start_date", "unknown"),
                        "operator_id": run.get("operator", "unknown"),
                        "vehicle_id": run.get("vehicle", "unknown"),
                        "trip_id": run.get("trip_id", "unknown"),
                    }
                    return {
                        "vehicle_id": vehicle_input,
                        "current_assignment": assigment,
                    }
            return {
                "message": "No active assignment found for vehicle",
                "vehicle_id": vehicle_input,
            }
        return {"error": "Run information not available", "vehicle_id": vehicle_input}
    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching vehicle assignment: {str(e)}")
        return {"error": str(e), "vehicle_input": vehicle_input}
