import { describe, expect, it } from 'vitest'

import type { LocationSuggestion } from '../api/searchLocations'
import type { TripFormValues } from '../tripPlanViewModels'
import {
  hasVerifiedLocations,
  selectLocationValue,
  swapTripLocations,
  updateLocationValue,
} from './tripLocations'

const values: TripFormValues = {
  origin: 'Chicago, IL',
  destination: 'Denver, CO',
  originCoordinates: { latitude: 41.8781, longitude: -87.6298 },
  destinationCoordinates: { latitude: 39.7392, longitude: -104.9903 },
  departureTime: '2026-10-27T08:00',
  loadWeightLb: 38_000,
  samplingIntervalMiles: 25,
}

const suggestion: LocationSuggestion = {
  id: '5128581',
  name: 'New York',
  region: 'New York',
  country: 'United States',
  country_code: 'US',
  label: 'New York, United States',
  latitude: 40.7128,
  longitude: -74.006,
}

describe('trip location state', () => {
  it('clears verification when a selected location is edited', () => {
    const updated = updateLocationValue(values, 'origin', 'New')
    expect(updated.origin).toBe('New')
    expect(updated.originCoordinates).toBeUndefined()
    expect(hasVerifiedLocations(updated)).toBe(false)
  })

  it('stores the selected label and exact coordinates', () => {
    const updated = selectLocationValue(values, 'origin', suggestion)
    expect(updated.origin).toBe('New York, United States')
    expect(updated.originCoordinates).toEqual({ latitude: 40.7128, longitude: -74.006 })
  })

  it('swaps labels and coordinates together', () => {
    const swapped = swapTripLocations(values)
    expect(swapped.origin).toBe('Denver, CO')
    expect(swapped.originCoordinates).toEqual(values.destinationCoordinates)
    expect(swapped.destinationCoordinates).toEqual(values.originCoordinates)
  })
})
