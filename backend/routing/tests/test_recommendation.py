from django.test import SimpleTestCase

from routing.domain.recommendation import (
    RouteRiskSummary,
    RouteSegment,
    rank_routes,
    recommend_route,
    summarize_route,
)
from routing.domain.risk import RiskLevel


def route_summary(
    route_id: str,
    *,
    no_travel: float = 0,
    severe: float = 0,
    high: float = 0,
    average: float = 1,
    duration: int = 500,
) -> RouteRiskSummary:
    return RouteRiskSummary(
        route_id=route_id,
        distance_miles=500,
        duration_minutes=duration,
        no_travel_miles=no_travel,
        severe_miles=severe,
        high_risk_miles=high,
        average_risk_score=average,
    )


class RouteSummaryTests(SimpleTestCase):
    def test_summarizes_weighted_route_risk(self):
        summary = summarize_route(
            'route-a',
            duration_minutes=120,
            segments=(
                RouteSegment(50, RiskLevel.LOW),
                RouteSegment(25, RiskLevel.HIGH),
                RouteSegment(15, RiskLevel.SEVERE),
                RouteSegment(10, RiskLevel.NO_TRAVEL),
            ),
        )

        self.assertEqual(summary.distance_miles, 100)
        self.assertEqual(summary.high_risk_miles, 25)
        self.assertEqual(summary.severe_miles, 15)
        self.assertEqual(summary.no_travel_miles, 10)
        self.assertAlmostEqual(summary.average_risk_score, 1.35)


class RouteRecommendationTests(SimpleTestCase):
    def test_no_travel_route_is_ranked_after_travelable_route(self):
        unsafe = route_summary('unsafe', no_travel=1, severe=0)
        safe = route_summary('safe', no_travel=0, severe=50)

        self.assertEqual(recommend_route((unsafe, safe)).route_id, 'safe')

    def test_uses_required_lexicographic_order(self):
        routes = (
            route_summary('fast', severe=5, high=0, average=0.2, duration=300),
            route_summary('balanced', severe=0, high=10, average=1.0, duration=400),
            route_summary('recommended', severe=0, high=5, average=1.5, duration=500),
        )

        ranked = rank_routes(routes)

        self.assertEqual(
            [route.route_id for route in ranked],
            ['recommended', 'balanced', 'fast'],
        )

    def test_average_risk_breaks_high_mileage_tie(self):
        higher_average = route_summary('higher', high=5, average=1.2, duration=300)
        lower_average = route_summary('lower', high=5, average=0.8, duration=500)

        self.assertEqual(
            recommend_route((higher_average, lower_average)).route_id,
            'lower',
        )

    def test_duration_is_final_business_tie_breaker(self):
        slow = route_summary('slow', duration=500)
        fast = route_summary('fast', duration=400)

        self.assertEqual(recommend_route((slow, fast)).route_id, 'fast')

    def test_duplicate_route_ids_are_rejected(self):
        with self.assertRaises(ValueError):
            rank_routes((route_summary('same'), route_summary('same')))
