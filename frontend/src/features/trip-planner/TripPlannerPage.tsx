import { lazy, Suspense, useState } from 'react'

import { StatusBadge } from '../../shared/components/StatusBadge'
import { ForecastTimeline } from './components/ForecastTimeline'
import { RouteComparison } from './components/RouteComparison'
import { RouteAnalysisLoader } from './components/RouteAnalysisLoader'
import { TripForm } from './components/TripForm'
import { createRoutePlan } from './api/createRoutePlan'
import { ApiError } from '../../shared/services/httpClient'
import { defaultTrip } from './tripPlanDefaults'
import type { RouteViewModel, TripFormValues } from './tripPlanViewModels'
import { presentRoutePlan } from './routePlanPresenter'

const RouteMap = lazy(() => import('./components/RouteMap').then((module) => ({
  default: module.RouteMap,
})))

export function TripPlannerPage() {
  const [trip, setTrip] = useState<TripFormValues>(defaultTrip)
  const [selectedRouteId, setSelectedRouteId] = useState('')
  const [forecastHour, setForecastHour] = useState(12)
  const [routes, setRoutes] = useState<RouteViewModel[]>([])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isLiveData, setIsLiveData] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const selectedRoute = routes.find((route) => route.id === selectedRouteId) ?? routes[0]
  const frames = selectedRoute?.forecastFrames ?? []
  const activeForecast = frames.find((frame) => frame.hour === forecastHour) ?? frames[0]
  const hasRoutePlan = selectedRoute !== undefined && activeForecast !== undefined

  async function handlePlan(nextTrip: TripFormValues) {
    setTrip(nextTrip)
    setIsSubmitting(true)
    setRoutes([])
    setSelectedRouteId('')
    setIsLiveData(false)
    setErrorMessage(null)
    try {
      const response = await createRoutePlan({
        origin: nextTrip.origin,
        destination: nextTrip.destination,
        origin_coordinates: nextTrip.originCoordinates,
        destination_coordinates: nextTrip.destinationCoordinates,
        departure_time: new Date(nextTrip.departureTime).toISOString(),
        load_weight_lb: nextTrip.loadWeightLb,
        sampling_interval_miles: nextTrip.samplingIntervalMiles,
      })
      const presented = presentRoutePlan(response)
      setRoutes(presented.routes)
      setSelectedRouteId(presented.recommendedRouteId)
      setForecastHour(12)
      setIsLiveData(true)
    } catch (error) {
      setRoutes([])
      setSelectedRouteId('')
      setIsLiveData(false)
      setErrorMessage(error instanceof ApiError ? error.message : 'Route analysis failed. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="dashboard-shell">
      <header className="site-header">
        <a className="brand" href="/" aria-label="RouteCast home">
          <span className="brand-mark" aria-hidden="true">R</span>
          <span>RouteCast<small>Fleet weather intelligence</small></span>
        </a>
        <div className="header-meta">
          <span className="updated-time">
            {isSubmitting ? 'Analyzing route network' : isLiveData ? 'Forecast updated just now' : 'Awaiting route analysis'}
          </span>
          <StatusBadge>{isSubmitting ? 'Analyzing' : isLiveData ? 'Live forecast' : 'Ready to plan'}</StatusBadge>
        </div>
      </header>

      <div className="dashboard-grid">
        <aside className="trip-sidebar" aria-label="Trip configuration">
          <div className="panel-heading">
            <p className="eyebrow">New route analysis</p>
            <h1>Plan a safer haul</h1>
            <p>Compare travel time against weather exposure before dispatch.</p>
          </div>
          <TripForm initialValues={defaultTrip} isSubmitting={isSubmitting} onSubmit={handlePlan} />
          {errorMessage ? <div className="form-error" role="alert">{errorMessage}</div> : null}
        </aside>

        <section className="map-workspace" aria-label="Route analysis">
          <div className="trip-summary-bar">
            <div>
              <span className="summary-label">Active corridor</span>
              <strong>{trip.origin} <span aria-hidden="true">→</span> {trip.destination}</strong>
            </div>
            <div className="summary-stat"><span>Departure</span><strong>{formatDeparture(trip.departureTime)}</strong></div>
            <div className="summary-stat"><span>Load</span><strong>{Number(trip.loadWeightLb).toLocaleString()} lb</strong></div>
          </div>

          {isSubmitting ? (
            <RouteAnalysisLoader origin={trip.origin} destination={trip.destination} />
          ) : hasRoutePlan ? (
            <>
              <Suspense fallback={<div className="map-loading">Loading interactive map…</div>}>
                <RouteMap
                  routes={routes}
                  selectedRoute={selectedRoute}
                  forecast={activeForecast}
                  originLabel={trip.origin}
                  destinationLabel={trip.destination}
                  onSelectRoute={setSelectedRouteId}
                />
              </Suspense>
              <ForecastTimeline
                frames={frames}
                selectedHour={forecastHour}
                onChange={setForecastHour}
              />
            </>
          ) : (
            <section className="analysis-empty-state" aria-labelledby="empty-analysis-title">
              <span className="analysis-empty-icon" aria-hidden="true">R</span>
              <p className="eyebrow">Route intelligence</p>
              <h2 id="empty-analysis-title">Your route analysis will appear here</h2>
              <p>Confirm the trip details, then select Analyze routes to load road options and live weather conditions.</p>
            </section>
          )}
        </section>

        <aside className="route-sidebar" aria-label="Route recommendations">
          {isSubmitting ? (
            <div className="comparison-loading-state">
              <p className="eyebrow">Live analysis</p>
              <h2>Comparing routes</h2>
              <p>Travel time and weather exposure are being evaluated.</p>
              <div className="comparison-loading-cards" aria-hidden="true">
                {[1, 2, 3].map((item) => <span key={item}><i /><b /></span>)}
              </div>
            </div>
          ) : hasRoutePlan ? (
            <RouteComparison
              routes={routes}
              selectedRouteId={selectedRoute.id}
              onSelect={setSelectedRouteId}
            />
          ) : (
            <div className="comparison-empty-state">
              <p className="eyebrow">Route comparison</p>
              <h2>No routes analyzed</h2>
              <p>Up to three route options will be ranked here after analysis.</p>
            </div>
          )}
        </aside>
      </div>
    </main>
  )
}

function formatDeparture(value: string) {
  return new Intl.DateTimeFormat('en-US', {
    month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit',
  }).format(new Date(value))
}
