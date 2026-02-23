from fastmcp import FastMCP, Context
from mcp.types import ToolAnnotations

from .operations import resolve_company_code
from utils.common import  filter_by_field, format_timestamp, normalize_text
from utils.databus_client import get_client
from datetime import datetime

# Define FastMCP provider for vehicle-related topics

mcp = FastMCP("vehicles")

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
    name="vehicle_occupancy",
    description="Get current occupancy information for a specific vehicle by its ID.",
    tags={"fleet", "vehicles", "read-only"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_vehicle_occupancy(
    vehicle_input: str,
    ctx: Context | None = None) -> dict:
    
    try: 
        client = get_client()
        
        # TODO: Normalize vehicle ID input (e.g., remove spaces, uppercase) and handle common variations
        vehicle_id = vehicle_input.strip()
        if ctx:
            await ctx.info(f"Fetching occupancy for vehicle ID: {vehicle_id}")
        
        feed = await client.get_feed("vehicle_positions")
        
        if not feed or "entity" not in feed:
            return {"error": "Vehicle positions feed not available"}
        
        for entity in feed["entity"]:
            vehicle_data = entity.get("vehicle", {})
            vehicle_info = vehicle_data.get("vehicle", {})
            
            if vehicle_info.get("license_plate") == vehicle_id:
                return {
                    "vehicle_id": vehicle_id,
                    "occupancy_status": vehicle_data.get("occupancy_status", "unknown"),
                    "occupancy_percentage": vehicle_data.get("occupancy_percentage", "unknown"),
                    "timestamp": format_timestamp(vehicle_data.get("timestamp", "unknown")),
                }
        return {
            "error": "Vehicle not found in positions feed",
            "vehicle_id": vehicle_id
        }
    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching vehicle occupancy: {str(e)}")
        return {"error": str(e), "vehicle_id": vehicle_id}



@mcp.tool(
    name="vehicle_position",
    description="Get the current position of a specific vehicle by its ID.",
    tags={"fleet", "vehicles", "real-time"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
) 
async def get_vehicle_position(
    vehicle_input: str,
    ctx: Context | None = None
) -> dict:
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
            if vehicle_info.get("license_plate") == vehicle_id:
                
                return {
                    "vehicle_id": vehicle_id,
                    "latitude": position.get("latitude", "unknown"),
                    "longitude": position.get("longitude", "unknown"),
                    "speed_km": position.get("speed", "unknown"),
                    "timestamp": format_timestamp(vehicle_data.get("timestamp"))
                }
        return {
            "error": "Vehicle not found in positions feed",
            "vehicle_id": vehicle_id
        }
    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching vehicle position: {str(e)}")
        return {"error": str(e), "vehicle_input": vehicle_input}
   
   
@mcp.tool(
    name="high_occupancy_vehicles",
    description="Get a list of vehicles that currently have high occupancy (e.g., over 80%).",
    tags={"fleet", "vehicles", "real-time"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_high_occupancy_vehicles(ctx: Context | None = None) -> dict:
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
                high_occupancy_vehicles.append({
                    "vehicle_id": vehicle_data.get("vehicle", {}).get("id", "unknown"),
                    "vehicle_license_plate": vehicle_data.get("vehicle", {}).get("license_plate", "unknown"),
                    "occupancy_percentage": occ_percent,
                    "timestamp": vehicle_data.get("timestamp", "unknown"),
                })
        
        return {
            "total_high_occupancy_vehicles": len(high_occupancy_vehicles),
            "high_occupancy_vehicles": high_occupancy_vehicles
            }
    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching high occupancy vehicles: {str(e)}")
        return {"error": str(e)}
    
@mcp.tool(
    name="vehicle_current_info",
    description="Get comprehensive current information about a specific vehicle by its ID, including static details and real-time status.",
    tags={"fleet", "vehicles", "comprehensive"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
) 
async def get_vehicle_current_info(
    vehicle_input: str,
    ctx: Context | None = None
) -> dict:
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
                        "occupancy_status": vehicle_data.get("occupancy_status") or "unknown",
                        "occupancy_percentage": vehicle_data.get("occupancy_percentage") or "unknown",
                        "timestamp": format_timestamp(vehicle_data.get("timestamp")) if vehicle_data.get("timestamp") else "unknown",
                        "current_status": vehicle_data.get("current_status") or "unknown",
                        "congestion_level": vehicle_data.get("congestion_level") or "unknown",
                    }
                    break
        #run info
        run_info = await client.get_api("run")
        run_status = "unassigned"
        assignment = None
        if run_info:
            for run in run_info:
                if run.get("vehicle") == vehicle_id and run.get("run_status") == "IN_PROGRESS":
                    run_status = run.get("run_status", "unknown")
                    assignment = {
                        "route_id": run.get("route_id", "unknown"),
                        "operator": run.get("operator", "unknown"),
                        "trip_id": run.get("trip_id", "unknown"),
                        "start_time": run.get("start_time", "unknown"),
                        "start_date": run.get("start_date", "unknown"),
                        "run_status": run.get("run_status", "unknown"),
                    }
                    
        # Merge static and realtime info
        # TODO: ADD OPERATOR INFO, ROUTE INFO, LAST STOP INFO, etc. by cross-referencing with other feeds and APIs
        result = {
            "vehicle_id": vehicle_id,
            "label": vehicle_static.get("label") or vehicle_realtime.get("label", "unknown"),
            "license_plate": vehicle_static.get("license_plate") or vehicle_id,
            "status": vehicle_static.get("status", "unknown"),  # status del vehículo (estático)
            "company": vehicle_static.get("company", "unknown"),
            "route_id": vehicle_static.get("route_id") or vehicle_realtime.get("route_id", "unknown"),
            "latitude": vehicle_realtime.get("latitude", "unknown"),
            "longitude": vehicle_realtime.get("longitude", "unknown"),
            "speed": vehicle_realtime.get("speed", "unknown"),
            "occupancy_status": vehicle_realtime.get("occupancy_status", "unknown"),
            "occupancy_percentage": vehicle_realtime.get("occupancy_percentage", "unknown"),
            "timestamp": vehicle_realtime.get("timestamp", "unknown"),
            "current_status": vehicle_realtime.get("current_status", "unknown"),
            "congestion_level": vehicle_realtime.get("congestion_level", "unknown"),
            "run_status": run_status,  # status del run (asignación)
            "assignment": assignment,
        }
        
        # Error handling if no data found
        if not static_found and not realtime_found:
            return {
                "error": "Vehicle not found in both static and realtime data",
                "vehicle_id": vehicle_id
            }
        elif not static_found:
            result["warning"] = "Vehicle not found in static data, only realtime info available"
        elif not realtime_found:
            result["warning"] = "Vehicle not found in realtime feed, only static info available"
        
        return {
                
            "vehicle_id": vehicle_id,
            "full_info": result
        }

        
    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching vehicle full info: {str(e)}")
        return {"error": str(e), "vehicle_input": vehicle_input}
    
@mcp.tool(
    name="vehicle_full_info",
    description="Get full current information about a specific vehicle, including static details, real-time status, and assignment/run info.",
    tags={"fleet", "vehicles", "comprehensive"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_vehicle_full_info(
    vehicle_input: str,
    ctx: Context | None = None
) -> dict:
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
        vehicle_extra = next((v for v in vehicles_list if v.get("license_plate") == vehicle_id), {})


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
                        "occupancy_status": vehicle_data.get("occupancy_status", "unknown"),
                        "occupancy_percentage": vehicle_data.get("occupancy_percentage", "unknown"),
                        "timestamp": format_timestamp(vehicle_data.get("timestamp")) if vehicle_data.get("timestamp") else "unknown",
                        "current_status": vehicle_data.get("current_status", "unknown"),
                        "congestion_level": vehicle_data.get("congestion_level", "unknown"),
                    }
                    realtime_found = True
                    break

        # Assignment/run info
        run_info = await client.get_api("run")
        assignment = None
        if run_info:
            for run in run_info:
                if run.get("vehicle") == vehicle_id and run.get("run_status") == "IN_PROGRESS":
                    assignment = {
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
            "label": vehicle_static.get("label") or vehicle_extra.get("label", "unknown"),
            "license_plate": vehicle_static.get("license_plate") or vehicle_id,
            "company": vehicle_static.get("company", "unknown"),
            "status": vehicle_static.get("status", vehicle_extra.get("status", "unknown")),
            "wheelchair_accessible": vehicle_extra.get("wheelchair_accessible", "unknown"),
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
            "occupancy_percentage": vehicle_realtime.get("occupancy_percentage", "unknown"),
            "timestamp": vehicle_realtime.get("timestamp", "unknown"),
            "current_status": vehicle_realtime.get("current_status", "unknown"),
            "congestion_level": vehicle_realtime.get("congestion_level", "unknown"),
            "assignment": assignment,
        }

        if not static_found and not realtime_found:
            return {
                "error": "Vehicle not found in both static and realtime data",
                "vehicle_id": vehicle_id
            }
        elif not static_found:
            result["warning"] = "Vehicle not found in static data, only realtime info available"
        elif not realtime_found:
            result["warning"] = "Vehicle not found in realtime feed, only static info available"

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
    vehicle_input: str,
    ctx: Context | None = None
) -> dict:
    try:
        client = get_client()
        if ctx:
            await ctx.info(f"Fetching current assignment for vehicle ID: {vehicle_input}")
            
        vehicle_input = vehicle_input.strip()
        run_info = await client.get_api("run")
        
        if run_info and not "error" in run_info:
            for run in run_info:
                if run.get("vehicle") == vehicle_input and run.get("run_status") == "IN_PROGRESS":
                    assigment = {
                        "route_id": run.get("route_id", "unknown"),
                        "start_time": run.get("start_time", "unknown"),
                        "start_date": run.get("start_date", "unknown"),
                        "operator_id": run.get("operator", "unknown"),
                        "vehicle_id": run.get("vehicle", "unknown"),
                        "trip_id": run.get("trip_id", "unknown"),
                    }
                    return {"vehicle_id": vehicle_input, "current_assignment": assigment}
            return {
                "message": "No active assignment found for vehicle",
                "vehicle_id": vehicle_input
            }
        return {
            "error": "Run information not available",
            "vehicle_id": vehicle_input
        }
    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching vehicle assignment: {str(e)}")
        return {"error": str(e), "vehicle_input": vehicle_input}
    
@mcp.tool(
    name="vehicle_is_active",
    description="Check if a specific vehicle is currently active (i.e., has a recent position update).",
    tags={"fleet", "vehicles", "status"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def is_vehicle_moving(
    vehicle_input: str,
    ctx: Context | None = None
) -> dict:
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
            
            if vehicle_info.get("id") == vehicle_id or vehicle_info.get("license_plate") == vehicle_id:
                return {
                    "vehicle_id": vehicle_id,
                    "vehicle_licese_plate": vehicle_info.get("license_plate", "unknown"),
                    "trip_id": vehicle_data.get("trip", {}).get("trip_id", "unknown"),
                    "current_status": vehicle_data.get("current_status", "unknown"),
                    "position": {
                        "latitude": vehicle_data.get("position", {}).get("latitude", "unknown"),
                        "longitude": vehicle_data.get("position", {}).get("longitude", "unknown"),
                    },
                    "last_position_timestamp": format_timestamp(vehicle_data.get("timestamp"))
                }
            break
            
        return {
            "vehicle_id": vehicle_id,
            "is_active": False,
            "message": "Vehicle not found in positions feed, assuming inactive"
        }
            
    except Exception as e:
        if ctx:
            await ctx.error(f"Error checking vehicle active status: {str(e)}")
        return {"error": str(e), "vehicle_input": vehicle_input
}
        
@mcp.tool(
    name="vehicle_operators_history",
    description="Get a list of operators that have been assigned to a specific vehicle over time.",
    tags={"fleet", "vehicles", "history"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_all_operators_id_by_vehicle(
    vehicle_input: str,
    ctx: Context | None = None
) -> dict:
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
                        assignments.append({
                            "operator": key[0],
                            "vehicle_license_plate": key[1],
                            "route_id": key[2],
                        })
                    
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
    vehicle_input: str,
    ctx: Context | None = None
) -> dict:
    try:
        client = get_client()
        if ctx:
            await ctx.info(f"Fetching last operator for vehicle ID: {vehicle_input}")
        
        run_info = await client.get_api("run")

        latest_datetime = None
        last_run = None
        
        if run_info and not "error" in run_info:
            #Search if IN_PROGRESS run exists for the vehicle
            
            for run in run_info:
                if run.get("vehicle") == vehicle_input and run.get("run_status") == "IN_PROGRESS":
                    if run.get("status") == "IN_PROGRESS":
                        last_run = run
            #If no IN_PROGRESS run, get the last completed run
            for run in run_info:
                if run.get("vehicle") == vehicle_input and run.get("run_status") == "COMPLETED":
                    start_date = run.get("start_date","")
                    start_time = run.get("start_time","")
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
                return {
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

@mcp.tool(
    name="all_vehicles",
    description="Get a list of all vehicles with basic information. (license plate, label, company)",
    tags={"fleet", "vehicles", "list"},
    annotations=ToolAnnotations(readOnlyHint=True),  
    meta={"version": "1.0"}, 
)
async def get_all_vehicles(ctx: Context | None = None) -> dict:
    try:
        client = get_client()
        if ctx:
            await ctx.info("Fetching all vehicles")
        
        vehicles = await client.get_api("vehicle")
        
        if "error" in vehicles:
            return {"error": "Error fetching vehicles data"}
        
        vehicles_cleaned = []
        for v in vehicles:
            vehicles_cleaned.append({
                "license_plate": v.get("license_plate", "unknown"),
                "label": v.get("label", "unknown"),
                "company": v.get("company", "unknown"),
            })
        if not vehicles_cleaned:
            return {"error": "No vehicles found"}
        
        return {
            "total_vehicles": len(vehicles_cleaned),
            "vehicles": vehicles_cleaned
        }
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
    route_input: str,
    ctx: Context | None = None
) -> dict:
    try:
        client = get_client()
        if ctx:
            await ctx.info(f"Fetching vehicles used for route ID: {route_input}")
            
        route_input = route_input.strip()
        run_info = await client.get_api("run")

        used_vehicles = []
        
        if not "error" in run_info and run_info:
            for run in run_info:
                if run.get("route_id") == route_input and run.get("run_status") == "COMPLETED":
                    used_vehicles.append({
                        "vehicle_id": run.get("vehicle", "unknown"),
                        "operator": run.get("operator", "unknown"),
                        "start_time": run.get("start_time", "unknown"),
                        "start_date": run.get("start_date", "unknown"),
                        "trip_id": run.get("trip_id", "unknown"),
                    })
                    
        return {"route_id": route_input, "used_vehicles": used_vehicles}
    except Exception as e:  
        if ctx:
            await ctx.error(f"Error fetching vehicles by route: {str(e)}")
        return {"error": str(e), "route_input": route_input}
    

if __name__ == "__main__":
    mcp.run()
