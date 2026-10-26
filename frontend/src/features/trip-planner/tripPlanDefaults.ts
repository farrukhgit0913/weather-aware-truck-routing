import type { SamplingIntervalMiles } from './api/routePlan.types'
import type { TripFormValues } from './tripPlanViewModels'

export const MAX_DEPARTURE_DAYS_AHEAD = 4

export const defaultTrip: TripFormValues = {
  origin: 'Chicago, IL',
  destination: 'Denver, CO',
  originCoordinates: { latitude: 41.8781, longitude: -87.6298 },
  destinationCoordinates: { latitude: 39.7392, longitude: -104.9903 },
  departureTime: nextDepartureTime(),
  loadWeightLb: 38_000,
  samplingIntervalMiles: 25 as SamplingIntervalMiles,
}

export function departureDateTimeBounds(reference = new Date()) {
  const earliestDeparture = new Date(reference.getTime() + 5 * 60_000)
  const latestDeparture = new Date(reference)
  latestDeparture.setDate(latestDeparture.getDate() + MAX_DEPARTURE_DAYS_AHEAD)
  return {
    minimum: toDateTimeLocalValue(earliestDeparture),
    maximum: toDateTimeLocalValue(latestDeparture),
  }
}

function nextDepartureTime() {
  const departure = new Date(Date.now() + 60 * 60 * 1000)
  departure.setMinutes(0, 0, 0)
  return toDateTimeLocalValue(departure)
}

function toDateTimeLocalValue(value: Date) {
  const localTime = new Date(value.getTime() - value.getTimezoneOffset() * 60_000)
  return localTime.toISOString().slice(0, 16)
}
