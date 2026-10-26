from datetime import datetime, timezone

from django.test import SimpleTestCase

from routing.integrations.route_provider import ProviderRoute
from routing.services.checkpoints import METERS_PER_MILE, sample_route


class CheckpointSamplingTests(SimpleTestCase):
    def test_includes_endpoints_and_regular_intervals(self):
        route = ProviderRoute(
            distance_meters=100 * METERS_PER_MILE,
            duration_seconds=5 * 60 * 60,
            coordinates=((-90.0, 40.0), (-89.0, 40.0), (-88.0, 40.0)),
        )
        departure = datetime(2026, 10, 27, 8, tzinfo=timezone.utc)

        checkpoints = sample_route(route, 25, departure)

        self.assertEqual(checkpoints[0].distance_from_origin_miles, 0)
        self.assertAlmostEqual(checkpoints[-1].distance_from_origin_miles, 100)
        self.assertEqual(checkpoints[0].eta, departure)
        self.assertEqual(checkpoints[-1].eta, departure.replace(hour=13))
        self.assertGreaterEqual(len(checkpoints), 4)
