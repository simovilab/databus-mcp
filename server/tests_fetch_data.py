
import asyncio
import httpx

API_ROOT = "http://localhost:8000/api/"

async def fetch_vehicles():
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(API_ROOT + "vehicle/")
        resp.raise_for_status()
        data = resp.json()
        return data

async def main():
    vehicles = await fetch_vehicles()
    print("total:", len(vehicles))
    print("primer item:", vehicles[0] if vehicles else None)

if __name__ == "__main__":
    asyncio.run(main())