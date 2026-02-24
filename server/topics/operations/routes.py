from urllib.parse import urlparse

from . import mcp
from fastmcp import Context
from mcp.types import ToolAnnotations
from utils.databus_client import get_client


@mcp.tool(
    name="get_all_routes",
    description="Get a list of all routes.",
    tags={"fleet", "routes", "read-only"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_all_routes(ctx: Context | None = None) -> dict:
    """Get a list of all routes.

    arguments:
        - ctx: Optional context for logging and additional information during execution.

    returns:
        - A dictionary containing the total number of routes and a list of routes with their details.
        - If an error occurs, an error message is included in the response.
    """
    try:
        client = get_client()
        if ctx:
            await ctx.info("Fetching all routes information")

        routes_info = await client.get_api(f"routes")

        if ctx:
            await ctx.info(f"Total routes fetched: {len(routes_info)}")

        routes_cleaned = []
        for r in routes_info:
            routes_cleaned.append(
                {
                    "route_id": r.get("route_id", "unknown"),
                    "agency_id": r.get("agency_id", "unknown"),
                    "route_short_name": r.get("route_short_name", "unknown"),
                    "route_long_name": r.get("route_long_name", "unknown"),
                    "route_desc": r.get("route_desc", "unknown"),
                }
            )

        return {"total_routes": len(routes_cleaned), "routes": routes_cleaned}
    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching all routes: {str(e)}")
        return {"error": str(e)}


@mcp.tool(
    name="get_current_route_info",
    description="Get current information about a route, including active runs, assigned vehicles, and operators.",
    tags={"operations", "routes", "active runs", "read-only"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_current_route_info(route_input: str, ctx: Context | None = None) -> dict:
    """Get current information about a route, including active runs, assigned vehicles, and operators.

    arguments:
        - route_input: The route ID to fetch information for.
        - ctx: Optional context for logging and additional information during execution.

    returns:
        - A dictionary containing the route ID, route short name, route long name, route description, and a list of active runs.
        - If an error occurs or the route is not found, an error message is included in the response.
    """
    try:
        client = get_client()
        if ctx:
            await ctx.info(f"Fetching route information for route_id: {route_input}")

        route_input = route_input.strip()

        route_info = await client.get_api(f"routes")

        route = None
        for r in route_info:
            if r.get("route_id") == route_input:
                route = r
                break

        if not route:
            return {
                "route_input": route_input,
                "error": f"Route details not found for {route_input}",
            }

        run_info = await client.get_api(f"run")

        active_runs = []
        if not "error" in run_info and run_info:
            for run in run_info:
                if (
                    run.get("route_id") == route_input
                    and run.get("run_status") == "IN_PROGRESS"
                ):
                    url = run.get("url", "unknown")
                    parsed = urlparse(url)
                    path_parts = parsed.path.rstrip("/").split("/")
                    run_id = path_parts[-1]
                    vehicle_id = run.get("vehicle", "unknown")
                    operator_id = run.get("operator", "unknown")
                    trip_id = run.get("trip_id", "unknown")
                    start_date = run.get("start_date", "unknown")
                    route_id = run.get("route_id", "unknown")
                    start_time = run.get("start_time", "unknown")
                    current_assigment = {
                        "run_id": run_id,
                        "operator_id": operator_id,
                        "vehicle_id": vehicle_id,
                        "route_id": route_id,
                        "trip_id": trip_id,
                        "start_time": start_time,
                        "start_date": start_date,
                    }
                    active_runs.append(current_assigment)
        return {
            "route_id": route_input,
            "route_short_name": route.get("route_short_name", "unknown"),
            "route_long_name": route.get("route_long_name", "unknown"),
            "route_desc": route.get("route_desc", "unknown"),
            "active_runs": active_runs,
        }

    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching route info: {str(e)}")
        return {"error": str(e), "route_input": route_input}


@mcp.tool(
    name="get_current_assigned_vehicles_by_route",
    description="Get a list of currently assigned vehicles for a specific route.",
    tags={"operations", "routes", "vehicles", "active runs", "read-only"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_current_assigned_vehicles_by_route(
    route_input: str, ctx: Context | None = None
) -> dict:
    """Get a list of currently assigned vehicles for a specific route.

    arguments:
        - route_input: The route ID to fetch assigned vehicles for.
        - ctx: Optional context for logging and additional information during execution.
    returns:
        - A dictionary containing the route ID and a list of assigned vehicles with their details.
        - If an error occurs or no active runs are found, an error message is included in the response.
    """
    try:
        client = get_client()
        if ctx:
            await ctx.info(
                f"Fetching current assigned vehicles for route_id: {route_input}"
            )
        route_input = route_input.strip()

        run_info = await client.get_api(f"run")

        if run_info and not "error" in run_info:
            assigned_vehicles = []
            for run in run_info:
                if (
                    run.get("route_id") == route_input
                    and run.get("run_status") == "IN_PROGRESS"
                ):
                    url = run.get("url", "unknown")
                    parsed = urlparse(url)
                    path_parts = parsed.path.rstrip("/").split("/")
                    run_id = path_parts[-1]
                    vehicle_id = run.get("vehicle", "unknown")
                    operator_id = run.get("operator", "unknown")
                    trip_id = run.get("trip_id", "unknown")
                    start_date = run.get("start_date", "unknown")
                    route_id = run.get("route_id", "unknown")
                    start_time = run.get("start_time", "unknown")
                    current_assigment = {
                        "run_id": run_id,
                        "operator_id": operator_id,
                        "vehicle_id": vehicle_id,
                        "route_id": route_id,
                        "trip_id": trip_id,
                        "start_time": start_time,
                        "start_date": start_date,
                    }
                    assigned_vehicles.append(current_assigment)
            return {"route_id": route_input, "assigned_vehicles": assigned_vehicles}

    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching assigned vehicles by route: {str(e)}")
        return {"error": str(e), "route_input": route_input}


@mcp.tool(
    name="get_current_assigned_operators_by_route",
    description="Get a list of currently assigned operators for a specific route.",
    tags={"operations", "routes", "operators", "active runs", "read-only"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_current_assigned_operators_by_route(
    route_id: str, ctx: Context | None = None
) -> dict:
    """Get a list of currently assigned operators for a specific route.

    arguments:
        - route_id: The route ID to fetch assigned operators for.
        - ctx: Optional context for logging and additional information during execution.

    returns:
        - A dictionary containing the route ID and a list of assigned operators with their details.
        - If an error occurs or no active runs are found, an error message is included in the response.
    """
    try:
        client = get_client()
        if ctx:
            await ctx.info(
                f"Fetching current assigned operators for route_id: {route_id}"
            )
        route_id = route_id.strip()

        run_info = await client.get_api(f"run")

        if run_info and not "error" in run_info:
            assigned_operators = []
            for run in run_info:
                if (
                    run.get("route_id") == route_id
                    and run.get("run_status") == "IN_PROGRESS"
                ):
                    url = run.get("url", "unknown")
                    parsed = urlparse(url)
                    path_parts = parsed.path.rstrip("/").split("/")
                    run_id = path_parts[-1]
                    vehicle_id = run.get("vehicle", "unknown")
                    operator_id = run.get("operator", "unknown")
                    trip_id = run.get("trip_id", "unknown")
                    start_date = run.get("start_date", "unknown")
                    route_id = run.get("route_id", "unknown")
                    start_time = run.get("start_time", "unknown")
                    current_assigment = {
                        "run_id": run_id,
                        "operator_id": operator_id,
                        "vehicle_id": vehicle_id,
                        "route_id": route_id,
                        "trip_id": trip_id,
                        "start_time": start_time,
                        "start_date": start_date,
                    }
                    assigned_operators.append(current_assigment)
            return {"route_id": route_id, "assigned_operators": assigned_operators}

    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching assigned operators by route: {str(e)}")
        return {"error": str(e), "route_id": route_id}


@mcp.tool(
    name="get_trips_by_route",
    description="Get a list of trips associated with a specific route.",
    tags={"operations", "routes", "trips", "read-only"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_trips_by_route(route_id: str, ctx: Context | None = None) -> dict:
    """Get a list of trips associated with a specific route.

    arguments:
        - route_id: The route ID to fetch trips for.
        - ctx: Optional context for logging and additional information during execution.

    returns:
        - A dictionary containing the route ID and a list of trips with their details.
        - If an error occurs or no trips are found, an error message is included in the response.
    """
    try:
        client = get_client()
        if ctx:
            await ctx.info(f"Fetching trips for route_id: {route_id}")

        route_id = route_id.strip()
        trips_info = await client.get_api(f"trips")

        trips = []
        if not "error" in trips_info and trips_info:
            for trip in trips_info:
                if trip.get("route_id") == route_id:
                    parsed = urlparse(trip["url"])
                    path_parts = parsed.path.rstrip("/").split("/")
                    trip_id = path_parts[-1]

                    trips.append(
                        {
                            "trip_id": trip_id,
                            "trip": trip.get("trip_id", "unknown"),
                            "trip_headsign": trip.get("trip_headsign", "unknown"),
                            "direction_id": trip.get("direction_id", "unknown"),
                            "wheelchair_accessible": trip.get(
                                "wheelchair_accessible", "unknown"
                            ),
                            "bikes_allowed": trip.get("bikes_allowed", "unknown"),
                        }
                    )

        if not trips:
            return {
                "route_id": route_id,
                "error": f"No trips found for route {route_id}",
            }

        return {"route_id": route_id, "trips": trips}

    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching trips by route: {str(e)}")
        return {"error": str(e), "route_id": route_id}
