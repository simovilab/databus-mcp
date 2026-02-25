from urllib.parse import urlparse

from . import mcp
from fastmcp import Context
from mcp.types import ToolAnnotations
from utils.databus_client import get_client
from topics.operations.companies import resolve_company_code


@mcp.tool(
    name="operators_list",
    description="Return codes (IDs) of all operators.",
    tags={"operations", "operators", "read-only"},
    annotations=ToolAnnotations(readOnlyHint=True),
    meta={"version": "1.0"},
)
async def get_all_operators_id(ctx: Context | None = None) -> dict:
    try:
        """Return codes (IDs) of all operators.

        arguments:
         - ctx: Optional context for logging and additional information during execution.

         returns:
         - A dictionary containing the total number of operators and a list of operator codes.
         - If an error occurs, an error message is included in the response."""
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
            operators_cleaned.append(
                {
                    "code": code,
                }
            )
        return {
            "total_operators": len(operators_cleaned),
            "operators": operators_cleaned,
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
async def get_operator_by_id(operator_input: str, ctx: Context | None = None) -> dict:
    """Get operator information by operator ID.

    arguments:
        - operator_input: The operator ID or code to fetch information for.
        - ctx: Optional context for logging and additional information during execution.

    returns:
        - A dictionary containing the operator code, company code, and phone number.
        - If an error occurs or the operator is not found, an error message is included in the response.
    """
    try:
        client = get_client()
        if ctx:
            await ctx.info(f"Resolving operator input: {operator_input}")

        operator_code = operator_input.strip()

        operator_data = await client.get_api(f"operator/{operator_code}")
        if "error" in operator_data or not operator_data:
            return {
                "operator_input": operator_input,
                "error": f"Operator details not found{operator_data}",
            }

        return {
            "operator_code": operator_code,
            "company_code": operator_data.get("company", "unknown"),
            "phone": operator_data.get("phone", "unknown"),
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
    vehicle_input: str, ctx: Context | None = None
) -> dict:
    """Get operator information by vehicle ID.

    arguments:
        - vehicle_input: The vehicle ID to fetch operator information for.
        - ctx: Optional context for logging and additional information during execution.

    returns:
        - A dictionary containing the vehicle ID and a list of operator IDs.
        - If an error occurs or the operator is not found, an error message is included in the response.
    """
    try:
        client = get_client()
        if ctx:
            await ctx.info(f"Fetching operator for vehicle_id: {vehicle_input}")

        vehicle_id = vehicle_input.strip()
        run_info = await client.get_api("run")

        if "error" in run_info or not run_info:
            return {
                "vehicle_id": vehicle_input,
                "error": f"Operator details not found for {vehicle_input}",
            }

        operators = set()
        for run in run_info:
            if run.get("vehicle", "") == vehicle_id:
                operator_id = run.get("operator", "unknown")
                operators.add(operator_id)

        if operators:
            return {"vehicle_id": vehicle_id, "operator_ids": list(operators)}
        else:
            return {
                "vehicle_id": vehicle_input,
                "error": "Operator not found for this vehicle",
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
    operator_input: str, ctx: Context | None = None
) -> dict:
    """Get vehicle information by operator ID.

    arguments:
        - operator_input: The operator ID to fetch vehicle information for.
        - ctx: Optional context for logging and additional information during execution.

    returns:
        - A dictionary containing the operator ID and a list of vehicle IDs.
        - If an error occurs or the vehicle is not found, an error message is included in the response.
    """
    try:
        client = get_client()
        if ctx:
            await ctx.info(
                f"Fetching vehicle information for operator_id: {operator_input}"
            )

        operator_id = operator_input.strip()
        run_info = await client.get_api("run")
        if "error" in run_info or not run_info:
            return {
                "operator_id": operator_input,
                "error": f"Vehicle details not found for {operator_input}",
            }

        vehicles = set()
        for run in run_info:
            if run.get("operator") == operator_id:
                vehicle = run.get("vehicle", "unknown")
                vehicles.add(vehicle)
        return {"operator_id": operator_id, "vehicle_ids": list(vehicles)}
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
    company_input: str, ctx: Context | None = None
) -> dict:
    """Get a list of operators for a specific company ID or name.

    arguments:
        - company_input: The company ID or name to fetch operator information for.
        - ctx: Optional context for logging and additional information during execution.

    returns:
        - A dictionary containing the company ID, company name, and a list of operator IDs.
        - If an error occurs or the company is not found, an error message is included in the response.
    """
    try:
        client = get_client()

        if ctx:
            await ctx.info(
                f"Fetching operator information for company_id: {company_input}"
            )

        company_input = company_input.strip()

        resolve_company_code_result = await resolve_company_code(company_input, ctx)

        companies_data = await client.get_api(
            f"company/{resolve_company_code_result.get('company_code', '')}"
        )
        company_code = resolve_company_code_result.get("company_code", "unknown")

        if not companies_data or companies_data.get(
            "name"
        ) != resolve_company_code_result.get("company_name"):
            return {
                "company_id": company_input,
                "error": f"Company details not found or company name mismatch for {company_input}",
            }

        operators_data = await get_all_operators_id(ctx)

        if "error" in operators_data or not operators_data:
            return {
                "company_id": company_input,
                "error": f"Operators details not found for {company_input}",
            }

        operator_ids = [op["code"] for op in operators_data.get("operators", [])]

        return {
            "company_id": company_code,
            "company_name": companies_data.get("name", "unknown"),
            "operators": operator_ids,
        }

    except Exception as e:
        if ctx:
            await ctx.error(f"Error fetching operator by company: {str(e)}")
        return {"error": str(e), "company_id": company_input}
