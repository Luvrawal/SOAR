import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { DashboardPage } from './DashboardPage'
import { api } from '../lib/api'

vi.mock('../lib/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
  getLastCorrelationId: vi.fn(() => 'test-correlation-id'),
}))

describe('DashboardPage', () => {
  it('renders operations metrics and handles observability access fallback', async () => {
    api.get.mockImplementation(async (url) => {
      if (url === '/simulations/summary') {
        return {
          data: {
            data: {
              total_incidents: 4,
              queue: {
                backlog: 3,
                capacity: 200,
                pressure: 'low',
                utilization_pct: 1.5,
                per_queue: {
                  playbook_default: {
                    total: 2,
                    failed: 0,
                    throughput_per_hour: 0.08,
                    failure_rate_pct: 0,
                  },
                },
              },
            },
          },
        }
      }

      if (url === '/incidents') {
        return {
          data: {
            data: {
              items: [
                {
                  id: 101,
                  title: 'Brute Force Detected',
                  severity: 'high',
                  status: 'open',
                  playbook_status: 'pending',
                  created_at: new Date().toISOString(),
                },
              ],
            },
          },
        }
      }

      if (url === '/observability/metrics') {
        return {
          data: {
            data: {
              metrics: {
                error_rate_pct: 0,
                avg_latency_ms: 12.4,
                recent_events: [
                  {
                    timestamp: new Date().toISOString(),
                    method: 'GET',
                    route: '/api/v1/health',
                    status_code: 200,
                    latency_ms: 10.2,
                    correlation_id: 'test-correlation-id',
                  },
                ],
                recent_trace_events: [
                  {
                    timestamp: new Date().toISOString(),
                    stage: 'queue.enqueue',
                    message: 'Incident queued for asynchronous playbook execution',
                    correlation_id: 'test-correlation-id',
                  },
                ],
              },
            },
          },
        }
      }

      return { data: { data: {} } }
    })

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByText('Platform Operations')).toBeInTheDocument()
    })

    expect(screen.getByText('Queue Backlog')).toBeInTheDocument()
    expect(screen.getByText('Recent API Events')).toBeInTheDocument()
    expect(screen.getByText('Recent Queue and Task Events')).toBeInTheDocument()
  })

  it('falls back to queue-metrics endpoint when summary queue is unavailable', async () => {
    api.get.mockImplementation(async (url) => {
      if (url === '/simulations/summary') {
        return {
          data: {
            data: {
              total_incidents: 2,
            },
          },
        }
      }

      if (url === '/simulations/queue-metrics') {
        return {
          data: {
            data: {
              queue: {
                backlog: 7,
                capacity: 200,
                pressure: 'medium',
                utilization_pct: 3.5,
                per_queue: {},
              },
            },
          },
        }
      }

      if (url === '/incidents') {
        return {
          data: {
            data: {
              items: [],
            },
          },
        }
      }

      if (url === '/observability/metrics') {
        throw new Error('Request failed with status code 403')
      }

      return { data: { data: {} } }
    })

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByText('Platform Operations')).toBeInTheDocument()
    })

    expect(screen.getByText('7')).toBeInTheDocument()
    expect(screen.getByText('Detailed platform observability metrics are available to admin role.')).toBeInTheDocument()
    expect(screen.getByText('Endpoint status: summary=fulfilled, queue-metrics=fulfilled, observability=rejected')).toBeInTheDocument()
  })

  it('derives queue metrics from summary breakdown when queue endpoints are unavailable', async () => {
    api.get.mockImplementation(async (url) => {
      if (url === '/simulations/summary') {
        return {
          data: {
            data: {
              total_incidents: 10,
              playbook_status_breakdown: {
                pending: 5,
                running: 3,
              },
            },
          },
        }
      }

      if (url === '/simulations/queue-metrics') {
        throw new Error('Request failed with status code 404')
      }

      if (url === '/incidents') {
        return {
          data: {
            data: {
              items: [],
            },
          },
        }
      }

      if (url === '/observability/metrics') {
        throw new Error('Cannot connect to API')
      }

      return { data: { data: {} } }
    })

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByText('Platform Operations')).toBeInTheDocument()
    })

    expect(screen.getByText('8')).toBeInTheDocument()
    expect(screen.getByText('Queue metrics fallback is derived from summary and incident status data. Observability metrics are temporarily unavailable.')).toBeInTheDocument()
    expect(screen.getByText('Endpoint status: summary=fulfilled, queue-metrics=rejected, observability=rejected')).toBeInTheDocument()
  })
})
