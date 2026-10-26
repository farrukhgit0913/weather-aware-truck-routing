from dataclasses import dataclass
from enum import Enum


class RiskLevel(str, Enum):
    LOW = 'low'
    MODERATE = 'moderate'
    HIGH = 'high'
    SEVERE = 'severe'
    NO_TRAVEL = 'no_travel'

    @property
    def score(self) -> int:
        return {
            RiskLevel.LOW: 0,
            RiskLevel.MODERATE: 1,
            RiskLevel.HIGH: 2,
            RiskLevel.SEVERE: 3,
            RiskLevel.NO_TRAVEL: 4,
        }[self]


@dataclass(frozen=True, slots=True)
class WeatherConditions:
    wind_speed_mph: float
    rain_rate_in_hr: float
    snow_rate_in_hr: float

    def __post_init__(self) -> None:
        measurements = {
            'wind_speed_mph': self.wind_speed_mph,
            'rain_rate_in_hr': self.rain_rate_in_hr,
            'snow_rate_in_hr': self.snow_rate_in_hr,
        }
        for name, value in measurements.items():
            if value < 0:
                raise ValueError(f'{name} cannot be negative.')


@dataclass(frozen=True, slots=True)
class RiskAssessment:
    level: RiskLevel
    score: int
    reasons: tuple[str, ...]
    component_levels: dict[str, RiskLevel]


def classify_wind(speed_mph: float) -> RiskLevel:
    _validate_non_negative('speed_mph', speed_mph)
    if speed_mph >= 55:
        return RiskLevel.NO_TRAVEL
    if speed_mph >= 45:
        return RiskLevel.SEVERE
    if speed_mph >= 35:
        return RiskLevel.HIGH
    if speed_mph >= 25:
        return RiskLevel.MODERATE
    return RiskLevel.LOW


def classify_rain(rate_in_hr: float) -> RiskLevel:
    _validate_non_negative('rate_in_hr', rate_in_hr)
    if rate_in_hr > 1.00:
        return RiskLevel.NO_TRAVEL
    if rate_in_hr >= 0.50:
        return RiskLevel.SEVERE
    if rate_in_hr >= 0.25:
        return RiskLevel.HIGH
    if rate_in_hr >= 0.10:
        return RiskLevel.MODERATE
    return RiskLevel.LOW


def classify_snow(rate_in_hr: float) -> RiskLevel:
    _validate_non_negative('rate_in_hr', rate_in_hr)
    if rate_in_hr > 3.00:
        return RiskLevel.NO_TRAVEL
    if rate_in_hr >= 2.00:
        return RiskLevel.SEVERE
    if rate_in_hr >= 1.00:
        return RiskLevel.HIGH
    if rate_in_hr >= 0.50:
        return RiskLevel.MODERATE
    return RiskLevel.LOW


def assess_checkpoint_risk(
    conditions: WeatherConditions,
    load_weight_lb: int,
) -> RiskAssessment:
    if load_weight_lb <= 0:
        raise ValueError('load_weight_lb must be greater than zero.')

    component_levels = {
        'wind': classify_wind(conditions.wind_speed_mph),
        'rain': classify_rain(conditions.rain_rate_in_hr),
        'snow': classify_snow(conditions.snow_rate_in_hr),
    }
    reasons = [
        _component_reason('Wind', conditions.wind_speed_mph, 'mph', component_levels['wind']),
        _component_reason('Rain', conditions.rain_rate_in_hr, 'in/hr', component_levels['rain']),
        _component_reason('Snow', conditions.snow_rate_in_hr, 'in/hr', component_levels['snow']),
    ]

    load_adjusted_wind = _apply_load_rule(
        conditions.wind_speed_mph,
        load_weight_lb,
    )
    if load_adjusted_wind.score > component_levels['wind'].score:
        component_levels['wind'] = load_adjusted_wind
        reasons.append(
            _load_rule_reason(
                conditions.wind_speed_mph,
                load_weight_lb,
                load_adjusted_wind,
            )
        )

    overall_level = max(component_levels.values(), key=lambda level: level.score)
    return RiskAssessment(
        level=overall_level,
        score=overall_level.score,
        reasons=tuple(reasons),
        component_levels=component_levels,
    )


def _apply_load_rule(wind_speed_mph: float, load_weight_lb: int) -> RiskLevel:
    base_level = classify_wind(wind_speed_mph)
    if wind_speed_mph >= 55:
        return RiskLevel.NO_TRAVEL
    if wind_speed_mph >= 45 and load_weight_lb > 30_000:
        return RiskLevel.NO_TRAVEL
    if wind_speed_mph >= 35 and load_weight_lb > 40_000:
        return RiskLevel.SEVERE
    return base_level


def _component_reason(
    condition: str,
    value: float,
    unit: str,
    level: RiskLevel,
) -> str:
    return f'{condition} at {value:g} {unit} is {level.value.replace("_", " ")} risk.'


def _load_rule_reason(
    wind_speed_mph: float,
    load_weight_lb: int,
    level: RiskLevel,
) -> str:
    return (
        f'Wind at {wind_speed_mph:g} mph with a {load_weight_lb:,} lb load '
        f'raises risk to {level.value.replace("_", " ")}.'
    )


def _validate_non_negative(name: str, value: float) -> None:
    if value < 0:
        raise ValueError(f'{name} cannot be negative.')
