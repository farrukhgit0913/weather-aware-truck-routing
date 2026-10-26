from datetime import timedelta
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch

from routing.api.serializers import RoutePlanRequestSerializer
from routing.integrations.exceptions import ProviderError
from routing.integrations.location_search import LocationSuggestion


VALID_REQUEST = {
    'origin': 'Chicago, IL',
    'destination': 'Denver, CO',
    'departure_time': '2026-10-27T08:00:00Z',
    'load_weight_lb': 38_000,
    'sampling_interval_miles': 25,
}


class RoutePlanRequestSerializerTests(APITestCase):
    def test_accepts_valid_request(self):
        serializer = RoutePlanRequestSerializer(data=VALID_REQUEST)

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_rejects_unsupported_sampling_interval(self):
        serializer = RoutePlanRequestSerializer(
            data={**VALID_REQUEST, 'sampling_interval_miles': 20}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('sampling_interval_miles', serializer.errors)

    def test_rejects_matching_origin_and_destination(self):
        serializer = RoutePlanRequestSerializer(
            data={**VALID_REQUEST, 'destination': 'chicago, il'}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('destination', serializer.errors)

    def test_accepts_verified_location_coordinates(self):
        serializer = RoutePlanRequestSerializer(data={
            **VALID_REQUEST,
            'origin_coordinates': {'latitude': 41.8781, 'longitude': -87.6298},
            'destination_coordinates': {'latitude': 39.7392, 'longitude': -104.9903},
        })

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_rejects_only_one_set_of_location_coordinates(self):
        serializer = RoutePlanRequestSerializer(data={
            **VALID_REQUEST,
            'origin_coordinates': {'latitude': 41.8781, 'longitude': -87.6298},
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    def test_rejects_departure_beyond_the_supported_forecast_window(self):
        serializer = RoutePlanRequestSerializer(data={
            **VALID_REQUEST,
            'departure_time': timezone.now() + timedelta(days=5),
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn('departure_time', serializer.errors)

    def test_rejects_departure_in_the_past(self):
        serializer = RoutePlanRequestSerializer(data={
            **VALID_REQUEST,
            'departure_time': timezone.now() - timedelta(minutes=1),
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn('departure_time', serializer.errors)


class RoutePlanEndpointTests(APITestCase):
    @patch('routing.views.RoutePlanningService.plan')
    def test_returns_provider_error_after_validating_request(self, plan):
        plan.side_effect = ProviderError('routing_provider_error', 'Unavailable')
        response = self.client.post(
            reverse('routing:route-plan'),
            VALID_REQUEST,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertEqual(response.data['error']['code'], 'routing_provider_error')
        plan.assert_called_once()

    def test_returns_validation_errors_for_invalid_request(self):
        response = self.client.post(
            reverse('routing:route-plan'),
            {**VALID_REQUEST, 'load_weight_lb': 0},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('load_weight_lb', response.data)


class LocationSearchEndpointTests(APITestCase):
    @patch('routing.views.OpenMeteoLocationSearchProvider.search')
    def test_returns_location_suggestions(self, search):
        search.return_value = (
            LocationSuggestion(
                id='5128581',
                name='New York',
                region='New York',
                country='United States',
                country_code='US',
                label='New York, United States',
                latitude=40.7128,
                longitude=-74.006,
            ),
        )

        response = self.client.get(
            reverse('routing:location-search'),
            {'q': 'New York'},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['name'], 'New York')
        search.assert_called_once_with('New York', country_code='US')

    def test_rejects_a_one_character_query(self):
        response = self.client.get(reverse('routing:location-search'), {'q': 'N'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
