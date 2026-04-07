import React from 'react'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { SimulationLabPage } from './SimulationLabPage'
import { api } from '../lib/api'

const mockNavigate = vi.fn()

vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal()
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

vi.mock('../lib/api', () => ({
  api: {
    post: vi.fn(),
  },
}))

describe('SimulationLabPage', () => {
  it('runs simulation and stores summary', async () => {
    api.post.mockResolvedValueOnce({
      data: {
        data: {
          contract_version: 'v1',
          simulation_type: 'phishing',
          requested_count: 20,
          alerts_generated: 20,
          incidents_created: 20,
          latest_incident_id: 123,
          pipeline_flow: ['simulation', 'incident'],
        },
      },
    })

    render(
      <MemoryRouter>
        <SimulationLabPage />
      </MemoryRouter>,
    )

    fireEvent.click(screen.getAllByRole('button', { name: 'Run' })[1])

    await waitFor(() => {
      expect(screen.getByText('Last Run Summary')).toBeInTheDocument()
    })

    expect(mockNavigate).toHaveBeenCalledWith('/incidents/123')
  })
})
