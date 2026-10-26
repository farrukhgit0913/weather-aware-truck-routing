import { useState, type FormEvent } from 'react'
import type { SamplingIntervalMiles } from '../api/routePlan.types'
import type { LocationSuggestion } from '../api/searchLocations'
import type { TripFormValues } from '../tripPlanViewModels'
import { departureDateTimeBounds } from '../tripPlanDefaults'
import {
  selectLocationValue,
  swapTripLocations,
  updateLocationValue,
  type LocationField,
} from '../utils/tripLocations'
import { LocationAutocomplete } from './LocationAutocomplete'

interface TripFormProps {
  initialValues: TripFormValues
  isSubmitting: boolean
  onSubmit: (values: TripFormValues) => void
}
const samplingOptions: SamplingIntervalMiles[] = [10, 25, 50]

export function TripForm({ initialValues, isSubmitting, onSubmit }: TripFormProps) {
  const [values, setValues] = useState(initialValues)
  const [locationError, setLocationError] = useState<string | null>(null)
  const departureBounds = departureDateTimeBounds()
  const hasManualLocation = (
    (values.origin.trim().length > 0 && !values.originCoordinates)
    || (values.destination.trim().length > 0 && !values.destinationCoordinates)
  )

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const origin = values.origin.trim()
    const destination = values.destination.trim()
    if (!origin || !destination) {
      setLocationError('Enter both an origin and destination.')
      return
    }
    setLocationError(null)
    onSubmit({ ...values, origin, destination })
  }

  function swapLocations() {
    setValues(swapTripLocations)
    setLocationError(null)
  }

  function updateLocation(field: LocationField, value: string) {
    setValues((current) => updateLocationValue(current, field, value))
    setLocationError(null)
  }

  function selectLocation(field: LocationField, suggestion: LocationSuggestion) {
    setValues((current) => selectLocationValue(current, field, suggestion))
    setLocationError(null)
  }

  return (
    <form className="trip-form" onSubmit={handleSubmit} aria-busy={isSubmitting}>
      <div className="location-section">
        <div className="location-fields">
          <LocationAutocomplete
            field="origin"
            label="Origin"
            value={values.origin}
            coordinates={values.originCoordinates}
            disabled={isSubmitting}
            invalid={locationError !== null && values.origin.trim().length === 0}
            onChange={(value) => updateLocation('origin', value)}
            onSelect={(suggestion) => selectLocation('origin', suggestion)}
          />
          <button className="swap-button" type="button" onClick={swapLocations} aria-label="Swap origin and destination">⇅</button>
          <LocationAutocomplete
            field="destination"
            label="Destination"
            value={values.destination}
            coordinates={values.destinationCoordinates}
            disabled={isSubmitting}
            invalid={locationError !== null && values.destination.trim().length === 0}
            onChange={(value) => updateLocation('destination', value)}
            onSelect={(suggestion) => selectLocation('destination', suggestion)}
          />
        </div>
        {locationError ? (
          <div className="location-guidance" data-error="true" role="alert">
            {locationError}
          </div>
        ) : hasManualLocation ? (
          <div className="location-guidance">
            Manual locations will be verified when routes are analyzed.
          </div>
        ) : null}
      </div>

      <label className="field-group"><span>Departure date and time</span>
        <input
          className="standalone-input"
          required
          type="datetime-local"
          min={departureBounds.minimum}
          max={departureBounds.maximum}
          value={values.departureTime}
          onChange={(event) => setValues({ ...values, departureTime: event.target.value })}
        />
      </label>
      <label className="field-group"><span>Gross load weight</span>
        <span className="weight-input"><input required min="1" type="number" value={values.loadWeightLb} onChange={(event) => setValues({ ...values, loadWeightLb: Number(event.target.value) })} /><span>lb</span></span>
      </label>

      <fieldset className="sampling-fieldset">
        <legend>Weather sampling interval</legend>
        <div className="segmented-control">
          {samplingOptions.map((option) => (
            <label key={option}><input type="radio" name="sampling-interval" value={option} checked={values.samplingIntervalMiles === option} onChange={() => setValues({ ...values, samplingIntervalMiles: option })} /><span>{option} mi</span></label>
          ))}
        </div>
      </fieldset>
      <button className="primary-button" data-loading={isSubmitting} type="submit" disabled={isSubmitting}>
        <span className="button-copy">
          <strong>{isSubmitting ? 'Analyzing routes' : 'Analyze routes'}</strong>
          <small>{isSubmitting ? 'Checking road weather…' : 'Compare time and weather'}</small>
        </span>
        <span className="button-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24">
            <circle cx="5" cy="16" r="2" />
            <circle cx="13" cy="8" r="2" />
            <path d="M6.7 14.9 11.3 9.2M15 8h4M17 5l3 3-3 3" />
          </svg>
        </span>
      </button>
    </form>
  )
}
