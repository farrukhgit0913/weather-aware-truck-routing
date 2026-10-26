export type SamplingIntervalMiles = 10 | 25 | 50

export type RiskLevel =
  | 'low'
  | 'moderate'
  | 'high'
  | 'severe'
  | 'no_travel'

export interface Coordinates {
  latitude: number
  longitude: number
}

export interface ResolvedLocation {
  label: string
  coordinates: Coordinates
}

export interface RoutePlanRequest {
  origin: string
  destination: string
  origin_coordinates?: Coordinates
  destination_coordinates?: Coordinates
  departure_time: string
  load_weight_lb: number
  sampling_interval_miles: SamplingIntervalMiles
}

export interface WeatherSnapshot {
  forecast_at: string
  temperature_f: number
  wind_speed_mph: number
  rain_rate_in_hr: number
  snow_rate_in_hr: number
  precipitation_probability: number
  summary: string
}

export interface RiskAssessment {
  level: RiskLevel
  score: 0 | 1 | 2 | 3 | 4
  reasons: string[]
}

export interface RouteCheckpoint {
  id: string
  label: string
  sequence: number
  distance_from_origin_miles: number
  eta: string
  coordinates: Coordinates
  weather: WeatherSnapshot
  risk: RiskAssessment
}

export interface RouteSummary {
  distance_miles: number
  duration_minutes: number
  no_travel_miles: number
  severe_miles: number
  high_risk_miles: number
  average_risk_score: number
}

export interface RouteOption {
  id: string
  name: string
  geometry: {
    type: 'LineString'
    coordinates: [longitude: number, latitude: number][]
  }
  summary: RouteSummary
  checkpoints: RouteCheckpoint[]
}

export interface RouteRecommendation {
  route_id: string
  reasons: string[]
  comparison_order: [
    'severe_miles',
    'high_risk_miles',
    'average_risk_score',
    'duration_minutes',
  ]
}

export interface ForecastCell {
  coordinates: Coordinates
  risk_level: RiskLevel
  intensity: number
  weather: WeatherSnapshot
}

export interface ForecastFrame {
  offset_hours: number
  valid_at: string
  cells: ForecastCell[]
}

export interface ForecastTimeline {
  start_at: string
  end_at: string
  frames: ForecastFrame[]
}

export interface RoutePlanResponse {
  request_id: string
  generated_at: string
  origin: ResolvedLocation
  destination: ResolvedLocation
  departure_time: string
  load_weight_lb: number
  sampling_interval_miles: SamplingIntervalMiles
  routes: [RouteOption, RouteOption, RouteOption]
  recommendation: RouteRecommendation
  forecast_timelines: Record<string, ForecastTimeline>
}
