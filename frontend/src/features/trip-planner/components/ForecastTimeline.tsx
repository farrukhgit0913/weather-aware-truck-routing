import type { ForecastFrameViewModel } from '../tripPlanViewModels'

interface ForecastTimelineProps {
  frames: ForecastFrameViewModel[]
  selectedHour: number
  onChange: (hour: number) => void
}

export function ForecastTimeline({
  frames,
  selectedHour,
  onChange,
}: ForecastTimelineProps) {
  const selectedFrame = frames.find((frame) => frame.hour === selectedHour) ?? frames[0]

  return (
    <section className="forecast-panel" aria-labelledby="forecast-title">
      <div className="forecast-heading">
        <div>
          <span className="summary-label">Forecast timeline</span>
          <h2 id="forecast-title">Conditions across the next 48 hours</h2>
        </div>
        <div className="forecast-now">
          <span className="risk-dot" data-risk={selectedFrame.risk} />
          <span>
            <strong>{selectedFrame.condition} · {selectedFrame.focusLabel}</strong>
            <small>
              Highest corridor risk · {selectedFrame.windSpeedMph} mph ·{' '}
              {selectedFrame.precipitationChance}% precipitation
            </small>
          </span>
        </div>
      </div>
      <div className="timeline-control">
        <input
          aria-label="Forecast hour"
          type="range"
          min="0"
          max="48"
          step="6"
          value={selectedHour}
          onChange={(event) => onChange(Number(event.target.value))}
        />
        <div className="timeline-labels" aria-hidden="true">
          {frames.map((frame) => <span key={frame.hour}>{frame.label}</span>)}
        </div>
      </div>
    </section>
  )
}
