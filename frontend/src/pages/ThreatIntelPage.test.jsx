import React from 'react'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { SearchProvider } from '../app/SearchContext'
import { ThreatIntelPage } from './ThreatIntelPage'
import { api } from '../lib/api'

vi.mock('../lib/api', () => ({
  api: {
    post: vi.fn(),
  },
}))

describe('ThreatIntelPage', () => {
  it('submits query and renders risk summary', async () => {
    api.post.mockResolvedValueOnce({
      data: {
        data: {
          indicator: '8.8.8.8',
          indicator_type: 'ip',
          results: { virustotal: { malicious: 1 } },
          risk_summary: {
            score: 40,
            label: 'medium',
            degraded: false,
            provider_errors: {},
          },
        },
      },
    })

    render(
      <SearchProvider>
        <ThreatIntelPage />
      </SearchProvider>,
    )

    fireEvent.change(screen.getByPlaceholderText('Enter indicator...'), {
      target: { value: '8.8.8.8' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Query Intel' }))

    await waitFor(() => {
      expect(screen.getByText('Intelligence Results')).toBeInTheDocument()
    })

    expect(screen.getByText('Recent Queries')).toBeInTheDocument()
  })
})
