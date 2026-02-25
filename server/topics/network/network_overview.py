from . import mcp
from fastmcp import Context
from mcp.types import ToolAnnotations
from utils.databus_client import get_client


@mcp.tool(
    name="route_overview",
    description="Get an overview of the current route status, including congestion levels and occupancy for all routes.",
    tags={"network", "overview", "read-only"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_route_overview(route_input: str, ctx: Context | None = None) -> dict:
    """Get an overview of the current route status, including congestion levels and occupancy for all routes.

    arguments:
        - route_input: The route ID or name to get the overview for.
        - ctx: Optional context for logging and additional information during execution.

    returns:
        - A dictionary containing the route overview information, including congestion levels and occupancy status.
        - If the route is not found or an error occurs, an error message is included in the response.
    """
    try:
        client = get_client()
        route_id = route_input.strip()

        if ctx:
            await ctx.info("Fetching route overview data")
        feed = await client.get_feed("vehicle_positions")

        if not feed or "entity" not in feed:
            return {"error": "No feed data available"}

        vehicles = []
        route_found = False
        for entity in feed["entity"]:
            vehicle_data = entity.get("vehicle", {})
            trip = vehicle_data.get("trip", {})
            route = trip.get("route_id", "unknown")
            if route != route_id:
                continue
            route_found = True

            congestion = vehicle_data.get("congestion_level", "unknown")
            occupancy = vehicle_data.get("occupancy_status", "unknown")
            occupancy_percentage = vehicle_data.get("occupancy_percentage", "unknown")
            speed = vehicle_data.get("position", {}).get("speed", "unknown")

            vehicles.append(
                {
                    "congestion": congestion,
                    "occupancy": occupancy,
                    "occupancy_percentage": occupancy_percentage,
                    "speed": speed,
                }
            )

        if not route_found:
            return {"error": f"Route {route_id} not found in feed data"}
        if not vehicles:
            return {"error": f"No vehicles found for route {route_id}"}

        congestions = [
            v["congestion"] for v in vehicles if v["congestion"] != "unknown"
        ]
        occ_percents = [
            float(v["occupancy_percentage"])
            for v in vehicles
            if v["occupancy_percentage"] != "unknown"
        ]
        occupancies = [v["occupancy"] for v in vehicles if v["occupancy"] != "unknown"]
        speeds = [float(v["speed"]) for v in vehicles if v["speed"] != "unknown"]

        route_overview = {
            "route_id": route_id,
            "total_vehicles": len(vehicles),
            "main_congestion_level": max(set(congestions), key=congestions.count),
            "main_occupancy_status": max(set(occupancies), key=occupancies.count),
            "average_occupancy_percentage": (
                sum(occ_percents) / len(occ_percents) if occ_percents else 0
            ),
            "average_speed_km": sum(speeds) / len(speeds) if speeds else 0,
        }
        return {"route_overview": route_overview}
    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching network overview: {str(e)}")
        return {"error": str(e)}


@mcp.tool(
    name="congestion_status_by_route",
    description="Get the current congestion status for a specific route, including congestion levels and average speed.",
    tags={"network", "congestion", "read-only"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_congestion_status_by_route(
    route_id: str, ctx: Context | None = None
) -> dict:
    """Get the current congestion status for a specific route, including congestion levels and average speed.

    arguments:
        - route_id: The route ID or name to get congestion status for.
        - ctx: Optional context for logging and additional information during execution.

    returns:
        - A dictionary containing the route ID, main congestion level, and average speed.
        - If an error occurs or no data is found, an error message is included in the response.
    """
    try:
        client = get_client()

        route_id = route_id.strip()
        if ctx:
            await ctx.info(f"Fetching congestion status for route: {route_id}")

        feed = await client.get_feed("vehicle_positions")
        if not feed or "entity" not in feed:
            return {"error": "No feed data available"}

        vehicles = []
        route_found = False
        for entity in feed["entity"]:
            vehicle_data = entity.get("vehicle", {})
            trip = vehicle_data.get("trip", {})
            route = trip.get("route_id", "unknown")
            if route != route_id:
                continue
            route_found = True
            congestion = vehicle_data.get("congestion_level", "unknown")
            vehicles.append(
                {
                    "congestion": congestion,
                    "speed": vehicle_data.get("position", {}).get("speed", "unknown"),
                }
            )
        if not route_found:
            return {"error": f"Route {route_id} not found in feed data"}
        if not vehicles:
            return {"error": f"No vehicles found for route {route_id}"}
        congestions = [
            v["congestion"] for v in vehicles if v["congestion"] != "unknown"
        ]
        speeds = [float(v["speed"]) for v in vehicles if v["speed"] != "unknown"]

        route_congestion_status = {
            "route_id": route_id,
            "main_congestion_level": (
                max(set(congestions), key=congestions.count)
                if congestions
                else "unknown"
            ),
            "average_speed_km": sum(speeds) / len(speeds) if speeds else 0,
        }
        return {"route_congestion_status": route_congestion_status}
    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching congestion status: {str(e)}")
        return {"error": str(e)}
