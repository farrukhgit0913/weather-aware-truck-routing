import type { CSSProperties } from 'react'
import type { RouteViewModel } from '../tripPlanViewModels'

interface RouteComparisonProps { routes: RouteViewModel[]; selectedRouteId: string; onSelect: (routeId: string) => void }

export function RouteComparison({ routes, selectedRouteId, onSelect }: RouteComparisonProps) {
  const recommendedRoute = routes.find((route) => route.recommended) ?? routes[0]
  return (
    <div className="route-comparison">
      <div className="comparison-heading"><div><p className="eyebrow">Route comparison</p><h2>{routes.length} viable options</h2></div><span className="route-count">{routes.length}</span></div>
      <div className="recommendation-note"><span className="recommendation-icon" aria-hidden="true">✓</span><div><strong>Safest route identified</strong><p>{recommendedRoute.name} has the strongest balance of no-travel exposure, severe weather, high-risk mileage, and travel time.</p></div></div>
      <div className="route-list">
        {routes.map((route, index) => {
          const isSelected = route.id === selectedRouteId
          const highestRisk = route.noTravelMiles > 0
            ? 'no_travel'
            : route.severeMiles > 0
              ? 'severe'
              : route.highRiskMiles > 0
                ? 'high'
                : 'low'
          const riskSummary = route.noTravelMiles > 0
            ? `${Math.round(route.noTravelMiles)} no-travel mi`
            : route.severeMiles > 0
              ? `${Math.round(route.severeMiles)} severe mi`
              : `${Math.round(route.highRiskMiles)} high-risk mi`
          return (
            <button
              className="route-card"
              data-selected={isSelected}
              type="button"
              key={route.id}
              onClick={() => onSelect(route.id)}
              aria-pressed={isSelected}
              style={{ '--route-color': route.color } as CSSProperties}
            >
              <span className="route-card-topline"><span className="route-rank">Option {String(index + 1).padStart(2, '0')}</span>{route.recommended ? <span className="recommended-pill">Recommended</span> : <span className="route-kind">Alternative</span>}</span>
              <span className="route-title-row"><span><strong>{route.name}</strong><small>{route.via}</small></span><span className="route-swatch" style={{ backgroundColor: route.color }} /></span>
              <span className="route-metrics"><span><strong>{route.duration}</strong><small>Travel time</small></span><span><strong>{route.distanceMiles.toLocaleString()} mi</strong><small>Distance</small></span><span><strong>{route.arrival}</strong><small>Arrival</small></span></span>
              <span className="risk-summary"><span className="risk-badge" data-risk={highestRisk}>{riskSummary}</span><span>Risk score {route.averageRiskScore.toFixed(1)}</span></span>
            </button>
          )
        })}
      </div>
      <div className="ranking-logic"><span>How routes are ranked</span><p>Severe miles · High-risk miles · Average risk · Travel time</p></div>
    </div>
  )
}
