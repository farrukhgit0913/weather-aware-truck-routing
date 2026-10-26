from unittest.mock import patch

from django.test import SimpleTestCase

from routing.integrations.weather import LocationForecast, OpenMeteoWeatherProvider


class OpenMeteoWeatherProviderTests(SimpleTestCase):
    def test_large_coordinate_sets_are_batched_without_changing_order(self):
        provider = OpenMeteoWeatherProvider(
            'https://weather.example',
            timeout_seconds=5,
            max_parallel_requests=2,
        )
        provider.batch_size = 2
        coordinates = [
            (41.88, -87.63),
            (41.59, -93.62),
            (41.26, -95.94),
            (41.13, -100.77),
            (39.74, -104.99),
        ]

        def forecast_batch(batch):
            return [
                LocationForecast(latitude, longitude, ())
                for latitude, longitude in batch
            ]

        with patch.object(provider, '_fetch_batch', side_effect=forecast_batch) as fetch:
            forecasts = provider.get_forecasts(coordinates)

        self.assertEqual(fetch.call_count, 3)
        self.assertEqual(
            [(forecast.latitude, forecast.longitude) for forecast in forecasts],
            coordinates,
        )
