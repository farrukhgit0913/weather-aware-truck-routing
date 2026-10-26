from dataclasses import dataclass
from typing import Iterable

from routing.domain.risk import RiskLevel


@dataclass(frozen=True, slots=True)
class RouteSegment:
    distance_miles: float
    risk_level: RiskLevel

    def __post_init__(self) -> None:
        if self.distance_miles < 0:
            raise ValueError('distance_miles cannot be negative.')


@dataclass(frozen=True, slots=True)
class RouteRiskSummary:
    route_id: str
    distance_miles: float
    duration_minutes: int
    no_travel_miles: float
    severe_miles: float
    high_risk_miles: float
    average_risk_score: float


def summarize_route(
    route_id: str,
    duration_minutes: int,
    segments: Iterable[RouteSegment],
) -> RouteRiskSummary:
    if not route_id.strip():
        raise ValueError('route_id is required.')
    if duration_minutes <= 0:
        raise ValueError('duration_minutes must be greater than zero.')

    route_segments = tuple(segments)
    if not route_segments:
        raise ValueError('At least one route segment is required.')

    distance_miles = sum(segment.distance_miles for segment in route_segments)
    if distance_miles <= 0:
        raise ValueError('Total route distance must be greater than zero.')

    def miles_at(level: RiskLevel) -> float:
        return sum(
            segment.distance_miles
            for segment in route_segments
            if segment.risk_level is level
        )

    weighted_risk = sum(
        segment.distance_miles * segment.risk_level.score
        for segment in route_segments
    )

    return RouteRiskSummary(
        route_id=route_id,
        distance_miles=distance_miles,
        duration_minutes=duration_minutes,
        no_travel_miles=miles_at(RiskLevel.NO_TRAVEL),
        severe_miles=miles_at(RiskLevel.SEVERE),
        high_risk_miles=miles_at(RiskLevel.HIGH),
        average_risk_score=weighted_risk / distance_miles,
    )


def rank_routes(routes: Iterable[RouteRiskSummary]) -> tuple[RouteRiskSummary, ...]:
    route_summaries = tuple(routes)
    if not route_summaries:
        raise ValueError('At least one route is required.')

    route_ids = [route.route_id for route in route_summaries]
    if len(route_ids) != len(set(route_ids)):
        raise ValueError('Route identifiers must be unique.')

    return tuple(sorted(route_summaries, key=_comparison_key))


def recommend_route(routes: Iterable[RouteRiskSummary]) -> RouteRiskSummary:
    return rank_routes(routes)[0]


def _comparison_key(route: RouteRiskSummary) -> tuple[float | int | str, ...]:
    # No-travel mileage is a safety gate. The remaining order follows the brief.
    return (
        route.no_travel_miles,
        route.severe_miles,
        route.high_risk_miles,
        route.average_risk_score,
        route.duration_minutes,
        route.route_id,
    )
