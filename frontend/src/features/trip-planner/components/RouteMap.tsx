import { useEffect, useRef, useState } from 'react'
import type { FeatureCollection, LineString, Point } from 'geojson'
import {
  AttributionControl,
  type CircleLayerSpecification,
  type GeoJSONSource,
  LngLatBounds,
  type LineLayerSpecification,
  Map as MapLibreMap,
  NavigationControl,
  setWorkerUrl,
  type StyleSpecification,
} from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'

import { environment } from '../../../shared/config/environment'
import type {
  CheckpointViewModel,
  ForecastFrameViewModel,
  RouteViewModel,
} from '../tripPlanViewModels'

setWorkerUrl(workerUrl)

interface RouteMapProps {
  routes: RouteViewModel[]
  selectedRoute: RouteViewModel
  forecast: ForecastFrameViewModel
  originLabel: string
  destinationLabel: string
  onSelectRoute: (routeId: string) => void
}

interface RouteProperties {
  id: string
  color: string
  selected: boolean
}

interface CheckpointProperties {
  id: string
  risk: string
}

interface WeatherProperties {
  risk: string
  intensity: number
  checkpointId: string
}

const riskLabels = {
  low: 'Low',
  moderate: 'Moderate',
  high: 'High',
  severe: 'Severe',
  no_travel: 'No travel',
} as const

