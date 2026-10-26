import { createRoot } from 'react-dom/client'

import { App } from './app/App'
import './styles/globals.css'

type RouteCastWindow = Window & {
  __routeCastMapAbortGuardInstalled?: boolean
}

function installMapAbortGuard() {
  const guardedWindow = window as RouteCastWindow
  if (guardedWindow.__routeCastMapAbortGuardInstalled) return

  window.addEventListener('unhandledrejection', (event) => {
    const reason = event.reason
    if (!(reason instanceof Error) || reason.name !== 'AbortError') return

    const stack = reason.stack ?? ''
    const isMapLibreCancellation = stack.includes('maplibre-gl')
      || reason.message === 'signal is aborted without reason'

    if (isMapLibreCancellation) event.preventDefault()
  })

  guardedWindow.__routeCastMapAbortGuardInstalled = true
}

const rootElement = document.getElementById('root')

if (!rootElement) {
  throw new Error('Application root element was not found.')
}

installMapAbortGuard()
createRoot(rootElement).render(<App />)
