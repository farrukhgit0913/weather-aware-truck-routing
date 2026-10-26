# RouteCast

RouteCast is a weather-aware truck-routing demo built with React, TypeScript,
Django, and Django REST Framework. A dispatcher selects verified U.S. locations,
chooses a departure time and weather-sampling interval, and receives three live
road-route alternatives ranked by forecast exposure and travel time.

## What is included

- Verified city, state, and ZIP-code autocomplete
- Three OSRM road-route alternatives on an interactive OpenStreetMap basemap
- Weather checkpoints every 10, 25, or 50 miles
- A restrained, slider-linked weather corridor instead of an obscuring heat blob
- A 48-hour forecast timeline
- Low, Moderate, High, Severe, and No Travel risk classifications
- A deterministic safest-route recommendation with explainable ranking metrics
- Loading, empty, validation, and provider-error states

## Project structure

- `frontend/` contains the Vite-powered React client.
- `backend/` contains the Django API and local SQLite database.
- Domain features live in dedicated frontend feature folders and Django applications.

The browser sends verified coordinates to Django. The API requests route alternatives,
samples checkpoints along each route, fetches time-aligned weather in bounded batches,
calculates risk, and returns presentation-ready route and forecast data. SQLite is used
for Django's local application data; no external database server is required for the demo.

## Local development

### Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Environment templates are provided in each application. Never commit populated `.env` files.

## Configuration

Copy `backend/.env.example` to `backend/.env` and `frontend/.env.example` to
`frontend/.env`. Provider URLs, timeouts, CORS origins, map tiles, geocoding scope,
and weather request concurrency are configurable without code changes.

The default providers are Open-Meteo Geocoding, Nominatim, OSRM, Open-Meteo Weather,
and OpenStreetMap tiles. These public services keep the demo quick to run, but they
have availability and usage limits; a production deployment should use contracted
providers or self-hosted equivalents.

## How route ranking works

No Travel exposure is treated as a safety gate. Eligible routes are then compared by:

1. Fewest severe miles
2. Fewest high-risk miles
3. Lowest average risk score
4. Shortest travel time

The exact thresholds and rationale are documented in `docs/risk-model.md`; request and
response fields are documented in `docs/api-contract.md`.

## Tests

```powershell
cd backend
.\venv\Scripts\python.exe manage.py test routing.tests

cd ..\frontend
npm test
npm run typecheck
npm run build
```