export function RouteMap({
  routes,
  selectedRoute,
  forecast,
  originLabel,
  destinationLabel,
  onSelectRoute,
}: RouteMapProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<MapLibreMap | null>(null)
  const latestRef = useRef({ routes, selectedRoute, forecast, onSelectRoute })
  const [selectedCheckpoint, setSelectedCheckpoint] = useState<CheckpointViewModel>(
    selectedRoute.checkpoints[Math.min(2, selectedRoute.checkpoints.length - 1)],
  )

  latestRef.current = { routes, selectedRoute, forecast, onSelectRoute }

  useEffect(() => {
    setSelectedCheckpoint(
      selectedRoute.checkpoints[Math.min(2, selectedRoute.checkpoints.length - 1)],
    )
  }, [selectedRoute])

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return

    const initialBounds = getRouteBounds(routes)
    const map = new MapLibreMap({
      container: containerRef.current,
      style: createBaseMapStyle(),
      bounds: initialBounds.isEmpty() ? undefined : initialBounds,
      fitBoundsOptions: {
        padding: { top: 74, right: 54, bottom: 118, left: 54 },
        maxZoom: 8,
        duration: 0,
      },
      attributionControl: false,
    })
    mapRef.current = map
    map.addControl(new NavigationControl({ showCompass: false }), 'top-right')
    map.addControl(
      new AttributionControl({
        compact: true,
        customAttribution: 'Weather by Open-Meteo',
      }),
      'bottom-left',
    )

    map.on('load', () => {
      addMapData(map)
      syncRouteData(map, latestRef.current.routes, latestRef.current.selectedRoute)
      syncWeatherData(map, latestRef.current.selectedRoute, latestRef.current.forecast)
    })

    map.on('click', 'route-lines', (event) => {
      const routeId = event.features?.[0]?.properties?.id as string | undefined
      if (routeId) latestRef.current.onSelectRoute(routeId)
    })
    map.on('click', 'checkpoint-points', (event) => {
      const checkpointId = event.features?.[0]?.properties?.id as string | undefined
      const checkpoint = latestRef.current.selectedRoute.checkpoints.find(
        (item) => item.id === checkpointId,
      )
      if (checkpoint) setSelectedCheckpoint(checkpoint)
    })
    for (const layerId of ['route-lines', 'checkpoint-points']) {
      map.on('mouseenter', layerId, () => { map.getCanvas().style.cursor = 'pointer' })
      map.on('mouseleave', layerId, () => { map.getCanvas().style.cursor = '' })
    }

    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [])

  useEffect(() => {
    const map = mapRef.current
    if (!map?.getSource('route-data')) return
    syncRouteData(map, routes, selectedRoute)
  }, [routes, selectedRoute])

  useEffect(() => {
    const map = mapRef.current
    if (!map?.getSource('weather-corridor-data')) return
    syncWeatherData(map, selectedRoute, forecast)
  }, [forecast, selectedRoute])

  useEffect(() => {
    const map = mapRef.current
    if (!map?.getSource('route-data')) return
    fitRoutes(map, routes)
  }, [routes])

  return (
    <section className="map-card" aria-labelledby="map-title">
      <div className="map-toolbar">
        <div>
          <span className="summary-label">Weather corridor</span>
          <h2 id="map-title">{selectedRoute.name} conditions at {forecast.label.toLowerCase()}</h2>
        </div>
        <div className="map-legend" aria-label="Weather risk legend">
          <span><i data-risk="low" />Low</span>
          <span><i data-risk="moderate" />Moderate</span>
          <span><i data-risk="high" />High</span>
          <span><i data-risk="severe" />Severe</span>
          <span><i data-risk="no_travel" />No travel</span>
        </div>
      </div>

      <div
        className="map-canvas"
        role="region"
        aria-label={`Interactive route map from ${originLabel} to ${destinationLabel}`}
      >
        <div className="real-map" ref={containerRef} />
        <div className="map-weather-card" data-risk={forecast.risk}>
          <div className="map-weather-card-heading">
            <span>{forecast.label} · Corridor snapshot</span>
            <span className="risk-badge" data-risk={forecast.risk}>
              {riskLabels[forecast.risk]}
            </span>
          </div>
          <strong>{forecast.condition}</strong>
          <p>Highest corridor risk at {forecast.focusLabel}</p>
          <div><b>{forecast.temperatureF}°F</b><small>{forecast.windSpeedMph} mph wind</small></div>
        </div>
        <div className="checkpoint-card" data-risk={selectedCheckpoint.risk}>
          <div className="checkpoint-heading">
            <span className="risk-dot" data-risk={selectedCheckpoint.risk} />
            <div>
              <span className="checkpoint-context">Weather at truck ETA</span>
              <strong>{selectedCheckpoint.city}</strong>
              <small>ETA {selectedCheckpoint.eta} · Mile {selectedCheckpoint.distanceMiles}</small>
            </div>
            <span className="risk-badge" data-risk={selectedCheckpoint.risk}>
              {riskLabels[selectedCheckpoint.risk]}
            </span>
          </div>
          <div className="checkpoint-weather">
            <span><small>Condition</small><strong>{selectedCheckpoint.condition}</strong></span>
            <span><small>Temperature</small><strong>{selectedCheckpoint.temperatureF}°F</strong></span>
            <span><small>Wind</small><strong>{selectedCheckpoint.windSpeedMph} mph</strong></span>
          </div>
        </div>
      </div>
    </section>
  )
}

