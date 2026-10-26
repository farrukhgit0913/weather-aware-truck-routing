import type { LocationSuggestion } from '../api/searchLocations'
import type { TripFormValues } from '../tripPlanViewModels'

export type LocationField = 'origin' | 'destination'

export function updateLocationValue(
  values: TripFormValues,
  field: LocationField,
  value: string,
): TripFormValues {
  return {
    ...values,
    [field]: value,
    [`${field}Coordinates`]: undefined,
  }
}

export function selectLocationValue(
  values: TripFormValues,
  field: LocationField,
  suggestion: LocationSuggestion,
): TripFormValues {
  return {
    ...values,
    [field]: suggestion.label,
    [`${field}Coordinates`]: {
      latitude: suggestion.latitude,
      longitude: suggestion.longitude,
    },
  }
}

export function swapTripLocations(values: TripFormValues): TripFormValues {
  return {
    ...values,
    origin: values.destination,
    destination: values.origin,
    originCoordinates: values.destinationCoordinates,
    destinationCoordinates: values.originCoordinates,
  }
}

export function hasVerifiedLocations(values: TripFormValues) {
  return values.originCoordinates !== undefined && values.destinationCoordinates !== undefined
}
