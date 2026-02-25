from urllib.parse import urlparse

from . import mcp
from fastmcp import Context
from mcp.types import ToolAnnotations
from utils.databus_client import get_client
from utils.common import normalize_text


@mcp.tool(
    name="companies_list",
    description="Get a list of all companies with their codes and names.",
    tags={"operations", "companies", "read-only"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_all_companies(ctx: Context | None = None) -> dict:
    """Get a list of all companies with their codes and names.

    arguments:
        - ctx: Optional context for logging and additional information during execution.

    returns:
        - A dictionary containing the total number of companies and a list of companies with their codes and names.
        - If an error occurs, an error message is included in the response.
    """
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
            companies_cleaned.append({"code": code, "name": c["name"]})
        return {
            "total_companies": len(companies_cleaned),
            "companies": companies_cleaned,
        }
    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching companies: {str(e)}")
        return {"error": str(e)}


@mcp.tool(
    name="resolve_company_code",
    description="Resolve a company input (code or name) to the internal company code.",
    tags={"operations", "companies", "read-only"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def resolve_company_code(company_input: str, ctx: Context | None = None) -> dict:
    try:
        """Resolve a company input (code or name) to the internal company code.

        arguments:
            - company_input: The company name or code to resolve.
            - ctx: Optional context for logging and additional information during execution.

        returns:
            - A dictionary containing the resolved company code and name.
            - If an error occurs or the company is not found, an error message is included in the response.
        """
        companies_data = await get_all_companies(ctx)

        if "error" in companies_data:
            return {
                "company_input": company_input,
                "error": f"Failed to fetch companies: {companies_data['error']}",
            }
        companies = companies_data.get("companies", [])

        normalized_input = normalize_text(company_input)
        matches = []

        for c in companies:
            code_normalized = normalize_text(c["code"])
            name_normalized = normalize_text(c["name"])
            if (
                normalized_input == code_normalized
                or normalized_input == name_normalized
            ):
                matches.append(c)

        if not matches:
            return {
                "company_input": company_input,
                "normalized_input": normalized_input,
                "error": "Company not found",
            }

        if len(matches) > 1:
            return {
                "company_input": company_input,
                "error": "Multiple companies found",
                "candidates": [
                    {"company_code": c["code"], "company_name": c["name"]}
                    for c in matches
                ],
            }

        # Exact single match
        match = matches[0]

        return {
            "company_input": company_input,
            "company_code": match["code"],
            "company_name": match["name"],
        }
    except Exception as e:
        if ctx:
            await ctx.error(f"Error resolving company code: {str(e)}")
        return {"error": str(e), "company_input": company_input}


@mcp.tool(
    name="get_company_fleet_run_status",
    description="Get the current run status of all vehicles for a specific company.",
    tags={"operations", "companies", "fleet status", "read-only"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_company_fleet_run_status(
    company_id: str, ctx: Context | None = None
) -> dict:
    """Get the current run status of all vehicles for a specific company.

    arguments:
        - company_id: The company ID to fetch fleet status for.
        - ctx: Optional context for logging and additional information during execution.

    returns:
        - A dictionary containing the company ID and a list of vehicles with their current run status and assignment details.
        - If an error occurs or no vehicles are found, an error message is included in the response.
    """
    try:
        client = get_client()
        if ctx:
            await ctx.info(f"Fetching fleet status for company_id: {company_id}")

        company_id = company_id.strip()
        company_id = await resolve_company_code(company_id, ctx)
        company_id = company_id.get("company_code", "unknown")
        run_info = await client.get_api(f"run")
        vehicles_info = await client.get_api(f"vehicle")

        company_vehicles = [
            v for v in vehicles_info if v.get("company", "unknown") == company_id
        ]
        fleet_status = []

        for v in company_vehicles:
            vehicle_id = v.get("license_plate", "unknown")
            vehicle_status = v.get("status", "unknown")
            assignment = None
            if run_info:
                for run in run_info:
                    if (
                        run.get("vehicle") == vehicle_id
                        and run.get("run_status") == "IN_PROGRESS"
                    ):
                        url = run.get("url", "unknown")
                        parsed = urlparse(url)
                        path_parts = parsed.path.rstrip("/").split("/")
                        run_id = path_parts[-1]
                        assignment = {
                            "run_id": run_id,
                            "operator_id": run.get("operator", "unknown"),
                            "route_id": run.get("route_id", "unknown"),
                            "trip_id": run.get("trip_id", "unknown"),
                            "start_time": run.get("start_time", "unknown"),
                            "start_date": run.get("start_date", "unknown"),
                            "run_status": run.get("run_status", "unknown"),
                        }
                        break
            fleet_status.append(
                {
                    "vehicle_id": vehicle_id,
                    "vehicle_status": vehicle_status,
                    "assignment": assignment,
                }
            )

        return {"company_id": company_id, "fleet_status": fleet_status}
    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching company fleet status: {str(e)}")
        return {"error": str(e), "company_id": company_id}
