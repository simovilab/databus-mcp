from fastmcp import FastMCP, Context
from mcp.types import ToolAnnotations
from utils.common import format_timestamp
from utils.databus_client import get_client
from urllib.parse import urlparse

mcp = FastMCP("network")

#TODO: Complete 
@mcp.tool(
    name="route_overview",
    description="Get an overview of the current route status, including congestion levels and occupancy for all routes.",
    tags={"network", "overview", "read-only"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async  def get_route_overview(
    route_input: str,
    ctx: Context | None = None) -> dict:
    try:
        client = get_client()
        #TODO: Normalize route ID input (e.g., remove spaces, uppercase) and handle common variations
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
            
            vehicles.append({
                "congestion": congestion,
                "occupancy": occupancy,
                "occupancy_percentage": occupancy_percentage,
                "speed": speed
            })
        # TODO CHECK 
        if not route_found:
            return {"error": f"Route {route_id} not found in feed data"}
        if not vehicles:
            return {"error": f"No vehicles found for route {route_id}"}
            
            
        congestions = [ v["congestion"] for v in vehicles if v["congestion"] != "unknown"]
        occ_percents = [float(v["occupancy_percentage"]) for v in vehicles if v["occupancy_percentage"] != "unknown"]
        occupancies = [v["occupancy"] for v in vehicles if v["occupancy"] != "unknown"]
        speeds = [float(v["speed"]) for v in vehicles if v["speed"] != "unknown"]
            
        route_overview = {
            "route_id": route_id,
            "total_vehicles": len(vehicles),
            "main_congestion_level": max(set(congestions), key=congestions.count),                "main_occupancy_status": max(set(occupancies), key=occupancies.count),
            "average_occupancy_percentage": sum(occ_percents) / len(occ_percents) if occ_percents else 0,
            "average_speed_km": sum(speeds) / len(speeds) if speeds else 0,
        }
        return {"route_overview": route_overview}
    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching network overview: {str(e)}")
        return {"error": str(e)}
    
@mcp.tool(
    name="active_runs_by_route",
    description="Get a list of active runs for a specific route, including vehicle IDs, current locations, and occupancy status.",
    tags={"network", "active runs", "read-only"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_active_runs_by_route(
        route_input: str,
        ctx: Context | None = None
    ) -> dict:
        try:
            client = get_client()
            if ctx:
                await ctx.info(f"Resolving route input: {route_input}")
            
            route = route_input.strip()
            feed_trip  = await client.get_feed("trip_updates")
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
                    pos_license_plate = pos_vehicle.get("vehicle", {}).get("license_plate", "unknown")
                    if pos_license_plate == license_plate:
                        vehicle_position = pos_vehicle
                        break

                position = vehicle_position.get("position", {}) if vehicle_position else {}
                current_status = vehicle_position.get("current_status", "unknown") if vehicle_position else "unknown"
                current_stop_id = vehicle_position.get("stop_id", "unknown") if vehicle_position else "unknown"
                congestion_level = vehicle_position.get("congestion_level", "unknown") if vehicle_position else "unknown"
                occupancy_status = vehicle_position.get("occupancy_status", "unknown") if vehicle_position else "unknown"
                occupancy_percentage = vehicle_position.get("occupancy_percentage", "unknown") if vehicle_position else "unknown"
                speed = position.get("speed", "unknown")
                latitude = position.get("latitude", "unknown")
                longitude = position.get("longitude", "unknown")

                active_runs.append({
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
                    "occupancy_percentage": occupancy_percentage
                })
            
                return {
                    "total_active_runs": len(active_runs),
                    "active_runs": active_runs
                }
        except Exception as e:
            if ctx:
                await ctx.error(f"Error fetching active runs: {str(e)}")
            return {"error": str(e)}
        
async def get_complete_runs_by_day_and_operator(
    day_input: str,
    operator_input: str,
    ctx: Context | None = None
) -> dict:
    client = get_client()
    
    if ctx:
        await ctx.info(f"Fetching completed runs for day: {day_input} and operator: {operator_input}")
        
    return {
        "day": day_input,
        "operator": operator_input,
        "completed_runs": "Completed runs information not implemented yet"
    }
    
@mcp.tool(
    name="congestion_status_by_route",
    description="Get the current congestion status for a specific route, including congestion levels and average speed.",
    tags={"network", "congestion", "read-only"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)   
async def get_congestion_status_by_route(route_id: str, ctx: Context | None = None) -> dict:
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
            vehicles.append({
                "congestion": congestion,
                "speed": vehicle_data.get("position", {}).get("speed", "unknown")
            })
        if not route_found:
            return {"error": f"Route {route_id} not found in feed data"}
        if not vehicles:
            return {"error": f"No vehicles found for route {route_id}"} 
        congestions = [ v["congestion"] for v in vehicles if v["congestion"] != "unknown"]
        speeds = [float(v["speed"]) for v in vehicles if v["speed"] != "unknown"]
        
        route_congestion_status = {
            "route_id": route_id,
            "main_congestion_level": max(set(congestions), key=congestions.count) if congestions else "unknown",
            "average_speed_km": sum(speeds) / len(speeds) if speeds else 0,
        }
        return {"route_congestion_status": route_congestion_status}
    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching congestion status: {str(e)}")
        return {"error": str(e)}

@mcp.tool(
    name="completed_runs_by_day_and_vehicle",
    description="Get a list of completed runs for a specific day and vehicle, including run IDs, start times, and route information.",
    tags={"network", "completed runs", "read-only"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_complete_runs_by_day_and_vehicle(
    day_input: str,
    vehicle_input: str,
    ctx: Context | None = None
) -> dict:
    try:
        client = get_client()
        if ctx:
            await ctx.info(f"Fetching completed runs for day: {day_input} and vehicle: {vehicle_input}")
        run_info = await client.get_api(f"run")
        vehicle_input = vehicle_input.strip()
        day_input = day_input.strip()
        
        if not "error" in run_info and run_info:
            completed_runs = []
            for run in run_info:
                if run.get("vehicle") == vehicle_input and run.get("start_date") == day_input and run.get("run_status") == "COMPLETED":
                    
                    completed_runs.append({
                        #TODO: add run_id
                        "vehicle_id": run.get("vehicle", "unknown"),
                        "route_id": run.get("route_id", "unknown"),
                        "start_time": run.get("start_time", "unknown"),
                        "start_date": run.get("start_date", "unknown"),
                        "operator_id": run.get("operator", "unknown"),
                        "trip_id": run.get("trip_id", "unknown"),
                    })
            return {
                "day": day_input,
                "vehicle": vehicle_input,
                "completed_runs": completed_runs
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
    day_input: str,
    operator_input: str,
    ctx: Context | None = None
) -> dict:
    try:
        client = get_client()
        if ctx:
            await ctx.info(f"Fetching completed runs for day: {day_input} and operator: {operator_input}")
        run_info = await client.get_api(f"run")
        if not "error" in run_info and run_info:
            completed_runs = []
            for run in run_info:
                if run.get("operator") == operator_input and run.get("start_date") == day_input and run.get("run_status") == "COMPLETED":
                    
                    completed_runs.append({
                        #TODO: add run_id
                        "vehicle_id": run.get("vehicle", "unknown"),
                        "route_id": run.get("route_id", "unknown"),
                        "start_time": run.get("start_time", "unknown"),
                        "start_date": run.get("start_date", "unknown"),
                        "operator_id": run.get("operator", "unknown"),
                        "trip_id": run.get("trip_id", "unknown"),
                    })
            return {
                "day": day_input,
                "operator": operator_input,
                "completed_runs": completed_runs
            }
        
    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching completed runs: {str(e)}")
        return {"error": str(e), "operator_input": operator_input}
 
if __name__ == "__main__":
    mcp.run()