from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from routing.api.serializers import (
    LocationSearchQuerySerializer,
    LocationSuggestionSerializer,
    RoutePlanRequestSerializer,
    RoutePlanResponseSerializer,
)
from routing.integrations.exceptions import ProviderError
from routing.integrations.location_search import OpenMeteoLocationSearchProvider
from routing.services.planner import RoutePlanningService


class RoutePlanView(APIView):
    """Create a weather-aware comparison of three truck routes."""

    serializer_class = RoutePlanRequestSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = RoutePlanningService.from_settings().plan(serializer.validated_data)
        except ProviderError as error:
            return Response(
                {'error': {'code': error.code, 'message': error.message}},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        response_serializer = RoutePlanResponseSerializer(data=result)
        response_serializer.is_valid(raise_exception=True)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class LocationSearchView(APIView):
    """Return U.S. location suggestions for the trip form."""

    def get(self, request):
        query_serializer = LocationSearchQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        provider = OpenMeteoLocationSearchProvider(
            settings.LOCATION_SEARCH_API_URL,
            settings.PROVIDER_TIMEOUT_SECONDS,
        )
        try:
            suggestions = provider.search(
                query_serializer.validated_data['q'],
                country_code=settings.LOCATION_SEARCH_COUNTRY_CODE,
            )
        except ProviderError as error:
            return Response(
                {'error': {'code': error.code, 'message': error.message}},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({
            'results': LocationSuggestionSerializer(suggestions, many=True).data,
        })
