import { api } from '../api'

export async function fetchSimulationSummary(limit = 50) {
  const response = await api.get('/simulations/summary', { params: { limit } })
  return response.data.data
}

export async function fetchIncidentsPage(page = 1, pageSize = 50) {
  const response = await api.get('/incidents', { params: { page, page_size: pageSize } })
  return response.data.data
}

export async function fetchObservabilityMetrics() {
  const response = await api.get('/observability/metrics')
  return response.data?.data?.metrics || null
}

export async function fetchQueueMetrics(windowHours = 24) {
  const response = await api.get('/simulations/queue-metrics', { params: { window_hours: windowHours } })
  return response.data?.data?.queue || null
}

export async function runSimulation(simulationType, count) {
  const response = await api.post(`/simulations/${simulationType}`, null, { params: { count } })
  return response.data?.data || {}
}

export async function fetchPlaybooks() {
  const response = await api.get('/playbooks')
  return response.data.data.items || []
}

export async function fetchPlaybookStats(playbookId) {
  const response = await api.get(`/playbooks/${playbookId}/stats`)
  return response.data.data
}

export async function fetchPlaybookExecutions(playbookId, { status = 'all', sinceHours, page, pageSize }) {
  const response = await api.get(`/playbooks/${playbookId}/executions`, {
    params: {
      ...(status !== 'all' ? { status } : {}),
      ...(sinceHours ? { since_hours: sinceHours } : {}),
      page,
      page_size: pageSize,
    },
  })
  return response.data.data
}
