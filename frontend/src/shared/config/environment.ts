const defaultApiBaseUrl = 'https://weather-aware-truck-routing-fawn.vercel.app/api/v1'

export const environment = Object.freeze({
  apiBaseUrl: import.meta.env.API_BASE_URL ?? defaultApiBaseUrl,
  mapStyleUrl: import.meta.env.MAP_STYLE_URL || null,
  mapTileUrl:
    import.meta.env.VITE_MAP_TILE_URL
    || 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
})
