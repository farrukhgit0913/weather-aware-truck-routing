from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone

import requests

from routing.integrations.exceptions import ProviderError


@dataclass(frozen=True, slots=True)
class WeatherSample:
    forecast_at: datetime
    temperature_f: float
    wind_speed_mph: float
    rain_rate_in_hr: float
    snow_rate_in_hr: float
    precipitation_probability: float
    weather_code: int

    @property
    def summary(self) -> str:
        if self.weather_code in {95, 96, 99}:
            return 'Thunderstorms'
        if self.weather_code in {71, 73, 75, 77, 85, 86}:
            return 'Snow'
        if self.weather_code in {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82}:
            return 'Rain'
        if self.weather_code in {45, 48}:
            return 'Fog'
        if self.weather_code in {1, 2, 3}:
            return 'Cloudy'
        return 'Clear'


@dataclass(frozen=True, slots=True)
class LocationForecast:
    latitude: float
    longitude: float
    samples: tuple[WeatherSample, ...]

    def nearest(self, target: datetime) -> WeatherSample:
        if not self.samples:
            raise ProviderError('forecast_unavailable', 'No forecast data was returned.')
        sample = min(
            self.samples,
            key=lambda item: abs((item.forecast_at - target).total_seconds()),
        )
        if abs((sample.forecast_at - target).total_seconds()) > 90 * 60:
            raise ProviderError(
                'forecast_out_of_range',
                'Weather is unavailable for the requested departure time.',
            )
        return sample


class OpenMeteoWeatherProvider:
    batch_size = 25

    def __init__(
        self,
        base_url: str,
        timeout_seconds: float,
        max_parallel_requests: int = 4,
        forecast_days: int = 7,
    ) -> None:
        if max_parallel_requests < 1:
            raise ValueError('max_parallel_requests must be at least 1.')
        if not 1 <= forecast_days <= 16:
            raise ValueError('forecast_days must be between 1 and 16.')
        self.base_url = base_url.rstrip('/')
        self.timeout_seconds = timeout_seconds
        self.max_parallel_requests = max_parallel_requests
        self.forecast_days = forecast_days

    def get_forecasts(
        self,
        coordinates: list[tuple[float, float]],
    ) -> tuple[LocationForecast, ...]:
        batches = [
            coordinates[start:start + self.batch_size]
            for start in range(0, len(coordinates), self.batch_size)
        ]
        if not batches:
            return ()
        if len(batches) == 1:
            return tuple(self._fetch_batch(batches[0]))

        with ThreadPoolExecutor(
            max_workers=min(self.max_parallel_requests, len(batches)),
        ) as executor:
            batch_forecasts = executor.map(self._fetch_batch, batches)
            return tuple(forecast for batch in batch_forecasts for forecast in batch)

    def _fetch_batch(
        self,
        coordinates: list[tuple[float, float]],
    ) -> list[LocationForecast]:
        latitudes = ','.join(str(latitude) for latitude, _ in coordinates)
        longitudes = ','.join(str(longitude) for _, longitude in coordinates)
        try:
            response = requests.get(
                f'{self.base_url}/v1/forecast',
                params={
                    'latitude': latitudes,
                    'longitude': longitudes,
                    'hourly': ','.join((
                        'temperature_2m',
                        'precipitation_probability',
                        'rain',
                        'snowfall',
                        'weather_code',
                        'wind_speed_10m',
                    )),
                    'temperature_unit': 'fahrenheit',
                    'wind_speed_unit': 'mph',
                    'precipitation_unit': 'inch',
                    'timezone': 'UTC',
                    'forecast_days': self.forecast_days,
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as error:
            raise ProviderError(
                'weather_provider_error',
                'The weather service is temporarily unavailable.',
            ) from error

        payloads = payload if isinstance(payload, list) else [payload]
        if len(payloads) != len(coordinates):
            raise ProviderError('invalid_weather_response', 'Weather data was incomplete.')
        return [self._parse_forecast(item) for item in payloads]

    @staticmethod
    def _parse_forecast(payload: dict) -> LocationForecast:
        hourly = payload.get('hourly', {})
        times = hourly.get('time', [])
        fields = (
            hourly.get('temperature_2m', []),
            hourly.get('wind_speed_10m', []),
            hourly.get('rain', []),
            hourly.get('snowfall', []),
            hourly.get('precipitation_probability', []),
            hourly.get('weather_code', []),
        )
        if not times or any(len(values) != len(times) for values in fields):
            raise ProviderError('invalid_weather_response', 'Weather data was incomplete.')

        samples = tuple(
            WeatherSample(
                forecast_at=_parse_utc_datetime(times[index]),
                temperature_f=float(fields[0][index] or 0),
                wind_speed_mph=float(fields[1][index] or 0),
                rain_rate_in_hr=float(fields[2][index] or 0),
                snow_rate_in_hr=float(fields[3][index] or 0),
                precipitation_probability=float(fields[4][index] or 0),
                weather_code=int(fields[5][index] or 0),
            )
            for index in range(len(times))
        )
        return LocationForecast(
            latitude=float(payload['latitude']),
            longitude=float(payload['longitude']),
            samples=samples,
        )


def _parse_utc_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed
