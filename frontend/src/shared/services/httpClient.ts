import { environment } from '../config/environment'

type RequestOptions = Omit<RequestInit, 'body'> & {
  body?: unknown
}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const response = await fetch(`${environment.apiBaseUrl}${path}`, {
    ...options,
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...options.headers,
    },
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  })

  const payload = await response.json().catch(() => null) as
    | T
    | { error?: { message?: string } }
    | null

  if (!response.ok) {
    const message = payload && 'error' in payload
      ? payload.error?.message
      : undefined
    throw new ApiError(
      message ?? 'The server could not complete the request.',
      response.status,
    )
  }

  return payload as T
}
