import { apiRequest } from '../../../shared/services/httpClient'
import type { RoutePlanRequest, RoutePlanResponse } from './routePlan.types'

export function createRoutePlan(input: RoutePlanRequest) {
  return apiRequest<RoutePlanResponse>('/route-plans/', {
    method: 'POST',
    body: input,
  })
}
