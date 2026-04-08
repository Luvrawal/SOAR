import axios from 'axios'

const DEFAULT_BASE_URL = 'http://localhost:8000/api/v1'
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || DEFAULT_BASE_URL

let authTokenGetter = null
let unauthorizedHandler = null
let lastCorrelationId = null

export function setAuthTokenGetter(getter) {
  authTokenGetter = getter
}

export function setUnauthorizedHandler(handler) {
  unauthorizedHandler = handler
}

export function getLastCorrelationId() {
  return lastCorrelationId
}

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 20000,
})

api.interceptors.request.use((config) => {
  const token = authTokenGetter ? authTokenGetter() : null
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => {
    const headerValue = response?.headers?.['x-correlation-id'] || response?.headers?.['X-Correlation-ID']
    if (headerValue) {
      lastCorrelationId = headerValue
    }
    return response
  },
  (error) => {
    const status = error?.response?.status
    const requestPath = error?.config?.url || 'unknown-path'
    const hadAuthToken = Boolean(authTokenGetter && authTokenGetter())

    let message = error?.response?.data?.message || error.message || 'Unknown API error'

    if (status === 404) {
      message = `API 404 on ${requestPath}. Check backend is running and API base URL is ${API_BASE_URL}`
    } else if (status === 401 && unauthorizedHandler && hadAuthToken) {
      unauthorizedHandler(error)
      message = 'Your session has expired. Please sign in again.'
    } else if (!status) {
      message = `Cannot connect to API at ${API_BASE_URL}. Check backend service and CORS.`
    }

    return Promise.reject(new Error(message))
  },
)
