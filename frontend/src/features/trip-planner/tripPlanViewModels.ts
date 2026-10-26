import type { Coordinates, RiskLevel, SamplingIntervalMiles } from './api/routePlan.types'

export interface TripFormValues {
  origin: string
  destination: string
  originCoordinates?: Coordinates
  destinationCoordinates?: Coordinates
  departureTime: string
  loadWeightLb: number
  samplingIntervalMiles: SamplingIntervalMiles
}

export interface CheckpointViewModel {
  id: string
  city: string
  eta: string
  distanceMiles: number
  temperatureF: number
  windSpeedMph: number
  condition: string
  risk: RiskLevel
  longitude: number
  latitude: number
}

export interface RouteViewModel {
  id: string
  name: string
  via: string
  distanceMiles: number
  duration: string
  arrival: string
  noTravelMiles: number
  severeMiles: number
  highRiskMiles: number
  averageRiskScore: number
  coordinates: [longitude: number, latitude: number][]
  color: string
  checkpoints: CheckpointViewModel[]
  forecastFrames: ForecastFrameViewModel[]
  recommended?: boolean
}

export interface ForecastFrameViewModel {
  hour: number
  label: string
  focusLabel: string
  condition: string
  temperatureF: number
  windSpeedMph: number
  precipitationChance: number
  risk: RiskLevel
  cells: Array<{
    checkpointId: string
    label: string
    distanceMiles: number
    longitude: number
    latitude: number
    intensity: number
    risk: RiskLevel
  }>
}
