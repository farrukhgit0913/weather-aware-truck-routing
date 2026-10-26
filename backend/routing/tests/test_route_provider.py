from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from routing.integrations.geocoding import GeocodedLocation
from routing.integrations.route_provider import OsrmRouteProvider


def provider_response(coordinates, distance=1_000_000):
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        'code': 'Ok',
        'routes': [
            {
                'distance': distance,
                'duration': 50_000,
                'geometry': {'coordinates': coordinates},
            }
        ],
    }
    return response


class OsrmRouteProviderTests(SimpleTestCase):
    @patch('routing.integrations.route_provider.requests.get')
    def test_builds_waypoint_routes_when_alternatives_are_missing(self, get):
        get.side_effect = (
            provider_response([[-87.6, 41.8], [-96.0, 41.0], [-104.9, 39.7]]),
            provider_response([[-87.6, 41.8], [-96.0, 43.0], [-104.9, 39.7]], 1_050_000),
            provider_response([[-87.6, 41.8], [-96.0, 38.8], [-104.9, 39.7]], 1_080_000),
        )
        provider = OsrmRouteProvider('https://routing.example', 10)

        routes = provider.get_routes(
            GeocodedLocation('Chicago', 41.8, -87.6),
            GeocodedLocation('Denver', 39.7, -104.9),
        )

        self.assertEqual(len(routes), 3)
        self.assertEqual(get.call_count, 3)
        self.assertIn(';', get.call_args_list[1].args[0])
