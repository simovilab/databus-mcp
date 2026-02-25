import pytest
from utils.databus_client import DatabusClient, get_client


@pytest.fixture
def client():
    return DatabusClient("http://localhost:8000/", timeout=10.0)


@pytest.mark.asyncio
async def test_get_api_vehicles(client):
    result = await client.get_api("vehicle")
    assert isinstance(result, list)
    assert len(result) > 0
    vehicle = result[0]
    assert "url" in vehicle
    assert "company" in vehicle
    assert "label" in vehicle
    assert "license_plate" in vehicle


@pytest.mark.asyncio
async def test_get_feed_vehicle_positions(client):
    result = await client.get_feed("realtime/vehicle_positions.json")
    assert isinstance(result, dict)
    assert "header" in result
    assert "entity" in result

    assert isinstance(result["entity"], list)
    if len(result["entity"]) > 0:
        entity = result["entity"][0]
        assert "id" in entity
        assert "vehicle" in entity
        assert "position" in entity["vehicle"]
        assert "latitude" in entity["vehicle"]["position"]
        assert "longitude" in entity["vehicle"]["position"]


@pytest.mark.asyncio
async def test_get_api_routes(client):
    result = await client.get_api("routes")
    assert isinstance(result, list)
    assert len(result) > 0

    route = result[0]
    assert "route_id" in route
    assert "route_short_name" in route
    assert "route_long_name" in route
    assert "route_type" in route


def test_singleton():
    client1 = get_client()
    client2 = get_client()
    assert client1 is client2  #
