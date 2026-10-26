import { apiRequest } from '../../../shared/services/httpClient'

export interface LocationSuggestion {
  id: string
  name: string
  region: string
  country: string
  country_code: string
  label: string
  latitude: number
  longitude: number
}

interface LocationSearchResponse {
  results: LocationSuggestion[]
}

export function searchLocations(query: string, signal: AbortSignal) {
  return apiRequest<LocationSearchResponse>(
    `/locations/?q=${encodeURIComponent(query)}`,
    { method: 'GET', signal },
  )
}
