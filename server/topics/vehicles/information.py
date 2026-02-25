from urllib.parse import urlparse
from . import mcp
from fastmcp import Context
from mcp.types import ToolAnnotations

from topics.operations import resolve_company_code
from utils.common import normalize_text
from utils.databus_client import get_client
from datetime import datetime


@mcp.tool(
    name="vehicles_list_by_company",
    description="Get a list of vehicles filtered by company name. Requires company name or code as input.",
    tags={"fleet", "vehicles", "read-only"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_vehicles_list_by_company(
    company_input: str, ctx: Context | None = None
) -> dict:
    """Fetch a list of vehicles that belong to a specific company. The input can be either the company name or code.

    arguments:
        - company_input: The name or code of the company to filter vehicles by.
        - ctx: Optional context for logging and additional information during execution.

    returns:
        - A dictionary containing the company code, company name, total number of vehicles found, and a list of vehicles with their label, license plate, and status.
        - If an error occurs or no vehicles are found, an error message is included in the response.
    """
    try:
        resolved_company = await resolve_company_code(company_input, ctx)
        if "error" in resolved_company:
            return resolved_company

        company_code = resolved_company["company_code"]
        company_name = resolved_company["company_name"]

        client = get_client()

        if ctx:
            await ctx.info(
                f"Fetching vehicles for company: {company_code} {company_name}"
            )

        vehicles = await client.get_api("vehicle")

        if ctx:
            await ctx.info(f"company_code: {company_code}")
            await ctx.info(
                f"vehicle companies: {[v.get('company', '') for v in vehicles]}"
            )

        filtered_vehicles = [
            v
            for v in vehicles
            if normalize_text(v.get("company", "")) == normalize_text(company_code)
        ]

        if not filtered_vehicles:
            return {
                "error": "No vehicles found for company",
                "company_code": company_code,
                "company_name": company_name,
            }

        if ctx:
            await ctx.info(
                f"Found {len(filtered_vehicles)} vehicles for company: {company_code}, {company_name}"
            )

        vehicles_list = []
        for v in filtered_vehicles:
            vehicles_list.append(
                {
                    "label": v["label"],
                    "license_plate": v["license_plate"],
                    "status": v.get("status", "unknown"),
                }
            )

        return {
            "company_input": company_input,
            "company_code": company_code,
            "company_name": company_name,
            "total_vehicles": len(filtered_vehicles),
            "vehicles": vehicles_list,
        }
    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching vehicles list: {str(e)}")
        return {"error": str(e), "company_input": company_input}


@mcp.tool(
    name="all_vehicles",
    description="Get a list of all vehicles with basic information. (license plate, label, company)",
    tags={"fleet", "vehicles", "list"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_all_vehicles(ctx: Context | None = None) -> dict:
    """Fetch a list of all vehicles with basic information, including license plate, label, and company.

    arguments:
        - ctx: Optional context for logging and additional information during execution.

    returns:
        - A dictionary containing the total number of vehicles and a list of vehicles with their basic information.
        - If no vehicles are found or an error occurs, an appropriate message is included in the response.
    """
    try:
        client = get_client()
        if ctx:
            await ctx.info("Fetching all vehicles")

        vehicles = await client.get_api("vehicle")

        if "error" in vehicles:
            return {"error": "Error fetching vehicles data"}

        vehicles_cleaned = []
        for v in vehicles:
            vehicles_cleaned.append(
                {
                    "license_plate": v.get("license_plate", "unknown"),
                    "label": v.get("label", "unknown"),
                    "company": v.get("company", "unknown"),
                }
            )
        if not vehicles_cleaned:
            return {"error": "No vehicles found"}

        return {"total_vehicles": len(vehicles_cleaned), "vehicles": vehicles_cleaned}
    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching all vehicles: {str(e)}")
        return {"error": str(e)}


@mcp.tool(
    name="used_vehicles_by_route",
    description="Get a list of vehicles that have been used for a specific route. Requires route ID as input.",
    tags={"fleet", "vehicles", "route_history"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_used_vehicles_by_route(
    route_input: str, ctx: Context | None = None
) -> dict:
    """Fetch a list of vehicles that have been used for a specific route, given the route ID.

    arguments:
        - route_input: The ID of the route to fetch used vehicles for.
        - ctx: Optional context for logging and additional information during execution.

    returns:
        - A dictionary containing the route ID and a list of vehicles that have been used for the route.
        - If no vehicles are found or an error occurs, an appropriate message is included in the response.
    """
    try:
        client = get_client()
        if ctx:
            await ctx.info(f"Fetching vehicles used for route ID: {route_input}")

        route_input = route_input.strip()
        run_info = await client.get_api("run")

        used_vehicles = []

        if not "error" in run_info and run_info:
            for run in run_info:
                if (
                    run.get("route_id") == route_input
                    and run.get("run_status") == "COMPLETED"
                ):
                    url = run.get("url", "unknown")
                    parsed = urlparse(url)
                    path_parts = parsed.path.rstrip("/").split("/")
                    run_id = path_parts[-1]
                    used_vehicles.append(
                        {
                            "vehicle_id": run.get("vehicle", "unknown"),
                            "operator": run.get("operator", "unknown"),
                            "start_time": run.get("start_time", "unknown"),
                            "start_date": run.get("start_date", "unknown"),
                            "trip_id": run.get("trip_id", "unknown"),
                            "run_id": run_id,
                        }
                    )

        return {"route_id": route_input, "used_vehicles": used_vehicles}
    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching vehicles by route: {str(e)}")
        return {"error": str(e), "route_input": route_input}


@mcp.tool(
    name="vehicle_operators_history",
    description="Get a list of operators that have been assigned to a specific vehicle over time.",
    tags={"fleet", "vehicles", "history"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_all_operators_id_by_vehicle(
    vehicle_input: str, ctx: Context | None = None
) -> dict:
    """Fetch a list of operators that have been assigned to a specific vehicle over time.

    arguments:
        - vehicle_input: The license plate of the vehicle to fetch operator history for.
        - ctx: Optional context for logging and additional information during execution.

    returns:
        - A dictionary containing the vehicle ID and a list of operators that have been assigned to the vehicle over time.
        - If no operators are found or an error occurs, an appropriate message is included in the response.
    """
    try:
        client = get_client()
        if ctx:
            await ctx.info(f"Fetching all operators for vehicle ID: {vehicle_input}")

        run_info = await client.get_api("run")

        assignments = []
        seen = set()
        if run_info and not "error" in run_info:
            for run in run_info:
                if run.get("vehicle") == vehicle_input:
                    key = (
                        run.get("operator", "unknown"),
                        run.get("vehicle", "unknown"),
                        run.get("route_id", "unknown"),
                    )
                    if key not in seen:
                        seen.add(key)
                        assignments.append(
                            {
                                "operator": key[0],
                                "vehicle_license_plate": key[1],
                                "route_id": key[2],
                            }
                        )

        return {"vehicle_id": vehicle_input, "operators": assignments}
    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching vehicle operators: {str(e)}")
        return {"error": str(e), "vehicle_input": vehicle_input}


@mcp.tool(
    name="vehicle_last_operator",
    description="Get the last operator assigned to a specific vehicle.",
    tags={"fleet", "vehicles", "last_operator"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_vehicle_last_operator(
    vehicle_input: str, ctx: Context | None = None
) -> dict:
    """Fetch the last operator assigned to a specific vehicle.

    arguments:
        - vehicle_input: The license plate of the vehicle to fetch the last operator for.
        - ctx: Optional context for logging and additional information during execution.

    returns:
        - A dictionary containing the vehicle ID and the last operator assigned to the vehicle.
        - If no operator is found or an error occurs, an appropriate message is included in the response.
    """
    try:
        client = get_client()
        if ctx:
            await ctx.info(f"Fetching last operator for vehicle ID: {vehicle_input}")

        run_info = await client.get_api("run")

        latest_datetime = None
        last_run = None

        if run_info and not "error" in run_info:
            # Search if IN_PROGRESS run exists for the vehicle

            for run in run_info:
                if (
                    run.get("vehicle") == vehicle_input
                    and run.get("run_status") == "IN_PROGRESS"
                ):
                    if run.get("status") == "IN_PROGRESS":
                        last_run = run
            # If no IN_PROGRESS run, get the last completed run
            for run in run_info:
                if (
                    run.get("vehicle") == vehicle_input
                    and run.get("run_status") == "COMPLETED"
                ):
                    start_date = run.get("start_date", "")
                    start_time = run.get("start_time", "")
                    if start_date and start_time:
                        dt_str = f"{start_date} {start_time}"
                        try:

                            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                        except Exception:
                            continue
                        if latest_datetime is None or dt > latest_datetime:
                            latest_datetime = dt
                            last_run = run

            if last_run:
                url = last_run.get("url", "unknown")
                parsed = urlparse(url)
                path_parts = parsed.path.rstrip("/").split("/")
                run_id = path_parts[-1]
                return {
                    "run_id": run_id,
                    "vehicle_id": last_run.get("vehicle", "unknown"),
                    "last_operator": last_run.get("operator", "unknown"),
                    "run_status": last_run.get("run_status", "unknown"),
                    "route_id": last_run.get("route_id", "unknown"),
                    "trip_id": last_run.get("trip_id", "unknown"),
                    "start_time": last_run.get("start_time", "unknown"),
                    "start_date": last_run.get("start_date", "unknown"),
                }
            else:
                return {"vehicle_id": vehicle_input, "last_operator": "unknown"}

    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching vehicle last operator: {str(e)}")
        return {"error": str(e), "vehicle_input": vehicle_input}
