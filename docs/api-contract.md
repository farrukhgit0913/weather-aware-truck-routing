# Route-planning API contract

## Search verified locations

`GET /api/v1/locations/?q=chicago`

Returns U.S. city, state, and ZIP-code matches for the origin and destination
autocomplete. Each result includes a display label plus exact latitude and longitude.

```json
{
  "results": [
    {
      "id": "4887398",
      "name": "Chicago",
      "region": "Illinois",
      "country": "United States",
      "country_code": "US",
      "label": "Chicago, Illinois, United States",
      "latitude": 41.85003,
      "longitude": -87.65005
    }
  ]
}
```

## Create a route plan

`POST /api/v1/route-plans/`

### Request

```json
{
  "origin": "Chicago, IL",
  "destination": "Denver, CO",
  "origin_coordinates": { "latitude": 41.85003, "longitude": -87.65005 },
  "destination_coordinates": { "latitude": 39.73915, "longitude": -104.9847 },
  "departure_time": "2026-10-27T08:00:00Z",
  "load_weight_lb": 38000,
  "sampling_interval_miles": 25
}
```

Rules:

- Origin and destination are required and must be different.
- Verified origin and destination coordinates are optional, but must be supplied together.
  The UI supplies them after autocomplete selection to avoid ambiguous re-geocoding.
- Departure time is an ISO 8601 timestamp.
- Departure time must be between the current time and four days ahead. The backend
  requests seven forecast days, leaving enough coverage for long trips and the
  required 48-hour timeline.
- Load weight is a positive integer measured in pounds.
- Sampling interval must be `10`, `25`, or `50` miles.

### Successful response

The response contains a request identifier, resolved locations, exactly three route
options, the selected recommendation, and a 48-hour forecast timeline for every route.

Each route contains GeoJSON-compatible line coordinates, summary metrics, and ordered
checkpoints. Each checkpoint contains an ETA, weather measurements, a risk level, a
numeric risk score, and human-readable reasons.

`forecast_timelines` is keyed by route ID. This lets the map and timeline switch together
when the user selects another route without making another provider request.
The frontend renders these ordered cells as a solid-color, route-aligned risk corridor.
Colors change at sampled checkpoint regions; no interpolation invents weather between
provider samples.

Route summaries include No Travel, Severe, and High-risk mileage. No Travel mileage is
used as a safety gate before applying the documented recommendation order.

Risk levels are `low`, `moderate`, `high`, `severe`, and `no_travel`.

The recommendation comparison order is fixed:

1. Fewest severe miles
2. Fewest high-risk miles
3. Lowest average risk score
4. Shortest travel time

### Providers

- Nominatim resolves free-form locations.
- Open-Meteo Geocoding supplies U.S.-filtered autocomplete suggestions.
- OSRM produces full GeoJSON route geometry and alternatives.
- Open-Meteo supplies multi-point hourly forecasts in Fahrenheit, mph, and inches.

All provider URLs are configurable through backend environment variables.
Weather requests are sent in bounded parallel batches so 10-mile sampling remains
responsive without creating unbounded provider traffic.
When OSRM returns fewer than three native alternatives, the backend requests additional
drivable corridors through offset waypoints and removes duplicate route geometry.

### Error responses

- `400 Bad Request` for invalid input.
- `502 Bad Gateway` when a configured provider fails or cannot return the required data.
- Provider failures use an `error` object containing a stable `code` and a user-safe
  `message`.

