from urllib.parse import urlparse

from . import mcp
from fastmcp import Context
from mcp.types import ToolAnnotations
from utils.databus_client import get_client


@mcp.tool(
    name="completed_runs_by_day_and_vehicle",
    description="Get a list of completed runs for a specific day and vehicle, including run IDs, start times, and route information.",
    tags={"network", "completed runs", "read-only"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_complete_runs_by_day_and_vehicle(
    day_input: str, vehicle_input: str, ctx: Context | None = None
) -> dict:
    """Get a list of completed runs for a specific day and vehicle, including run IDs, start times, and route information.

    arguments:
        - day_input: The date to filter completed runs by (e.g., "2024-01-01").
        - vehicle_input: The license plate or ID of the vehicle to filter completed runs by.
        - ctx: Optional context for logging and additional information during execution.

    returns:
        - A dictionary containing the day, vehicle, and a list of completed runs.
        - If an error occurs or no data is found, an error message is included in the response.
    """
    try:
        client = get_client()
        if ctx:
            await ctx.info(
                f"Fetching completed runs for day: {day_input} and vehicle: {vehicle_input}"
            )
        run_info = await client.get_api(f"run")
        vehicle_input = vehicle_input.strip()
        day_input = day_input.strip()

        if not "error" in run_info and run_info:
            completed_runs = []
            for run in run_info:
                if (
                    run.get("vehicle") == vehicle_input
                    and run.get("start_date") == day_input
                    and run.get("run_status") == "COMPLETED"
                ):
                    url = run.get("url", "unknown")
                    parsed = urlparse(url)
                    path_parts = parsed.path.rstrip("/").split("/")
                    run_id = path_parts[-1]
                    completed_runs.append(
                        {
                            "run_id": run_id,
                            "vehicle_id": run.get("vehicle", "unknown"),
                            "route_id": run.get("route_id", "unknown"),
                            "start_time": run.get("start_time", "unknown"),
                            "start_date": run.get("start_date", "unknown"),
                            "operator_id": run.get("operator", "unknown"),
                            "trip_id": run.get("trip_id", "unknown"),
                        }
                    )
            return {
                "day": day_input,
                "vehicle": vehicle_input,
                "completed_runs": completed_runs,
            }

    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching completed runs: {str(e)}")
        return {"error": str(e), "vehicle_input": vehicle_input}


@mcp.tool(
    name="completed_runs_by_day_and_operator",
    description="Get a list of completed runs for a specific day and operator, including run IDs, start times, and route information.",
    tags={"network", "completed runs", "read-only"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_complete_runs_by_day_and_operator(
    day_input: str, operator_input: str, ctx: Context | None = None
) -> dict:
    """Get a list of completed runs for a specific day and operator, including run IDs, start times, and route information.

    arguments:
        - day_input: The date to filter completed runs by (e.g., "2024-01-01").
        - operator_input: The operator ID or name to filter completed runs by.
        - ctx: Optional context for logging and additional information during execution.

    returns:
        - A dictionary containing the day, operator, and a list of completed runs.
        - If an error occurs or no data is found, an error message is included in the response.
    """
    try:
        client = get_client()
        if ctx:
            await ctx.info(
                f"Fetching completed runs for day: {day_input} and operator: {operator_input}"
            )
        run_info = await client.get_api(f"run")
        if not "error" in run_info and run_info:
            completed_runs = []
            for run in run_info:
                if (
                    run.get("operator") == operator_input
                    and run.get("start_date") == day_input
                    and run.get("run_status") == "COMPLETED"
                ):
                    url = run.get("url", "unknown")
                    parsed = urlparse(url)
                    path_parts = parsed.path.rstrip("/").split("/")
                    run_id = path_parts[-1]
                    completed_runs.append(
                        {
                            "run_id": run_id,
                            "vehicle_id": run.get("vehicle", "unknown"),
                            "route_id": run.get("route_id", "unknown"),
                            "start_time": run.get("start_time", "unknown"),
                            "start_date": run.get("start_date", "unknown"),
                            "operator_id": run.get("operator", "unknown"),
                            "trip_id": run.get("trip_id", "unknown"),
                        }
                    )
            return {
                "day": day_input,
                "operator": operator_input,
                "completed_runs": completed_runs,
            }

    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching completed runs: {str(e)}")
        return {"error": str(e), "operator_input": operator_input}
