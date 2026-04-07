import axios from 'axios'

const DEFAULT_BASE_URL = 'http://localhost:8000/api/v1'
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || DEFAULT_BASE_URL

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 20000,
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status
    const requestPath = error?.config?.url || 'unknown-path'

    let message = error?.response?.data?.message || error.message || 'Unknown API error'

    if (status === 404) {
      message = `API 404 on ${requestPath}. Check backend is running and API base URL is ${API_BASE_URL}`
    } else if (!status) {
      message = `Cannot connect to API at ${API_BASE_URL}. Check backend service and CORS.`
    }

    return Promise.reject(new Error(message))
  },
)
