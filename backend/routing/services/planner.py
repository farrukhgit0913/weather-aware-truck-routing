from dataclasses import dataclass
from datetime import timedelta
from uuid import uuid4

from django.conf import settings
from django.utils import timezone

from routing.domain.recommendation import (
    RouteRiskSummary,
    RouteSegment,
    recommend_route,
    summarize_route,
)
from routing.domain.risk import WeatherConditions, assess_checkpoint_risk
from routing.integrations.geocoding import GeocodedLocation, NominatimGeocoder
from routing.integrations.route_provider import OsrmRouteProvider, ProviderRoute
from routing.integrations.weather import LocationForecast, OpenMeteoWeatherProvider, WeatherSample
from routing.services.checkpoints import METERS_PER_MILE, RouteCheckpoint, sample_route


@dataclass(slots=True)
class PlannedRoute:
    provider_route: ProviderRoute
    checkpoints: tuple[RouteCheckpoint, ...]
    forecasts: tuple[LocationForecast, ...]
    payload: dict
    summary: RouteRiskSummary


class RoutePlanningService:
    def __init__(
        self,
        geocoder: NominatimGeocoder,
        route_provider: OsrmRouteProvider,
        weather_provider: OpenMeteoWeatherProvider,
    ) -> None:
        self.geocoder = geocoder
        self.route_provider = route_provider
        self.weather_provider = weather_provider

    @classmethod
    def from_settings(cls) -> 'RoutePlanningService':
        return cls(
            geocoder=NominatimGeocoder(
                settings.GEOCODING_API_URL,
                settings.GEOCODING_USER_AGENT,
                settings.PROVIDER_TIMEOUT_SECONDS,
                getattr(settings, 'GEOCODING_MIN_INTERVAL_SECONDS', 1.0),
                getattr(settings, 'GEOCODING_COUNTRY_CODES', 'us'),
            ),
            route_provider=OsrmRouteProvider(
                settings.ROUTING_API_URL,
                settings.PROVIDER_TIMEOUT_SECONDS,
            ),
            weather_provider=OpenMeteoWeatherProvider(
                settings.WEATHER_API_URL,
                settings.PROVIDER_TIMEOUT_SECONDS,
                settings.WEATHER_MAX_PARALLEL_REQUESTS,
                settings.WEATHER_FORECAST_DAYS,
            ),
        )

    def plan(self, request_data: dict) -> dict:
        origin = self._resolve_location(
            request_data['origin'],
            request_data.get('origin_coordinates'),
        )
        destination = self._resolve_location(
            request_data['destination'],
            request_data.get('destination_coordinates'),
        )
        provider_routes = self.route_provider.get_routes(origin, destination)

        sampled_routes = [
            sample_route(
                route,
                request_data['sampling_interval_miles'],
                request_data['departure_time'],
            )
            for route in provider_routes
        ]
        all_checkpoints = [checkpoint for route in sampled_routes for checkpoint in route]
        all_forecasts = self.weather_provider.get_forecasts(
            [(checkpoint.latitude, checkpoint.longitude) for checkpoint in all_checkpoints]
        )

        planned_routes: list[PlannedRoute] = []
        forecast_offset = 0
        for index, (provider_route, checkpoints) in enumerate(zip(provider_routes, sampled_routes), start=1):
            forecasts = all_forecasts[forecast_offset:forecast_offset + len(checkpoints)]
            forecast_offset += len(checkpoints)
            planned_routes.append(
                self._build_route(
                    index,
                    provider_route,
                    checkpoints,
                    forecasts,
                    request_data['load_weight_lb'],
                )
            )

        recommendation = recommend_route(route.summary for route in planned_routes)
        generated_at = timezone.now()
        return {
            'request_id': uuid4(),
            'generated_at': generated_at,
            'origin': self._location_payload(origin),
            'destination': self._location_payload(destination),
            'departure_time': request_data['departure_time'],
            'load_weight_lb': request_data['load_weight_lb'],
            'sampling_interval_miles': request_data['sampling_interval_miles'],
            'routes': [route.payload for route in planned_routes],
            'recommendation': {
                'route_id': recommendation.route_id,
                'reasons': [
                    f'{recommendation.severe_miles:.1f} severe-weather miles',
                    f'{recommendation.high_risk_miles:.1f} high-risk miles',
                    f'{recommendation.average_risk_score:.2f} average risk score',
                ],
                'comparison_order': [
                    'severe_miles', 'high_risk_miles',
                    'average_risk_score', 'duration_minutes',
                ],
            },
            'forecast_timelines': {
                route.summary.route_id: self._forecast_timeline(
                    route,
                    request_data['departure_time'],
                    request_data['load_weight_lb'],
                )
                for route in planned_routes
            },
        }

    def _build_route(
        self,
        index: int,
        provider_route: ProviderRoute,
        checkpoints: tuple[RouteCheckpoint, ...],
        forecasts: tuple[LocationForecast, ...],
        load_weight_lb: int,
    ) -> PlannedRoute:
        assessments = []
        checkpoint_payloads = []
        for checkpoint, forecast in zip(checkpoints, forecasts):
            weather = forecast.nearest(checkpoint.eta)
            assessment = assess_checkpoint_risk(self._conditions(weather), load_weight_lb)
            assessments.append(assessment)
            checkpoint_payloads.append({
                'id': f'route-{index}-checkpoint-{checkpoint.sequence}',
                'label': f'Checkpoint {checkpoint.sequence + 1}',
                'sequence': checkpoint.sequence,
                'distance_from_origin_miles': checkpoint.distance_from_origin_miles,
                'eta': checkpoint.eta,
                'coordinates': {'latitude': checkpoint.latitude, 'longitude': checkpoint.longitude},
                'weather': self._weather_payload(weather),
                'risk': self._risk_payload(assessment),
            })

        segments = [
            RouteSegment(
                checkpoints[position].distance_from_origin_miles - checkpoints[position - 1].distance_from_origin_miles,
                assessments[position].level,
            )
            for position in range(1, len(checkpoints))
        ]
        route_id = f'route-{index}'
        summary = summarize_route(
            route_id,
            max(1, round(provider_route.duration_seconds / 60)),
            segments,
        )
        payload = {
            'id': route_id,
            'name': f'Route {index}',
            'geometry': {
                'type': 'LineString',
                'coordinates': [list(point) for point in provider_route.coordinates],
            },
            'summary': {
                'distance_miles': provider_route.distance_meters / METERS_PER_MILE,
                'duration_minutes': summary.duration_minutes,
                'no_travel_miles': summary.no_travel_miles,
                'severe_miles': summary.severe_miles,
                'high_risk_miles': summary.high_risk_miles,
                'average_risk_score': summary.average_risk_score,
            },
            'checkpoints': checkpoint_payloads,
        }
        return PlannedRoute(provider_route, checkpoints, forecasts, payload, summary)

    def _forecast_timeline(
        self,
        route: PlannedRoute,
        departure_time,
        load_weight_lb: int,
    ) -> dict:
        frames = []
        for offset_hours in range(0, 49, 6):
            valid_at = departure_time + timedelta(hours=offset_hours)
            cells = []
            for checkpoint, forecast in zip(route.checkpoints, route.forecasts):
                weather = forecast.nearest(valid_at)
                assessment = assess_checkpoint_risk(self._conditions(weather), load_weight_lb)
                cells.append({
                    'coordinates': {
                        'latitude': checkpoint.latitude,
                        'longitude': checkpoint.longitude,
                    },
                    'risk_level': assessment.level.value,
                    'intensity': assessment.score / 4,
                    'weather': self._weather_payload(weather),
                })
            frames.append({'offset_hours': offset_hours, 'valid_at': valid_at, 'cells': cells})
        return {
            'start_at': departure_time,
            'end_at': departure_time + timedelta(hours=48),
            'frames': frames,
        }

    @staticmethod
    def _conditions(weather: WeatherSample) -> WeatherConditions:
        return WeatherConditions(
            wind_speed_mph=weather.wind_speed_mph,
            rain_rate_in_hr=weather.rain_rate_in_hr,
            snow_rate_in_hr=weather.snow_rate_in_hr,
        )

    @staticmethod
    def _weather_payload(weather: WeatherSample) -> dict:
        return {
            'forecast_at': weather.forecast_at,
            'temperature_f': weather.temperature_f,
            'wind_speed_mph': weather.wind_speed_mph,
            'rain_rate_in_hr': weather.rain_rate_in_hr,
            'snow_rate_in_hr': weather.snow_rate_in_hr,
            'precipitation_probability': weather.precipitation_probability,
            'summary': weather.summary,
        }

    @staticmethod
    def _risk_payload(assessment) -> dict:
        return {
            'level': assessment.level.value,
            'score': assessment.score,
            'reasons': list(assessment.reasons),
        }

    @staticmethod
    def _location_payload(location: GeocodedLocation) -> dict:
        return {
            'label': location.label,
            'coordinates': {'latitude': location.latitude, 'longitude': location.longitude},
        }

    def _resolve_location(self, label: str, coordinates: dict | None) -> GeocodedLocation:
        if coordinates is None:
            return self.geocoder.geocode(label)
        return GeocodedLocation(
            label=label,
            latitude=coordinates['latitude'],
            longitude=coordinates['longitude'],
        )
