from urllib.parse import urlparse

from . import mcp
from fastmcp import Context
from mcp.types import ToolAnnotations
from utils.databus_client import get_client


@mcp.tool(
    name="get_operator_current_assignment",
    description="Get the current assignment of an operator, including vehicle ID, route, and trip information.",
    tags={"operations", "operators", "assignments", "read-only"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_operator_current_assignment(
    operator_input: str, ctx: Context | None = None
) -> dict:
    """Get the current assignment of an operator, including vehicle ID, route, and trip information.

    arguments:
        - operator_input: The operator ID to fetch the current assignment for.
        - ctx: Optional context for logging and additional information during execution.

    returns:
        - A dictionary containing the operator ID, vehicle ID, route ID, trip ID, start time, and start date.
        - If an error occurs or no active runs are found, an error message is included in the response.
    """
    try:
        client = get_client()
        if ctx:
            await ctx.info(
                f"Fetching current assignment for operator_id: {operator_input}"
            )

        operator_input = operator_input.strip()

        run_info = await client.get_api("run")

        for run in run_info:
            if (
                run.get("operator") == operator_input
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
                    "operator_id": operator_id,
                    "vehicle_id": vehicle_id,
                    "route_id": route_id,
                    "trip_id": trip_id,
                    "start_time": start_time,
                    "start_date": start_date,
                    "run_id": run_id,
                }
                return {"current_assignment": current_assigment}

        return {"error": f"No active runs found for operator {operator_input}"}

    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching operator current assignment: {str(e)}")
        return {"error": str(e), "operator_input": operator_input}


@mcp.tool(
    name="get_operator_assignment_history",
    description="Get the assignment history of an operator, including past runs, vehicles, and routes.",
    tags={"operations", "operators", "history", "read-only"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_operator_run_assignment_history(
    operator_id: str, ctx: Context | None = None
) -> dict:
    """Get the assignment history of an operator, including past runs, vehicles, and routes.

    arguments:
        - operator_id: The operator ID to fetch the assignment history for.
        - ctx: Optional context for logging and additional information during execution.

    returns:
        - A dictionary containing the operator ID and a list of completed runs with their details.
        - If an error occurs or no completed runs are found, an error message is included in the response.
    """
    try:
        client = get_client()
        if ctx:
            await ctx.info(f"Fetching completed runs for operator_id: {operator_id}")

        operator_id = operator_id.strip()
        run_info = await client.get_api(f"run")

        completed_runs = []
        if not "error" in run_info and run_info:
            for run in run_info:
                if run.get("operator") == operator_id:
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
                            "trip_id": run.get("trip_id", "unknown"),
                            "run_status": run.get("run_status", "unknown"),
                        }
                    )
            return {"operator_id": operator_id, "assignment_history": completed_runs}

        return {
            "operator_id": operator_id,
            "error": f"No runs found for operator {operator_id}",
        }
    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching operator assignment history: {str(e)}")
        return {"error": str(e), "operator_id": operator_id}
