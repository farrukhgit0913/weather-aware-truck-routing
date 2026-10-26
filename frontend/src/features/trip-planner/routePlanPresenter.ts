import type {
  ForecastCell,
  RiskLevel,
  RouteCheckpoint,
  RouteOption,
  RoutePlanResponse,
} from './api/routePlan.types'
import type { ForecastFrameViewModel, RouteViewModel } from './tripPlanViewModels'

const routeColors = ['#18725c', '#c2762c', '#596875'] as const
const riskScore: Record<RiskLevel, number> = {
  low: 0,
  moderate: 1,
  high: 2,
  severe: 3,
  no_travel: 4,
}

interface PresentedRoutePlan {
  routes: RouteViewModel[]
  recommendedRouteId: string
}

export function presentRoutePlan(response: RoutePlanResponse): PresentedRoutePlan {
  return {
    routes: response.routes.map((route, index) => presentRoute(
      route,
      response.forecast_timelines[route.id].frames,
      index,
      route.id === response.recommendation.route_id,
    )),
    recommendedRouteId: response.recommendation.route_id,
  }
}

function presentRoute(
  route: RouteOption,
  forecastFrames: RoutePlanResponse['forecast_timelines'][string]['frames'],
  index: number,
  recommended: boolean,
): RouteViewModel {
  const lastCheckpoint = route.checkpoints.at(-1)

  return {
    id: route.id,
    name: route.name,
    via: 'Live routing alternative',
    distanceMiles: Math.round(route.summary.distance_miles),
    duration: formatDuration(route.summary.duration_minutes),
    arrival: lastCheckpoint ? formatTime(lastCheckpoint.eta) : '—',
    noTravelMiles: route.summary.no_travel_miles,
    severeMiles: route.summary.severe_miles,
    highRiskMiles: route.summary.high_risk_miles,
    averageRiskScore: route.summary.average_risk_score,
    coordinates: route.geometry.coordinates,
    color: routeColors[index] ?? routeColors[routeColors.length - 1],
    recommended,
    forecastFrames: forecastFrames.map((frame) => presentForecastFrame(
      frame,
      route.checkpoints,
    )),
    checkpoints: route.checkpoints.map((checkpoint) => {
      return {
        id: checkpoint.id,
        city: checkpoint.label,
        eta: formatTime(checkpoint.eta),
        distanceMiles: Math.round(checkpoint.distance_from_origin_miles),
        temperatureF: Math.round(checkpoint.weather.temperature_f),
        windSpeedMph: Math.round(checkpoint.weather.wind_speed_mph),
        condition: checkpoint.weather.summary,
        risk: checkpoint.risk.level,
        longitude: checkpoint.coordinates.longitude,
        latitude: checkpoint.coordinates.latitude,
      }
    }),
  }
}

function presentForecastFrame(
  frame: RoutePlanResponse['forecast_timelines'][string]['frames'][number],
  checkpoints: RouteCheckpoint[],
): ForecastFrameViewModel {
  const focusIndex = highestRiskCellIndex(frame.cells)
  const weatherCell = frame.cells[focusIndex]
  const focusCheckpoint = checkpoints[focusIndex]
  return {
    hour: frame.offset_hours,
    label: frame.offset_hours === 0 ? 'Depart' : `+${frame.offset_hours} hr`,
    focusLabel: `${focusCheckpoint.label} · Mile ${Math.round(focusCheckpoint.distance_from_origin_miles)}`,
    condition: weatherCell.weather.summary,
    temperatureF: Math.round(weatherCell.weather.temperature_f),
    windSpeedMph: Math.round(weatherCell.weather.wind_speed_mph),
    precipitationChance: Math.round(weatherCell.weather.precipitation_probability),
    risk: weatherCell.risk_level,
    cells: frame.cells.map((cell, index) => ({
      checkpointId: checkpoints[index].id,
      label: checkpoints[index].label,
      distanceMiles: checkpoints[index].distance_from_origin_miles,
      longitude: cell.coordinates.longitude,
      latitude: cell.coordinates.latitude,
      intensity: cell.intensity,
      risk: cell.risk_level,
    })),
  }
}

function highestRiskCellIndex(cells: ForecastCell[]) {
  return cells.reduce((highestIndex, cell, index) => (
    riskScore[cell.risk_level] > riskScore[cells[highestIndex].risk_level]
      ? index
      : highestIndex
  ), 0)
}

function formatDuration(minutes: number) {
  return `${Math.floor(minutes / 60)}h ${String(minutes % 60).padStart(2, '0')}m`
}

function formatTime(value: string) {
  return new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(value))
}
