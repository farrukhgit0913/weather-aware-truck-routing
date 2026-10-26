from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from routing.integrations.location_search import OpenMeteoLocationSearchProvider


class OpenMeteoLocationSearchProviderTests(SimpleTestCase):
    @patch('routing.integrations.location_search.requests.get')
    def test_maps_provider_results_to_client_suggestions(self, get):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            'results': [{
                'id': 5128581,
                'name': 'New York',
                'latitude': 40.7128,
                'longitude': -74.006,
                'country_code': 'US',
                'country': 'United States',
                'admin1': 'New York',
            }],
        }
        get.return_value = response
        provider = OpenMeteoLocationSearchProvider('https://geocoding.example/v1', 10)

        suggestions = provider.search('New York', country_code='US')

        self.assertEqual(suggestions[0].label, 'New York, United States')
        self.assertEqual(suggestions[0].latitude, 40.7128)
        self.assertEqual(get.call_args.kwargs['params']['countryCode'], 'US')
