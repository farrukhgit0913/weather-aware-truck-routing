import {
  useEffect,
  useId,
  useRef,
  useState,
  type KeyboardEvent,
} from 'react'

import type { Coordinates } from '../api/routePlan.types'
import {
  searchLocations,
  type LocationSuggestion,
} from '../api/searchLocations'

interface LocationAutocompleteProps {
  field: 'origin' | 'destination'
  label: string
  value: string
  coordinates?: Coordinates
  disabled?: boolean
  invalid?: boolean
  onChange: (value: string) => void
  onSelect: (suggestion: LocationSuggestion) => void
}

type SearchStatus = 'idle' | 'loading' | 'success' | 'error'

export function LocationAutocomplete({
  field,
  label,
  value,
  coordinates,
  disabled = false,
  invalid = false,
  onChange,
  onSelect,
}: LocationAutocompleteProps) {
  const inputId = useId()
  const listboxId = useId()
  const wrapperRef = useRef<HTMLDivElement>(null)
  const [isFocused, setIsFocused] = useState(false)
  const [status, setStatus] = useState<SearchStatus>('idle')
  const [suggestions, setSuggestions] = useState<LocationSuggestion[]>([])
  const [activeIndex, setActiveIndex] = useState(0)
  const normalizedQuery = value.trim()
  const isVerified = coordinates !== undefined
  const showMenu = isFocused && !isVerified && normalizedQuery.length >= 3

  useEffect(() => {
    if (!showMenu) {
      setStatus('idle')
      setSuggestions([])
      return
    }

    const controller = new AbortController()
    const timer = window.setTimeout(async () => {
      setStatus('loading')
      try {
        const response = await searchLocations(normalizedQuery, controller.signal)
        setSuggestions(response.results)
        setActiveIndex(0)
        setStatus('success')
      } catch (error) {
        if (error instanceof DOMException && error.name === 'AbortError') return
        setSuggestions([])
        setStatus('error')
      }
    }, 300)

    return () => {
      window.clearTimeout(timer)
      controller.abort()
    }
  }, [normalizedQuery, showMenu])

  function selectSuggestion(suggestion: LocationSuggestion) {
    onSelect(suggestion)
    setSuggestions([])
    setStatus('idle')
    setIsFocused(false)
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (!showMenu || suggestions.length === 0) {
      if (event.key === 'Escape') setIsFocused(false)
      return
    }

    if (event.key === 'ArrowDown') {
      event.preventDefault()
      setActiveIndex((current) => (current + 1) % suggestions.length)
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      setActiveIndex((current) => (current - 1 + suggestions.length) % suggestions.length)
    } else if (event.key === 'Enter') {
      event.preventDefault()
      selectSuggestion(suggestions[activeIndex])
    } else if (event.key === 'Escape') {
      event.preventDefault()
      setIsFocused(false)
    }
  }

  function handleBlur() {
    window.setTimeout(() => {
      if (!wrapperRef.current?.contains(document.activeElement)) setIsFocused(false)
    }, 0)
  }

  return (
    <div className="location-autocomplete" ref={wrapperRef}>
      <div className="location-field">
        <span className={`location-dot ${field}-dot`} aria-hidden="true" />
        <span className="location-field-content">
          <label htmlFor={inputId}>
            {label}
            {isVerified ? <span className="location-verified" aria-label="Verified location">✓</span> : null}
          </label>
          <input
            id={inputId}
            required
            role="combobox"
            aria-autocomplete="list"
            aria-controls={listboxId}
            aria-expanded={showMenu}
            aria-activedescendant={showMenu && suggestions[activeIndex]
              ? `${listboxId}-${suggestions[activeIndex].id}`
              : undefined}
            aria-invalid={invalid}
            autoComplete="off"
            spellCheck={false}
            disabled={disabled}
            value={value}
            onChange={(event) => onChange(event.target.value)}
            onFocus={() => setIsFocused(true)}
            onBlur={handleBlur}
            onKeyDown={handleKeyDown}
            placeholder="City, state, or ZIP"
          />
        </span>
      </div>

      {showMenu ? (
        <div className="location-menu" id={listboxId} role="listbox" aria-label={`${label} suggestions`}>
          {status === 'loading' ? <div className="location-menu-status">Searching locations…</div> : null}
          {status === 'error' ? <div className="location-menu-status" role="status">Suggestions unavailable. Try again.</div> : null}
          {status === 'success' && suggestions.length === 0 ? <div className="location-menu-status">No U.S. locations found.</div> : null}
          {suggestions.map((suggestion, index) => (
            <button
              id={`${listboxId}-${suggestion.id}`}
              className="location-option"
              data-active={index === activeIndex}
              type="button"
              role="option"
              aria-selected={index === activeIndex}
              key={suggestion.id}
              onMouseDown={(event) => event.preventDefault()}
              onClick={() => selectSuggestion(suggestion)}
            >
              <span className="location-option-icon" aria-hidden="true">⌖</span>
              <span><strong>{suggestion.name}</strong><small>{[suggestion.region, suggestion.country].filter(Boolean).join(', ')}</small></span>
            </button>
          ))}
          <div className="location-menu-credit">Location data by Open-Meteo</div>
        </div>
      ) : null}
    </div>
  )
}
