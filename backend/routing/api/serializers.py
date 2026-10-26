from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import serializers


RISK_LEVELS = ('low', 'moderate', 'high', 'severe', 'no_travel')
SAMPLING_INTERVALS = (10, 25, 50)


class CoordinatesSerializer(serializers.Serializer):
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)


class ResolvedLocationSerializer(serializers.Serializer):
    label = serializers.CharField(max_length=255)
    coordinates = CoordinatesSerializer()


class LocationSearchQuerySerializer(serializers.Serializer):
    q = serializers.CharField(min_length=2, max_length=120, trim_whitespace=True)


class LocationSuggestionSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=80)
    name = serializers.CharField(max_length=160)
    region = serializers.CharField(max_length=160, allow_blank=True)
    country = serializers.CharField(max_length=120, allow_blank=True)
    country_code = serializers.CharField(max_length=2, allow_blank=True)
    label = serializers.CharField(max_length=320)
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)


class WeatherSnapshotSerializer(serializers.Serializer):
    forecast_at = serializers.DateTimeField()
    temperature_f = serializers.FloatField()
    wind_speed_mph = serializers.FloatField(min_value=0)
    rain_rate_in_hr = serializers.FloatField(min_value=0)
    snow_rate_in_hr = serializers.FloatField(min_value=0)
    precipitation_probability = serializers.FloatField(min_value=0, max_value=100)
    summary = serializers.CharField(max_length=160)


class RiskAssessmentSerializer(serializers.Serializer):
    level = serializers.ChoiceField(choices=RISK_LEVELS)
    score = serializers.IntegerField(min_value=0, max_value=4)
    reasons = serializers.ListField(
        child=serializers.CharField(max_length=160),
        allow_empty=False,
    )


class CheckpointSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=80)
    label = serializers.CharField(max_length=120)
    sequence = serializers.IntegerField(min_value=0)
    distance_from_origin_miles = serializers.FloatField(min_value=0)
    eta = serializers.DateTimeField()
    coordinates = CoordinatesSerializer()
    weather = WeatherSnapshotSerializer()
    risk = RiskAssessmentSerializer()


class RouteGeometrySerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=('LineString',))
    coordinates = serializers.ListField(
        child=serializers.ListField(
            child=serializers.FloatField(),
            min_length=2,
            max_length=2,
        ),
        min_length=2,
    )

    def validate_coordinates(self, value):
        for longitude, latitude in value:
            if not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
                raise serializers.ValidationError(
                    'Each coordinate must be a valid [longitude, latitude] pair.'
                )
        return value


class RouteSummarySerializer(serializers.Serializer):
    distance_miles = serializers.FloatField(min_value=0)
    duration_minutes = serializers.IntegerField(min_value=0)
    no_travel_miles = serializers.FloatField(min_value=0)
    severe_miles = serializers.FloatField(min_value=0)
    high_risk_miles = serializers.FloatField(min_value=0)
    average_risk_score = serializers.FloatField(min_value=0, max_value=4)


class RouteOptionSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=80)
    name = serializers.CharField(max_length=120)
    geometry = RouteGeometrySerializer()
    summary = RouteSummarySerializer()
    checkpoints = CheckpointSerializer(many=True, allow_empty=False)


class RecommendationSerializer(serializers.Serializer):
    route_id = serializers.CharField(max_length=80)
    reasons = serializers.ListField(
        child=serializers.CharField(max_length=240),
        allow_empty=False,
    )
    comparison_order = serializers.ListField(
        child=serializers.ChoiceField(
            choices=(
                'severe_miles',
                'high_risk_miles',
                'average_risk_score',
                'duration_minutes',
            )
        ),
        min_length=4,
        max_length=4,
    )


class ForecastCellSerializer(serializers.Serializer):
    coordinates = CoordinatesSerializer()
    risk_level = serializers.ChoiceField(choices=RISK_LEVELS)
    intensity = serializers.FloatField(min_value=0, max_value=1)
    weather = WeatherSnapshotSerializer()


class ForecastFrameSerializer(serializers.Serializer):
    offset_hours = serializers.IntegerField(min_value=0, max_value=48)
    valid_at = serializers.DateTimeField()
    cells = ForecastCellSerializer(many=True)


class ForecastTimelineSerializer(serializers.Serializer):
    start_at = serializers.DateTimeField()
    end_at = serializers.DateTimeField()
    frames = ForecastFrameSerializer(many=True, allow_empty=False)


class RoutePlanRequestSerializer(serializers.Serializer):
    origin = serializers.CharField(max_length=255, trim_whitespace=True)
    destination = serializers.CharField(max_length=255, trim_whitespace=True)
    origin_coordinates = CoordinatesSerializer(required=False)
    destination_coordinates = CoordinatesSerializer(required=False)
    departure_time = serializers.DateTimeField()
    load_weight_lb = serializers.IntegerField(min_value=1)
    sampling_interval_miles = serializers.ChoiceField(choices=SAMPLING_INTERVALS)

    def validate(self, attributes):
        if attributes['origin'].casefold() == attributes['destination'].casefold():
            raise serializers.ValidationError(
                {'destination': 'Destination must be different from origin.'}
            )
        has_origin_coordinates = 'origin_coordinates' in attributes
        has_destination_coordinates = 'destination_coordinates' in attributes
        if has_origin_coordinates != has_destination_coordinates:
            raise serializers.ValidationError(
                'Origin and destination coordinates must be provided together.'
            )
        now = timezone.now()
        departure_time = attributes['departure_time']
        if departure_time < now:
            raise serializers.ValidationError({
                'departure_time': 'Departure time cannot be in the past.',
            })
        latest_departure = now + timedelta(days=settings.MAX_DEPARTURE_DAYS_AHEAD)
        if departure_time > latest_departure:
            raise serializers.ValidationError({
                'departure_time': (
                    'Weather forecasts are available only for departures within '
                    f'the next {settings.MAX_DEPARTURE_DAYS_AHEAD} days.'
                ),
            })
        return attributes


class RoutePlanResponseSerializer(serializers.Serializer):
    request_id = serializers.UUIDField()
    generated_at = serializers.DateTimeField()
    origin = ResolvedLocationSerializer()
    destination = ResolvedLocationSerializer()
    departure_time = serializers.DateTimeField()
    load_weight_lb = serializers.IntegerField(min_value=1)
    sampling_interval_miles = serializers.ChoiceField(choices=SAMPLING_INTERVALS)
    routes = RouteOptionSerializer(many=True, min_length=3, max_length=3)
    recommendation = RecommendationSerializer()
    forecast_timelines = serializers.DictField(
        child=ForecastTimelineSerializer(),
        allow_empty=False,
    )
