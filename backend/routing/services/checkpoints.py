from dataclasses import dataclass
from datetime import datetime, timedelta
from math import asin, cos, radians, sin, sqrt

from routing.integrations.route_provider import ProviderRoute


METERS_PER_MILE = 1609.344
EARTH_RADIUS_MILES = 3958.7613


@dataclass(frozen=True, slots=True)
class RouteCheckpoint:
    sequence: int
    longitude: float
    latitude: float
    distance_from_origin_miles: float
    eta: datetime


def sample_route(
    route: ProviderRoute,
    interval_miles: int,
    departure_time: datetime,
) -> tuple[RouteCheckpoint, ...]:
    if interval_miles <= 0:
        raise ValueError('interval_miles must be greater than zero.')

    geometry_distances = [0.0]
    for start, end in zip(route.coordinates, route.coordinates[1:]):
        geometry_distances.append(geometry_distances[-1] + _distance_miles(start, end))

    geometry_total = geometry_distances[-1]
    route_miles = route.distance_meters / METERS_PER_MILE
    route_targets = [0.0]
    next_target = float(interval_miles)
    while next_target < route_miles:
        route_targets.append(next_target)
        next_target += interval_miles
    route_targets.append(route_miles)

    checkpoints = []
    segment_index = 1
    for sequence, route_target in enumerate(route_targets):
        target = route_target / route_miles * geometry_total
        while geometry_distances[segment_index] < target:
            segment_index += 1
        start_distance = geometry_distances[segment_index - 1]
        end_distance = geometry_distances[segment_index]
        ratio = 0 if end_distance == start_distance else (target - start_distance) / (end_distance - start_distance)
        start = route.coordinates[segment_index - 1]
        end = route.coordinates[segment_index]
        longitude = start[0] + (end[0] - start[0]) * ratio
        latitude = start[1] + (end[1] - start[1]) * ratio
        progress = route_target / route_miles
        checkpoints.append(
            RouteCheckpoint(
                sequence=sequence,
                longitude=longitude,
                latitude=latitude,
                distance_from_origin_miles=route_target,
                eta=departure_time + timedelta(seconds=route.duration_seconds * progress),
            )
        )
    return tuple(checkpoints)


def _distance_miles(
    start: tuple[float, float],
    end: tuple[float, float],
) -> float:
    start_lon, start_lat = map(radians, start)
    end_lon, end_lat = map(radians, end)
    delta_lon = end_lon - start_lon
    delta_lat = end_lat - start_lat
    value = sin(delta_lat / 2) ** 2 + cos(start_lat) * cos(end_lat) * sin(delta_lon / 2) ** 2
    return 2 * EARTH_RADIUS_MILES * asin(sqrt(value))
