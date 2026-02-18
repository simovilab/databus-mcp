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
    
    # Filter vehicles by company
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

if __name__ == "__main__":
    mcp.run()


    
