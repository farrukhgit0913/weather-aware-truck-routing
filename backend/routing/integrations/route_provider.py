from dataclasses import dataclass
from math import cos, hypot, radians

import requests

from routing.integrations.exceptions import ProviderError
from routing.integrations.geocoding import GeocodedLocation


@dataclass(frozen=True, slots=True)
class ProviderRoute:
    distance_meters: float
    duration_seconds: float
    coordinates: tuple[tuple[float, float], ...]


class OsrmRouteProvider:
    def __init__(self, base_url: str, timeout_seconds: float) -> None:
        self.base_url = base_url.rstrip('/')
        self.timeout_seconds = timeout_seconds

    def get_routes(
        self,
        origin: GeocodedLocation,
        destination: GeocodedLocation,
    ) -> tuple[ProviderRoute, ...]:
        routes = list(self._request_routes((origin, destination), alternatives=3))

        if len(routes) < 3:
            for waypoint in self._detour_waypoints(origin, destination):
                try:
                    candidates = self._request_routes(
                        (origin, waypoint, destination),
                        alternatives=0,
                    )
                except ProviderError:
                    continue
                for candidate in candidates:
                    if self._is_distinct(candidate, routes):
                        routes.append(candidate)
                    if len(routes) == 3:
                        return tuple(routes)

        if len(routes) < 3:
            raise ProviderError(
                'insufficient_route_options',
                'The routing provider could not produce three distinct route options.',
            )
        return tuple(routes[:3])

    def _request_routes(
        self,
        locations: tuple[GeocodedLocation, ...],
        alternatives: int,
    ) -> tuple[ProviderRoute, ...]:
        coordinate_path = ';'.join(
            f'{location.longitude},{location.latitude}' for location in locations
        )
        try:
            response = requests.get(
                f'{self.base_url}/route/v1/driving/{coordinate_path}',
                params={
                    'alternatives': alternatives,
                    'steps': 'false',
                    'geometries': 'geojson',
                    'overview': 'full',
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as error:
            raise ProviderError(
                'routing_provider_error',
                'The routing service is temporarily unavailable.',
            ) from error

        if payload.get('code') != 'Ok':
            raise ProviderError('route_not_found', 'No drivable route was found.')

        return tuple(self._parse_route(route) for route in payload.get('routes', [])[:3])

    @staticmethod
    def _detour_waypoints(
        origin: GeocodedLocation,
        destination: GeocodedLocation,
    ) -> tuple[GeocodedLocation, ...]:
        midpoint_latitude = (origin.latitude + destination.latitude) / 2
        midpoint_longitude = (origin.longitude + destination.longitude) / 2
        longitude_scale = max(cos(radians(midpoint_latitude)), 0.2)
        east_west = (destination.longitude - origin.longitude) * longitude_scale
        north_south = destination.latitude - origin.latitude
        direction_length = hypot(east_west, north_south)
        if direction_length == 0:
            raise ProviderError('route_not_found', 'Origin and destination resolve to the same place.')

        direct_miles = direction_length * 69
        base_offset_miles = min(max(direct_miles * 0.08, 15), 90)
        perpendicular_east = -north_south / direction_length
        perpendicular_north = east_west / direction_length
        waypoints = []
        for multiplier in (1, -1, 1.6, -1.6):
            offset_miles = base_offset_miles * multiplier
            waypoints.append(
                GeocodedLocation(
                    label='Alternative route corridor',
                    latitude=midpoint_latitude + perpendicular_north * offset_miles / 69,
                    longitude=(
                        midpoint_longitude
                        + perpendicular_east * offset_miles / (69 * longitude_scale)
                    ),
                )
            )
        return tuple(waypoints)

    @classmethod
    def _is_distinct(
        cls,
        candidate: ProviderRoute,
        existing_routes: list[ProviderRoute],
    ) -> bool:
        candidate_midpoint = candidate.coordinates[len(candidate.coordinates) // 2]
        return all(
            cls._coordinate_distance(candidate_midpoint, route.coordinates[len(route.coordinates) // 2])
            >= 5
            for route in existing_routes
        )

    @staticmethod
    def _coordinate_distance(
        first: tuple[float, float],
        second: tuple[float, float],
    ) -> float:
        mean_latitude = radians((first[1] + second[1]) / 2)
        east_west_miles = (first[0] - second[0]) * cos(mean_latitude) * 69
        north_south_miles = (first[1] - second[1]) * 69
        return hypot(east_west_miles, north_south_miles)

    @staticmethod
    def _parse_route(route: dict) -> ProviderRoute:
        coordinates = route.get('geometry', {}).get('coordinates', [])
        if len(coordinates) < 2:
            raise ProviderError('invalid_route_geometry', 'A route returned invalid geometry.')
        return ProviderRoute(
            distance_meters=float(route['distance']),
            duration_seconds=float(route['duration']),
            coordinates=tuple((float(point[0]), float(point[1])) for point in coordinates),
        )