function addMapData(map: MapLibreMap) {
  map.addSource('weather-corridor-data', { type: 'geojson', data: emptyFeatureCollection() })
  map.addSource('route-data', { type: 'geojson', data: emptyFeatureCollection() })
  map.addSource('checkpoint-data', { type: 'geojson', data: emptyFeatureCollection() })
  map.addLayer({
    id: 'weather-risk-corridor',
    type: 'line',
    source: 'weather-corridor-data',
    layout: { 'line-cap': 'round', 'line-join': 'round' },
    paint: {
      'line-width': ['interpolate', ['linear'], ['zoom'], 3, 16, 6, 24, 9, 32],
      'line-color': riskColorExpression(),
      'line-opacity': [
        'interpolate', ['linear'], ['get', 'intensity'],
        0, 0.32,
        0.25, 0.46,
        0.5, 0.58,
        0.75, 0.7,
        1, 0.82,
      ],
    },
  } as LineLayerSpecification)
  map.addLayer({
    id: 'route-casing',
    type: 'line',
    source: 'route-data',
    layout: { 'line-cap': 'round', 'line-join': 'round' },
    paint: {
      'line-color': '#ffffff',
      'line-width': ['case', ['get', 'selected'], 9, 5],
      'line-opacity': ['case', ['get', 'selected'], 0.92, 0.58],
    },
  } as LineLayerSpecification)
  map.addLayer({
    id: 'route-lines',
    type: 'line',
    source: 'route-data',
    layout: { 'line-cap': 'round', 'line-join': 'round' },
    paint: {
      'line-color': ['get', 'color'],
      'line-width': ['case', ['get', 'selected'], 6, 3],
      'line-opacity': ['case', ['get', 'selected'], 1, 0.62],
    },
  } as LineLayerSpecification)
  map.addLayer({
    id: 'weather-risk-indicator',
    type: 'line',
    source: 'weather-corridor-data',
    layout: { 'line-cap': 'round', 'line-join': 'round' },
    paint: {
      'line-width': ['interpolate', ['linear'], ['zoom'], 3, 2, 6, 3, 9, 4],
      'line-color': riskColorExpression(),
      'line-opacity': 0.96,
    },
  } as LineLayerSpecification)
  map.addLayer({
    id: 'checkpoint-points',
    type: 'circle',
    source: 'checkpoint-data',
    paint: {
      'circle-radius': ['interpolate', ['linear'], ['zoom'], 3, 4, 6, 6, 9, 8],
      'circle-color': riskColorExpression(),
      'circle-stroke-color': '#ffffff',
      'circle-stroke-width': ['interpolate', ['linear'], ['zoom'], 3, 1.5, 8, 2.5],
    },
  } as CircleLayerSpecification)
}

function createBaseMapStyle(): string | StyleSpecification {
  if (environment.mapStyleUrl) return environment.mapStyleUrl

  return {
    version: 8,
    sources: {
      'openstreetmap-road-tiles': {
        type: 'raster',
        tiles: [environment.mapTileUrl],
        tileSize: 256,
        minzoom: 0,
        maxzoom: 19,
        attribution: '© OpenStreetMap contributors',
      },
    },
    layers: [
      {
        id: 'openstreetmap-road-basemap',
        type: 'raster',
        source: 'openstreetmap-road-tiles',
        minzoom: 0,
        maxzoom: 19,
      },
    ],
  }
}

function syncRouteData(map: MapLibreMap, routes: RouteViewModel[], selectedRoute: RouteViewModel) {
  const routeSource = map.getSource('route-data') as GeoJSONSource | undefined
  const checkpointSource = map.getSource('checkpoint-data') as GeoJSONSource | undefined
  routeSource?.setData(routeFeatureCollection(routes, selectedRoute.id))
  checkpointSource?.setData(checkpointFeatureCollection(selectedRoute))
}

function syncWeatherData(
  map: MapLibreMap,
  route: RouteViewModel,
  forecast: ForecastFrameViewModel,
) {
  const source = map.getSource('weather-corridor-data') as GeoJSONSource | undefined
  source?.setData(weatherCorridorFeatureCollection(route, forecast))
}

function routeFeatureCollection(
  routes: RouteViewModel[],
  selectedRouteId: string,
): FeatureCollection<LineString, RouteProperties> {
  return {
    type: 'FeatureCollection',
    features: routes.map((route) => ({
      type: 'Feature',
      properties: {
        id: route.id,
        color: route.color,
        selected: route.id === selectedRouteId,
      },
      geometry: { type: 'LineString', coordinates: getRouteCoordinates(route) },
    })),
  }
}

function checkpointFeatureCollection(
  route: RouteViewModel,
): FeatureCollection<Point, CheckpointProperties> {
  return {
    type: 'FeatureCollection',
    features: route.checkpoints.map((checkpoint) => ({
      type: 'Feature',
      properties: { id: checkpoint.id, risk: checkpoint.risk },
      geometry: {
        type: 'Point',
        coordinates: [checkpoint.longitude, checkpoint.latitude],
      },
    })),
  }
}

