from . import mcp
from fastmcp import Context
from mcp.types import ToolAnnotations
from utils.databus_client import get_client
from utils.common import format_timestamp


@mcp.tool(
    name="realtime_runs_by_route",
    description="Get a list of active runs for a specific route, including vehicle IDs, current locations, and occupancy status.",
    tags={"network", "active runs", "read-only"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_realtime_runs_by_route(
    route_input: str, ctx: Context | None = None
) -> dict:
    """Get a list of active runs for a specific route, including vehicle IDs, current locations, and occupancy status.

    arguments:
        - route_input: The route ID or name to get active runs for.
        - ctx: Optional context for logging and additional information during execution.

    returns:
        - A dictionary containing a list of active runs with vehicle IDs, current locations, and occupancy status.
        - If an error occurs or no active runs are found, an error message is included in the response.
    """
    try:
        client = get_client()
        if ctx:
            await ctx.info(f"Resolving route input: {route_input}")

        route = route_input.strip()
        feed_trip = await client.get_feed("trip_updates")
        feed_positions = await client.get_feed("vehicle_positions")
        if not feed_trip or "entity" not in feed_trip:
            return {"error": "No feed data available"}
        if not feed_positions or "entity" not in feed_positions:
            return {"error": "No feed data available"}

        vehicle_positions = {}

        for entity in feed_positions["entity"]:
            vehicle_data = entity.get("vehicle", {})
            vehicle_id = vehicle_data.get("license_plate", "unknown")
            position = vehicle_data.get("position", {})
            vehicle_positions[vehicle_id] = position

        active_runs = []
        for entity in feed_trip["entity"]:
            trip_update = entity.get("trip_update", {})
            trip = trip_update.get("trip", {})
            vehicle = trip_update.get("vehicle", {})
            license_plate = vehicle.get("license_plate", "unknown")
            route_id = trip.get("route_id", "unknown")
            timestamp = trip_update.get("timestamp", None)

            if route_id != route_input:
                continue

            vehicle_position = None
            for pos_entity in feed_positions["entity"]:
                pos_vehicle = pos_entity.get("vehicle", {})
                pos_license_plate = pos_vehicle.get("vehicle", {}).get(
                    "license_plate", "unknown"
                )
                if pos_license_plate == license_plate:
                    vehicle_position = pos_vehicle
                    break

            position = vehicle_position.get("position", {}) if vehicle_position else {}
            current_status = (
                vehicle_position.get("current_status", "unknown")
                if vehicle_position
                else "unknown"
            )
            current_stop_id = (
                vehicle_position.get("stop_id", "unknown")
                if vehicle_position
                else "unknown"
            )
            congestion_level = (
                vehicle_position.get("congestion_level", "unknown")
                if vehicle_position
                else "unknown"
            )
            occupancy_status = (
                vehicle_position.get("occupancy_status", "unknown")
                if vehicle_position
                else "unknown"
            )
            occupancy_percentage = (
                vehicle_position.get("occupancy_percentage", "unknown")
                if vehicle_position
                else "unknown"
            )
            speed = position.get("speed", "unknown")
            latitude = position.get("latitude", "unknown")
            longitude = position.get("longitude", "unknown")

            active_runs.append(
                {
                    "route_id": route_id,
                    "vehicle_id": vehicle.get("id", "unknown"),
                    "vehicle_license_plate": license_plate,
                    "timestamp": format_timestamp(timestamp),
                    "speed_km": speed,
                    "stop_id": current_stop_id,
                    "latitude": latitude,
                    "longitude": longitude,
                    "current_status": current_status,
                    "congestion_level": congestion_level,
                    "occupancy_status": occupancy_status,
                    "occupancy_percentage": occupancy_percentage,
                }
            )

        return {"total_active_runs": len(active_runs), "active_runs": active_runs}
    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching active runs: {str(e)}")
        return {"error": str(e)}