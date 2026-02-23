from fastmcp import FastMCP, Context
from mcp.types import ToolAnnotations
from utils.common import  filter_by_field, format_timestamp, normalize_text
from utils.databus_client import get_client
from urllib.parse import urlparse


mcp = FastMCP("operations")

@mcp.tool(
    name="vehicles_list_by_company",
    description="Get a list of vehicles filtered by company name. Requires company name or code as input.",
    tags={"fleet", "vehicles", "read-only"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_vehicles_list_by_company(
    company_input: str,
    ctx: Context | None = None
) -> dict:
    try:
        resolved_company = await resolve_company_code(company_input, ctx)
        if "error" in resolved_company:
            return resolved_company
        
        company_code = resolved_company["company_code"]
        company_name = resolved_company["company_name"]

        client = get_client()

        if ctx:
            await ctx.info(f"Fetching vehicles for company: {company_code} {company_name}")
        
        vehicles = await client.get_api("vehicle")


        if ctx:
            await ctx.info(f"company_code: {company_code}")
            await ctx.info(f"vehicle companies: {[v.get('company', '') for v in vehicles]}")
        
        # TODO: Normalize vehicle ID input (e.g., remove spaces, uppercase) and handle common variations
        filtered_vehicles = [
            v for v in vehicles
            if normalize_text(v.get("company", "")) == normalize_text(company_code)
        ]

        if not filtered_vehicles:
            return {
                    "error": "No vehicles found for company",
                    "company_code": company_code,
                    "company_name": company_name
            }
        
        if ctx:
            await ctx.info(f"Found {len(filtered_vehicles)} vehicles for company: {company_code}, {company_name}")

        vehicles_list = []  
        for  v in filtered_vehicles:
            vehicles_list.append({
                "label": v["label"],
                "license_plate": v["license_plate"],
                "status": v.get("status", "unknown")
            })

        return {
            "company_input": company_input,
            "company_code": company_code,
            "company_name": company_name,
            "total_vehicles": len(filtered_vehicles),
            "vehicles": vehicles_list
        }
    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching vehicles list: {str(e)}")
        return {"error": str(e), "company_input": company_input}


@mcp.tool(
    name="companies_list",
    description="Get a list of all companies with their codes and names.",
    tags={"operations", "companies", "read-only"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_all_companies(ctx: Context | None = None) -> dict:
    try:
        client = get_client()
        if ctx:
            await ctx.info("Fetching list of companies from vehicles API")
        companies = await client.get_api("company")
        if ctx:
            await ctx.info(f"Found {len(companies)} unique companies")
        companies_cleaned = []
        for c in companies:
            parsed = urlparse(c["url"])
            path_parts = parsed.path.rstrip("/").split("/")
            code = path_parts[-1]
            companies_cleaned.append({
                "code": code,
                "name": c["name"]
            })
        return {
            "total_companies": len(companies_cleaned),
            "companies": companies_cleaned
        }
    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching companies: {str(e)}")
        return {"error": str(e)}
    
@mcp.tool(
    name="get_all_routes",
    description="Get a list of all routes.",
    tags={"fleet", "routes", "read-only"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_all_routes(
    ctx: Context | None = None
) -> dict:
    client = get_client()
    try:
        if ctx:
            await ctx.info("Fetching all routes information")
        
        #Feed/API to get complete info
        routes_info = await client.get_api(f"routes")

        if ctx:
            await ctx.info(f"Total routes fetched: {len(routes_info)}")
        
        routes_cleaned = []
        for r in routes_info:
            routes_cleaned.append({
                "route_id": r.get("route_id", "unknown"),
                "agency_id": r.get("agency_id", "unknown"),
                "route_short_name": r.get("route_short_name", "unknown"),
                "route_long_name": r.get("route_long_name", "unknown"),
                "route_desc": r.get("route_desc", "unknown"),
            })
        
        return {
            "total_routes": len(routes_cleaned),
            "routes": routes_cleaned
        }
    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching all routes: {str(e)}")
        return {"error": str(e)}


    
@mcp.tool(
    name="resolve_company_code",
    description="Resolve a company input (code or name) to the internal company code.",
    tags={"operations", "companies", "read-only"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def resolve_company_code(
    company_input: str,
    ctx: Context | None = None
) -> dict:
   try:
        companies_data = await get_all_companies(ctx)
        
        if "error" in companies_data:
            return {
                "company_input": company_input,
                "error": f"Failed to fetch companies: {companies_data['error']}"
            }
        companies = companies_data.get("companies", [])

        normalized_input = normalize_text(company_input)
        matches = []

    
        for c in companies:
            code_normalized = normalize_text(c["code"])
            name_normalized = normalize_text(c["name"])
            if normalized_input == code_normalized or normalized_input == name_normalized:
                matches.append(c)
                
        if not matches:
            return {
            "company_input": company_input,
            "normalized_input": normalized_input,
            "error": "Company not found"
        }   
        
        if len(matches) > 1:
            return {
                "company_input": company_input,
                "error": "Multiple companies found",
                "candidates": [
                    {"company_code": c["code"],
                    "company_name": c["name"]}
                    for c in matches
            ]
            }

        # Exact single match
        match = matches[0]

        return {
            "company_input": company_input,
            "company_code": match["code"],
            "company_name": match["name"]
        }
   except Exception as e:
        if ctx:
            await ctx.error(f"Error resolving company code: {str(e)}")
        return {"error": str(e), "company_input": company_input}
    
@mcp.tool(
    name="operators_list",
    description="Return codes (IDs) of all operators.",
    tags={"operations", "operators", "read-only"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_all_operators_id(ctx: Context | None = None) -> dict:
    try:
        client = get_client()
        if ctx:
            await ctx.info("Fetching list of operators from vehicles API")
        operators = await client.get_api("operator")
        if ctx:
            await ctx.info(f"Found {len(operators)} unique operators")
        operators_cleaned = []
        for o in operators:
            parsed = urlparse(o["url"])
            path_parts = parsed.path.rstrip("/").split("/")
            code = path_parts[-1]
            operators_cleaned.append({
                "code": code,
            })
        return {
            "total_operators": len(operators_cleaned),
            "operators": operators_cleaned
        }
    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching operators: {str(e)}")
        return {"error": str(e)}


@mcp.tool(
    name="get_operator_by_id",
    description="Get operator information by operator ID.",
    tags={"operations", "operators", "read-only"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_operator_by_id(
    operator_input: str,
    ctx: Context | None = None
) -> dict:
    
    try:
        client = get_client()
        if ctx:
            await ctx.info(f"Resolving operator input: {operator_input}")
    
        # TODO: Normalize operator ID input (e.g., remove spaces, uppercase) and handle common variations
        operator_code = operator_input.strip()
        
        operator_data = await client.get_api(f"operator/{operator_code}")        
        if "error" in operator_data or not operator_data:
            return {
                "operator_input": operator_input,
                "error": f"Operator details not found{operator_data}"
            }
        
        return {
            "operator_code": operator_code,
            "company_code": operator_data.get("company", "unknown"),
            "phone": operator_data.get("phone", "unknown")  
        }
    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching operator info: {str(e)}")
        return {"error": str(e), "operator_input": operator_input}

@mcp.tool(
    name="get_operator_id_by_vehicle",
    description="Get operator information by vehicle ID.",
    tags={"operations", "operators", "vehicles", "read-only"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_operator_id_by_vehicle(
    vehicle_input: str,
    ctx: Context | None = None
) -> dict:
    try:
        client = get_client()
        if ctx:
            await ctx.info(f"Fetching operator for vehicle_id: {vehicle_input}")
        
        vehicle_id = vehicle_input.strip()
        run_info = await client.get_api("run")
        
        if "error" in run_info or not run_info:
            return {
                "vehicle_id": vehicle_input,
                "error": f"Operator details not found for {vehicle_input}"
            }
        
        operators = set()
        for run in run_info:
            if run.get("vehicle", "") == vehicle_id:
                operator_id = run.get("operator", "unknown")
                operators.add(operator_id)
        
        if operators:
            return {
                "vehicle_id": vehicle_id,
                "operator_ids": list(operators)
            }
        else:
            return {
                "vehicle_id": vehicle_input,
                "error": "Operator not found for this vehicle"
            }
    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching operator by vehicle: {str(e)}")
        return {"error": str(e), "vehicle_id": vehicle_input}



@mcp.tool(
    name="get_vehicle_id_by_operator",
    description="Get vehicle information by operator ID.",
    tags={"operations", "operators", "vehicles", "read-only"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_vehicle_id_by_operator_id(
    operator_input: str,
    ctx: Context | None = None
) -> dict:
    try:
        client = get_client()
        if ctx:
            await ctx.info(f"Fetching vehicle information for operator_id: {operator_input}")
            
        operator_id = operator_input.strip()
        run_info = await client.get_api("run")
        if "error" in run_info or not run_info:
            return {
                "operator_id": operator_input,
                "error": f"Vehicle details not found for {operator_input}"
            }
        
        vehicles = set()
        for run in run_info:
            if run.get("operator") == operator_id:
                vehicle = run.get("vehicle", "unknown")
                vehicles.add(vehicle)
        return {
            "operator_id": operator_id,
            "vehicle_ids": list(vehicles)
        }
    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching vehicle by operator: {str(e)}")
        return {"error": str(e), "operator_id": operator_input}

@mcp.tool(
    name="get_operators_by_company_id",
    description="Get a list of operators for a specific company ID or name.",
    tags={"operations", "operators", "companies", "read-only"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_operators_by_company(
    company_input: str,
    ctx: Context | None = None
) -> dict:
    try:
        client = get_client()
        
        if ctx:
            await ctx.info(f"Fetching operator information for company_id: {company_input}")
        
        company_input = company_input.strip()
        
        resolve_company_code_result = await resolve_company_code(company_input, ctx)
        
        companies_data = await client.get_api(f"company/{resolve_company_code_result.get('company_code', '')}")
        company_code = resolve_company_code_result.get("company_code", "unknown")
        
            
        if not companies_data or companies_data.get("name") != resolve_company_code_result.get("company_name"):
            return {
                "company_id": company_input,
                "error": f"Company details not found or company name mismatch for {company_input}"
            }
                
        
        operators_data = await get_all_operators_id(ctx)
        
        if "error" in operators_data or not operators_data:
            return {
                "company_id": company_input,
                "error": f"Operators details not found for {company_input}"
            }
            
        operator_ids = [op["code"] for op in operators_data.get("operators", [])]
                
        return {
            "company_id": company_code,
            "company_name": companies_data.get("name", "unknown"),
            "operators": operator_ids
        }
        
    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching operator by company: {str(e)}")
        return {"error": str(e), "company_id": company_input}

@mcp.tool(
    name="get_operator_current_assignment",
    description="Get the current assignment of an operator, including vehicle ID, route, and trip information.",
    tags={"operations", "operators", "assignments", "read-only"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_operator_current_assignment(
    operator_input: str,
    ctx: Context | None = None
) -> dict:
    try:
        client = get_client()
        if ctx:
            await ctx.info(f"Fetching current assignment for operator_id: {operator_input}")
        
        operator_input = operator_input.strip()
        
        run_info = await client.get_api("run")
        #TODO: Check if a operator only has one active run at a time or can have multiple. 
        for run in run_info:
            if run.get("operator") == operator_input and run.get("run_status") == "IN_PROGRESS":
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
                }
                return {
                    "current_assignment": current_assigment
                }
        
        return {"error": f"No active runs found for operator {operator_input}"}
        
    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching operator current assignment: {str(e)}")
        return {"error": str(e), "operator_input": operator_input}
    
@mcp.tool(
    name="get_current_route_info",
    description="Get current information about a route, including active runs, assigned vehicles, and operators.",
    tags={"operations", "routes", "active runs", "read-only"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_current_route_info(
    route_input: str,
    ctx: Context | None = None
) -> dict:
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
                "error": f"Route details not found for {route_input}"
            }
        
        run_info = await client.get_api(f"run")
    
        active_runs = []
        if not "error" in run_info and run_info:
            for run in run_info:
                if run.get("route_id") == route_input and run.get("run_status") == "IN_PROGRESS":
                    
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
                    }
                    active_runs.append(current_assigment)
        return {
            "route_id": route_input,
            "route_short_name": route.get("route_short_name", "unknown"),
            "route_long_name": route.get("route_long_name", "unknown"),
            "route_desc": route.get("route_desc", "unknown"),
            "active_runs": active_runs
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
    route_input: str,
    ctx: Context | None = None
) -> dict:
    try:
        client = get_client()
        if ctx:
            await ctx.info(f"Fetching current assigned vehicles for route_id: {route_input}")
        route_input = route_input.strip()
        
        run_info = await client.get_api(f"run")
        
        if run_info and not "error" in run_info:
            assigned_vehicles = []
            for run in run_info:
                if run.get("route_id") == route_input and run.get("run_status") == "IN_PROGRESS":
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
                    }
                    assigned_vehicles.append(current_assigment)
            return {
                "route_id": route_input,
                "assigned_vehicles": assigned_vehicles
            }
        
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
    route_id: str,
    ctx: Context | None = None
) -> dict:
    try:
        client = get_client()
        if ctx:
            await ctx.info(f"Fetching current assigned operators for route_id: {route_id}")
        route_id = route_id.strip()
        
        run_info = await client.get_api(f"run")
        
        if run_info and not "error" in run_info:
            assigned_operators = []
            for run in run_info:
                if run.get("route_id") == route_id and run.get("run_status") == "IN_PROGRESS":
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
                    }
                    assigned_operators.append(current_assigment)
            return {
                "route_id": route_id,
                "assigned_operators": assigned_operators
            }
        
    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching assigned operators by route: {str(e)}")
        return {"error": str(e), "route_id": route_id}


@mcp.tool(
    name="get_operator_assignment_history",
    description="Get the assignment history of an operator, including past runs, vehicles, and routes.",
    tags={"operations", "operators", "history", "read-only"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_operator_run_assignment_history(
    operator_id: str,
    day_input: str,
    ctx: Context | None = None
) -> dict:
    try:
        client = get_client()
        if ctx:
            await ctx.info(f"Fetching completed runs for operator_id: {operator_id} on date: {day_input}")
        
        operator_id = operator_id.strip()
        run_info = await client.get_api(f"run")
        
        completed_runs = []
        if not "error" in run_info and run_info:
            for run in run_info:
                if run.get("operator") == operator_id:
                    
                    completed_runs.append({
                        "vehicle_id": run.get("vehicle", "unknown"),
                        "route_id": run.get("route_id", "unknown"),
                        "start_time": run.get("start_time", "unknown"),
                        "start_date": run.get("start_date", "unknown"),
                        "trip_id": run.get("trip_id", "unknown"),
                        "run_status": run.get("run_status", "unknown")
                    })
            return {
                "operator_id": operator_id,
                "assignment_history": completed_runs
            }
        
        return {
            "operator_id": operator_id,
            "error": f"No runs found for operator {operator_id}"
        }
    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching operator assignment history: {str(e)}")
        return {"error": str(e), "operator_id": operator_id, "day_input": day_input}            

async def get_operators_by_route(
    route_id: str,
    ctx: Context | None = None) -> dict:
    try:
        client = get_client()
        if ctx:
            await ctx.info(f"Fetching operators for route_id: {route_id}")
        
        route_id = route_id.strip()
        run_info = await client.get_api(f"run")
        
        operators = []
        if not "error" in run_info and run_info:
            for run in run_info:
                if run.get("route_id") == route_id:
                    operator_id = run.get("operator", "unknown")
                    vehicle_id = run.get("vehicle", "unknown")
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
                    }
                    operators.append(current_assigment)
            return {
                "route_id": route_id,
                "operators": operators
            }
        
    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching operators by route: {str(e)}")
        return {"error": str(e), "route_id": route_id}

@mcp.tool(
    name="get_company_fleet_run_status",
    description="Get the current run status of all vehicles for a specific company.",
    tags={"operations", "companies", "fleet status", "read-only"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_company_fleet_run_status(
    company_id: str,
    ctx: Context | None = None
) -> dict:
    try:
        client = get_client()
        if ctx:
            await ctx.info(f"Fetching fleet status for company_id: {company_id}")
        
        company_id = company_id.strip()
        run_info = await client.get_api(f"run")
        vehicles_info = await client.get_api(f"vehicle")
        
        company_vehicles = [
            v for v in vehicles_info
            if v.get("company", "unknown") == company_id
        ]
        fleet_status = []
        
        for v in company_vehicles:
            vehicle_id = v.get("license_plate", "unknown")
            vehicle_status = v.get("status", "unknown")
            assignment = None
            if run_info:
                for run in run_info:
                    if run.get("vehicle") == vehicle_id and run.get("run_status") == "IN_PROGRESS":
                        assignment = {
                            "operator_id": run.get("operator", "unknown"),
                            "route_id": run.get("route_id", "unknown"),
                            "trip_id": run.get("trip_id", "unknown"),
                            "start_time": run.get("start_time", "unknown"),
                            "start_date": run.get("start_date", "unknown"),
                            "run_status": run.get("run_status", "unknown"),
                        }
                        break
            fleet_status.append({
                "vehicle_id": vehicle_id,
                "vehicle_status": vehicle_status,
                "assignment": assignment
            })

        return {
            "company_id": company_id,
            "fleet_status": fleet_status
        }
    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching company fleet status: {str(e)}")
        return {"error": str(e), "company_id": company_id}
    

@mcp.tool(
    name="get_trips_by_route",
    description="Get a list of trips associated with a specific route.",
    tags={"operations", "routes", "trips", "read-only"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_trips_by_route(
    route_id: str,
    ctx: Context | None = None
) -> dict:
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
                    
                    trips.append({
                        "trip_id": trip_id,
                        "trip": trip.get("trip_id", "unknown"),
                        "trip_headsign": trip.get("trip_headsign", "unknown"),
                        "direction_id": trip.get("direction_id", "unknown"),
                        "wheelchair_accessible": trip.get("wheelchair_accessible", "unknown"),
                        "bikes_allowed": trip.get("bikes_allowed", "unknown"),
                    })
            
        if not trips:
            return {
                "route_id": route_id,
                "error": f"No trips found for route {route_id}"
            }
                
        return {
            "route_id": route_id,
            "trips": trips
        }
        
    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching trips by route: {str(e)}")
        return {"error": str(e), "route_id": route_id}
    

if __name__ == "__main__":
    mcp.run()