function weatherCorridorFeatureCollection(
  route: RouteViewModel,
  forecast: ForecastFrameViewModel,
): FeatureCollection<LineString, WeatherProperties> {
  if (route.coordinates.length < 2 || forecast.cells.length === 0) {
    return emptyFeatureCollection() as FeatureCollection<LineString, WeatherProperties>
  }

  const cumulativeDistances = [0]
  for (let index = 1; index < route.coordinates.length; index += 1) {
    cumulativeDistances.push(
      cumulativeDistances[index - 1]
      + coordinateDistanceMiles(route.coordinates[index - 1], route.coordinates[index]),
    )
  }
  const geometryMiles = cumulativeDistances.at(-1) ?? 0
  const features: FeatureCollection<LineString, WeatherProperties>['features'] = []
  let activeCell = forecast.cells[0]
  let activeCoordinates: [number, number][] = [route.coordinates[0]]

  for (let index = 1; index < route.coordinates.length; index += 1) {
    const midpointGeometryMiles = (
      cumulativeDistances[index - 1] + cumulativeDistances[index]
    ) / 2
    const midpointRouteMiles = geometryMiles === 0
      ? 0
      : midpointGeometryMiles / geometryMiles * route.distanceMiles
    const cell = nearestWeatherCell(forecast, midpointRouteMiles)

    if (cell.checkpointId !== activeCell.checkpointId) {
      if (activeCoordinates.length > 1) {
        features.push(weatherCorridorFeature(activeCoordinates, activeCell))
      }
      activeCoordinates = [route.coordinates[index - 1]]
      activeCell = cell
    }
    activeCoordinates.push(route.coordinates[index])
  }

  if (activeCoordinates.length > 1) {
    features.push(weatherCorridorFeature(activeCoordinates, activeCell))
  }
  return { type: 'FeatureCollection', features }
}

function weatherCorridorFeature(
  coordinates: [number, number][],
  cell: ForecastFrameViewModel['cells'][number],
) {
  return {
    type: 'Feature' as const,
    properties: {
      risk: cell.risk,
      intensity: cell.intensity,
      checkpointId: cell.checkpointId,
    },
    geometry: { type: 'LineString' as const, coordinates },
  }
}

function nearestWeatherCell(forecast: ForecastFrameViewModel, distanceMiles: number) {
  return forecast.cells.reduce((nearest, cell) => (
    Math.abs(cell.distanceMiles - distanceMiles) < Math.abs(nearest.distanceMiles - distanceMiles)
      ? cell
      : nearest
  ))
}

function coordinateDistanceMiles(start: [number, number], end: [number, number]) {
  const meanLatitude = (start[1] + end[1]) / 2 * Math.PI / 180
  const longitudeMiles = (end[0] - start[0]) * Math.cos(meanLatitude) * 69
  const latitudeMiles = (end[1] - start[1]) * 69
  return Math.hypot(longitudeMiles, latitudeMiles)
}

function fitRoutes(map: MapLibreMap, routes: RouteViewModel[]) {
  const bounds = getRouteBounds(routes)
  if (!bounds.isEmpty()) {
    map.fitBounds(bounds, {
      padding: { top: 74, right: 54, bottom: 118, left: 54 },
      maxZoom: 8,
      duration: 0,
    })
  }
}

function getRouteBounds(routes: RouteViewModel[]) {
  const bounds = new LngLatBounds()
  routes.flatMap(getRouteCoordinates).forEach((coordinate) => bounds.extend(coordinate))
  return bounds
}

function getRouteCoordinates(route: RouteViewModel): [number, number][] {
  return route.coordinates
}

function riskColorExpression(): CircleLayerSpecification['paint']['circle-color'] {
  return [
    'match', ['get', 'risk'],
    'low', '#2f7a61',
    'moderate', '#c08a2d',
    'high', '#c26528',
    'severe', '#b14338',
    'no_travel', '#762c2c',
    '#68736f',
  ]
}

function emptyFeatureCollection(): FeatureCollection {
  return { type: 'FeatureCollection', features: [] }
}
