from fastmcp import FastMCP, Context
from mcp.types import ToolAnnotations
from topics.operations import resolve_company_code
from utils.common import  filter_by_field, normalize_text
from utils.databus_client import get_client


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
            "id": v["label"],
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
@mcp.tool(
    name="vehicle_info",
    description="Get detailed information about a specific vehicle by its ID.",
    tags={"fleet", "vehicles", "read-only"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_vehicle_info(
    vehicle_input: str,
    ctx: Context | None = None) -> dict:
    client = get_client()
    
    # TODO: Normalize vehicle ID input (e.g., remove spaces, uppercase) and handle common variations
    vehicle_id = vehicle_input.strip()
    if ctx:
        await ctx.info(f"Fetching information for vehicle ID: {vehicle_id}"
                       )
    vehicle = await client.get_api(f"vehicle/{vehicle_id}")
    
    if not vehicle:
        return {"error": "Vehicle not found",
                "vehicle_id": vehicle_id}
    
    # Normalize status
    vehicle.update({"status": vehicle.get("status") or "UNKNOWN"})
    
    # Agregar información no incluida directamente en vehicles, si no en run, operator, etc
    return vehicle
    
# Get vehicle occupancy
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
        
        if vehicle_info.get("id") == vehicle_id:
            return {
                "vehicle_id": vehicle_id,
                "occupancy_status": vehicle_data.get("occupancy_status", "unknown"),
                "occupancy_percentage": vehicle_data.get("occupancy_percentage", "unknown"),
                "timestamp": vehicle_data.get("timestamp", "unknown"),
            }
    return {
        "error": "Vehicle not found in positions feed",
        "vehicle_id": vehicle_id
    }




if __name__ == "__main__":
    mcp.run()


    
