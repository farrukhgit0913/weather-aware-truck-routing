import { useEffect, useState } from 'react'

interface RouteAnalysisLoaderProps {
  origin: string
  destination: string
}

const stages = [
  'Resolving verified locations',
  'Comparing highway alternatives',
  'Checking route weather',
  'Ranking the safest option',
] as const

export function RouteAnalysisLoader({ origin, destination }: RouteAnalysisLoaderProps) {
  const [activeStage, setActiveStage] = useState(0)

  useEffect(() => {
    const timers = stages.slice(1).map((_, index) => window.setTimeout(
      () => setActiveStage(index + 1),
      (index + 1) * 1200,
    ))
    return () => timers.forEach(window.clearTimeout)
  }, [])

  return (
    <section className="route-analysis-loader" aria-busy="true" aria-labelledby="route-loader-title">
      <div className="route-loader-heading">
        <span className="route-loader-kicker"><i aria-hidden="true" />Live route analysis</span>
        <h2 id="route-loader-title">Building your safest route</h2>
        <p aria-live="polite">{stages[activeStage]}…</p>
      </div>

      <div className="route-loader-visual" aria-hidden="true">
        <svg viewBox="0 0 680 220" preserveAspectRatio="xMidYMid meet">
          <path className="route-loader-guide" d="M74 142 C174 42 275 61 350 120 S510 192 606 76" />
          <path className="route-loader-path" pathLength="1" d="M74 142 C174 42 275 61 350 120 S510 192 606 76" />
          <circle className="route-loader-checkpoint checkpoint-one" cx="205" cy="72" r="6" />
          <circle className="route-loader-checkpoint checkpoint-two" cx="350" cy="120" r="6" />
          <circle className="route-loader-checkpoint checkpoint-three" cx="493" cy="158" r="6" />
          <circle className="route-loader-endpoint" cx="74" cy="142" r="12" />
          <circle className="route-loader-endpoint-core" cx="74" cy="142" r="5" />
          <circle className="route-loader-endpoint" cx="606" cy="76" r="12" />
          <circle className="route-loader-endpoint-core" cx="606" cy="76" r="5" />
          <g className="route-loader-vehicle">
            <rect x="-15" y="-9" width="20" height="13" rx="3" />
            <path d="M5 -6 H11 L16 0 V4 H5 Z" />
            <circle cx="-9" cy="6" r="3" />
            <circle cx="10" cy="6" r="3" />
            <animateMotion
              dur="3.2s"
              repeatCount="indefinite"
              rotate="auto"
              path="M74 142 C174 42 275 61 350 120 S510 192 606 76"
            />
          </g>
        </svg>
        <div className="route-loader-location route-loader-origin"><span>Origin</span><strong>{shortLocation(origin)}</strong></div>
        <div className="route-loader-location route-loader-destination"><span>Destination</span><strong>{shortLocation(destination)}</strong></div>
      </div>

      <ol className="route-loader-stages" aria-hidden="true">
        {stages.map((stage, index) => {
          const state = index < activeStage ? 'complete' : index === activeStage ? 'active' : 'pending'
          return (
            <li data-state={state} key={stage}>
              <span className="route-loader-stage-mark">{state === 'complete' ? '✓' : index + 1}</span>
              <span>{stage}</span>
            </li>
          )
        })}
      </ol>
    </section>
  )
}

function shortLocation(label: string) {
  return label.split(',')[0] || label
}
