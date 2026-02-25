import asyncio

from utils.databus_client import get_client


async def explore_data():
    client = get_client()

    print("=" * 60)
    print("VEHÍCULOS")
    print("=" * 60)
    vehicles = await client.get_api("vehicle")
    print(f"Total: {len(vehicles)}")
    print("\nPrimer vehículo:")
    import json

    print(json.dumps(vehicles[0], indent=2))

    print("\n" + "=" * 60)
    print("RUTAS")
    print("=" * 60)
    routes = await client.get_api("routes")
    print(f"Total: {len(routes)}")
    print("\nPrimera ruta:")
    print(json.dumps(routes[0], indent=2))

    print("\n" + "=" * 60)
    print("FEED REALTIME - VEHICLE POSITIONS")
    print("=" * 60)
    feed = await client.get_feed("realtime/vehicle_positions.json")
    print(f"Header: {feed.get('header', {}).get('gtfs_realtime_version')}")
    print(f"Timestamp: {feed.get('header', {}).get('timestamp')}")
    print(f"Total entities: {len(feed.get('entity', []))}")
    if feed.get("entity"):
        print("\nPrimera entidad:")
        print(json.dumps(feed["entity"][0], indent=2))


if __name__ == "__main__":
    asyncio.run(explore_data())
