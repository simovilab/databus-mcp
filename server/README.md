# Databus MCP Server

## Overview

This document defines the logical domain structure of the **Databus MCP Server**.

The server is organized into operational domains (topics).  
Each topic groups MCP tools designed for administrative and operational intelligence.

Databus MCP is built primarily for:

- Transport operators  
- Regulatory institutions  
- Public transport management teams  
- Intelligent monitoring systems  

It focuses on operational visibility, performance analysis, and fleet supervision.

---

## Setup Notes

### Databus configuration
- MCP tools are implemented based on the models up to commit `bb5e4e537005dbdc35b70ca33990205d26d00dd1` in the [Databus repository](https://github.com/simovilab/databus).
- Inspect with `git show bb5e4e537005dbdc35b70ca33990205d26d00dd1`.

- Generate the .env file as described in [databus/HOWTO.md](https://github.com/simovilab/databus/blob/main/HOWTO.md).

- The compose file [compose.dev.yml](https://github.com/simovilab/databus/blob/main/compose.dev.yml) needs adjustments; a working reference is [databus_config/compose.dev.yml](databus_config/compose.dev.yml).

- Run the dev stack on databus root: 

```bash
./scripts/dev.sh
```

#### API Endpoints

The API root is available at http://localhost:8000/api/ and returns the list of resources.

Example response:

```json
{
	"company": "http://localhost:8000/api/company/",
	"operator": "http://localhost:8000/api/operator/",
	"data-provider": "http://localhost:8000/api/data-provider/",
	"vehicle": "http://localhost:8000/api/vehicle/",
	"equipment": "http://localhost:8000/api/equipment/",
	"equipment-log": "http://localhost:8000/api/equipment-log/",
	"run": "http://localhost:8000/api/run/",
	"position": "http://localhost:8000/api/position/",
	"progression": "http://localhost:8000/api/progression/",
	"occupancy": "http://localhost:8000/api/occupancy/",
	"agency": "http://localhost:8000/api/agency/",
	"stops": "http://localhost:8000/api/stops/",
	"geo-stops": "http://localhost:8000/api/geo-stops/",
	"shapes": "http://localhost:8000/api/shapes/",
	"geo-shapes": "http://localhost:8000/api/geo-shapes/",
	"routes": "http://localhost:8000/api/routes/",
	"calendars": "http://localhost:8000/api/calendars/",
	"calendar-dates": "http://localhost:8000/api/calendar-dates/",
	"trips": "http://localhost:8000/api/trips/",
	"stop-times": "http://localhost:8000/api/stop-times/",
	"fare-attributes": "http://localhost:8000/api/fare-attributes/",
	"fare-rules": "http://localhost:8000/api/fare-rules/",
	"feed-info": "http://localhost:8000/api/feed-info/"
}
```

#### Sample Data Fixture

Some endpoints do not include sample data by default. To load the fixture:

1. Copy feed_sample_data.json into [databus/backend/feed/fixtures/](https://github.com/simovilab/databus/tree/main/backend/feed/fixtures).
2. From the repository root, run:

```bash
docker compose -f compose.dev.yml exec backend uv run python manage.py loaddata feed_sample_data.json
```

#### Realtime Feed Outputs

The publisher generates realtime feed files at:

| File | Name |
| --- | --- |
| feed/realtime/vehicle_positions.json | vehicle_json |
| feed/realtime/vehicle_positions.pb | vehicle_pb |
| feed/realtime/trip_updates.json | trip_updates_json |
| feed/realtime/trip_updates.pb | trip_updates_pb |

For realtime data simulation, see [scripts/README.md](https://github.com/simovilab/databus/blob/main/scripts/README.md).

--- 
## Vehicles

Provides real-time and structural visibility over the vehicle fleet.

### Tools

| Tool Name | Description | Implemented |
|------------|------------|------------|
| `vehicles_list_by_company` | Returns the full fleet inventory for a specific company. | No |
| `vehicles_list_active` | Lists vehicles currently operating or reporting data. | No |
| `vehicles_list_without_signal` | Identifies vehicles that have not reported data within a defined period. | No |
| `vehicles_get_status` | Returns the current operational status of a specific vehicle. | No |
| `vehicles_get_last_position` | Provides the latest reported geographic position and telemetry data. | No |
| `vehicles_list_expected_not_operating` | Detects vehicles scheduled to operate but currently inactive. | No |


**Example question**
- What vehicles are registered under each company?
- Which vehicles are currently active?

**See implementation:** [server/topics/vehicles.py](topics/vehicles.py)

---

## Operations

Provides insights into service performance and delays.

### Tools

| Tool Name | Description | Implemented |
|------------|------------|------------|
| `operations_list_routes_by_company` | Lists all routes operated by a specific company. | No |
| `operations_list_trips_by_route` | Returns trips associated with a specific route. | No |
| `operations_list_trips_in_progress` | Identifies trips currently running. | No |
| `operations_list_vehicles_by_route` | Shows vehicles assigned to a route. | No |
| `operations_get_average_duration_by_route` | Calculates the average real trip duration per route. | No |
| `operations_compare_real_vs_estimated_duration` | Compares actual vs scheduled trip duration. | No |
| `operations_compare_start_time_variance` | Evaluates deviations from scheduled departure times. | No |
| `operations_identify_high_delay_routes` | Identifies routes with the highest average delays. | No |

---

**Example question**
- What routes does each company operate?
- Which trips are currently in progress on a specific route?
- Which vehicles are assigned to a given route?
- Which routes have the highest average delays?
---

**See implementation:** [server/topics/operations.py](topics/operations.py)

## Demand

Enables demand planning and capacity management.

### Tools


| Tool Name | Description | Implemented |
|------------|------------|------------|
| `demand_estimate_peak_time_ranges` | Identifies high-demand time ranges. | No |
| `demand_get_average_occupancy_by_route` | Calculates average occupancy levels per route. | No |
| `demand_identify_peak_hours_by_route` | Determines peak operating hours for each route. | No |
| `demand_get_occupancy_by_time_range` | Returns occupancy levels segmented by time window. | No |
| `demand_compare_usage_vs_capacity` | Evaluates actual usage against vehicle capacity. | No |
| `demand_list_highest_demand_stops` | Identifies stops with the highest passenger activity. | No |

**Example question**
- What is the average occupancy of vehicles per route?
- What are the peak hours for each route?
- How does actual vehicle usage compare to its capacity?
- Which stops have the highest passenger activity?

**See implementation:** [server/topics/demand.py](topics/demand.py)
---

## Alerts

Centralizes service alerts and operational events.

### Tools

| Tool Name | Description | Implemented |
|------------|------------|------------|
| `alerts_list_active` | Lists currently active alerts. | No |
| `alerts_list_by_route` | Filters alerts by route. | No |
| `alerts_summarize_recent` | Provides a consolidated summary of recent alerts. | No |
| `alerts_list_incidents_by_company` | Aggregates incidents by operator. | No |
| `alerts_identify_high_incident_routes` | Identifies routes with the highest number of incidents. | No |

**Example question**
- Which alerts are currently active?
- What is the summary of recent alerts?
- Which companies have the most incidents?
- Which routes are associated with the most incidents?

**See implementation:** [server/topics/alerts.py](topics/alerts.py)

---

## Network

Provides structural visibility over stops and route coverage.

### Tools

| Tool Name | Description | Implemented |
|------------|------------|------------|
| `network_list_stops_by_route` | Lists all stops associated with a route. | No |
| `network_list_routes_by_stop` | Identifies all routes passing through a stop. | No |


**Example question**
- What stops are included in a specific route?
- Which routes pass through a specific stop?
- How is the network structured across the city?

---