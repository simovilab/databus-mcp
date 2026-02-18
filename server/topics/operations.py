from fastmcp import FastMCP, Context
from mcp.types import ToolAnnotations
from utils.common import  filter_by_field, normalize_text
from utils.databus_client import get_client
from urllib.parse import urlparse


mcp = FastMCP("operations")


@mcp.tool(
    name="companies_list",
    description="Get a list of companies.",
    tags={"operations", "companies", "read-only"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_companies_list(
    ctx: Context | None = None
) -> dict:
    
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

    
    companies_data = await get_companies_list(ctx)
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
    

@mcp.tool(
    name="vehicle_info",
    description="Get detailed information about a specific vehicle by its ID.",
    tags={"fleet", "vehicles", "read-only"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_vehicle_info(vehicle_id: str, ctx: Context | None = None) -> dict:
    client = get_client()
    
    vehicle_id = vehicle_id.strip().upper()
    if ctx:
        await ctx.info(f"Fetching information for vehicle ID: {vehicle_id}"
                       )
    vehicle = await client.get_api(f"vehicle/{vehicle_id}")
    
    if not vehicle:
        return {"error": "Vehicle not found",
                "vehicle_id": vehicle_id}
    
    # Normalize status
    vehicle.update({"status": vehicle.get("status") or "UNKNOWN"})
    
    return vehicle
    
