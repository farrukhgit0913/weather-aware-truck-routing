from django.test import SimpleTestCase

from routing.domain.risk import (
    RiskLevel,
    WeatherConditions,
    assess_checkpoint_risk,
    classify_rain,
    classify_snow,
    classify_wind,
)


class WeatherThresholdTests(SimpleTestCase):
    def test_wind_boundaries(self):
        cases = (
            (24.9, RiskLevel.LOW),
            (25, RiskLevel.MODERATE),
            (35, RiskLevel.HIGH),
            (45, RiskLevel.SEVERE),
            (55, RiskLevel.NO_TRAVEL),
        )

        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(classify_wind(value), expected)

    def test_rain_boundaries(self):
        cases = (
            (0.09, RiskLevel.LOW),
            (0.10, RiskLevel.MODERATE),
            (0.25, RiskLevel.HIGH),
            (0.50, RiskLevel.SEVERE),
            (1.00, RiskLevel.SEVERE),
            (1.01, RiskLevel.NO_TRAVEL),
        )

        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(classify_rain(value), expected)

    def test_snow_boundaries(self):
        cases = (
            (0.49, RiskLevel.LOW),
            (0.50, RiskLevel.MODERATE),
            (1.00, RiskLevel.HIGH),
            (2.00, RiskLevel.SEVERE),
            (3.00, RiskLevel.SEVERE),
            (3.01, RiskLevel.NO_TRAVEL),
        )

        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(classify_snow(value), expected)

    def test_negative_measurement_is_rejected(self):
        with self.assertRaises(ValueError):
            WeatherConditions(-1, 0, 0)


class LoadRuleTests(SimpleTestCase):
    def test_wind_45_to_54_with_load_over_30000_is_no_travel(self):
        assessment = assess_checkpoint_risk(
            WeatherConditions(45, 0, 0),
            load_weight_lb=30_001,
        )

        self.assertEqual(assessment.level, RiskLevel.NO_TRAVEL)

    def test_wind_45_with_load_at_30000_remains_severe(self):
        assessment = assess_checkpoint_risk(
            WeatherConditions(45, 0, 0),
            load_weight_lb=30_000,
        )

        self.assertEqual(assessment.level, RiskLevel.SEVERE)

    def test_wind_35_to_44_with_load_over_40000_is_severe(self):
        assessment = assess_checkpoint_risk(
            WeatherConditions(35, 0, 0),
            load_weight_lb=40_001,
        )

        self.assertEqual(assessment.level, RiskLevel.SEVERE)

    def test_wind_35_with_load_at_40000_remains_high(self):
        assessment = assess_checkpoint_risk(
            WeatherConditions(35, 0, 0),
            load_weight_lb=40_000,
        )

        self.assertEqual(assessment.level, RiskLevel.HIGH)

    def test_highest_component_sets_overall_risk(self):
        assessment = assess_checkpoint_risk(
            WeatherConditions(20, 0.6, 0.6),
            load_weight_lb=20_000,
        )

        self.assertEqual(assessment.level, RiskLevel.SEVERE)
        self.assertEqual(assessment.score, 3)
