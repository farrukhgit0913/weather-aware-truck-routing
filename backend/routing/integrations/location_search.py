from dataclasses import dataclass

import requests

from routing.integrations.exceptions import ProviderError


@dataclass(frozen=True, slots=True)
class LocationSuggestion:
    id: str
    name: str
    region: str
    country: str
    country_code: str
    label: str
    latitude: float
    longitude: float


class OpenMeteoLocationSearchProvider:
    def __init__(self, base_url: str, timeout_seconds: float) -> None:
        self.base_url = base_url.rstrip('/')
        self.timeout_seconds = timeout_seconds

    def search(
        self,
        query: str,
        *,
        country_code: str = 'US',
        limit: int = 5,
    ) -> tuple[LocationSuggestion, ...]:
        try:
            response = requests.get(
                f'{self.base_url}/search',
                params={
                    'name': query,
                    'count': limit,
                    'language': 'en',
                    'format': 'json',
                    'countryCode': country_code,
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            results = response.json().get('results', [])
        except (requests.RequestException, AttributeError, ValueError) as error:
            raise ProviderError(
                'location_search_provider_error',
                'Location suggestions are temporarily unavailable.',
            ) from error

        return tuple(self._suggestion(result) for result in results)

    @staticmethod
    def _suggestion(result: dict) -> LocationSuggestion:
        name = str(result['name'])
        region = str(result.get('admin1', ''))
        country = str(result.get('country', ''))
        label_parts = [name]
        for part in (region, country):
            if part and part.casefold() not in {item.casefold() for item in label_parts}:
                label_parts.append(part)

        return LocationSuggestion(
            id=str(result['id']),
            name=name,
            region=region,
            country=country,
            country_code=str(result.get('country_code', '')),
            label=', '.join(label_parts),
            latitude=float(result['latitude']),
            longitude=float(result['longitude']),
        )
