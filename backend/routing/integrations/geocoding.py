from dataclasses import dataclass
from time import monotonic, sleep

import requests

from routing.integrations.exceptions import ProviderError


@dataclass(frozen=True, slots=True)
class GeocodedLocation:
    label: str
    latitude: float
    longitude: float


class NominatimGeocoder:
    def __init__(
        self,
        base_url: str,
        user_agent: str,
        timeout_seconds: float,
        minimum_interval_seconds: float = 1,
        country_codes: str = 'us',
    ) -> None:
        self.base_url = base_url.rstrip('/')
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds
        self.minimum_interval_seconds = minimum_interval_seconds
        self.country_codes = country_codes
        self._last_request_at = 0.0

    def geocode(self, query: str) -> GeocodedLocation:
        wait_seconds = self.minimum_interval_seconds - (monotonic() - self._last_request_at)
        if wait_seconds > 0:
            sleep(wait_seconds)
        try:
            response = requests.get(
                f'{self.base_url}/search',
                params={
                    'q': query,
                    'format': 'jsonv2',
                    'limit': 1,
                    'countrycodes': self.country_codes,
                },
                headers={'User-Agent': self.user_agent},
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            results = response.json()
            self._last_request_at = monotonic()
        except (requests.RequestException, ValueError) as error:
            raise ProviderError(
                'geocoding_provider_error',
                'The location service is temporarily unavailable.',
            ) from error

        if not results:
            raise ProviderError(
                'location_not_found',
                f'No location could be found for "{query}".',
            )

        result = results[0]
        return GeocodedLocation(
            label=result['display_name'],
            latitude=float(result['lat']),
            longitude=float(result['lon']),
        )
