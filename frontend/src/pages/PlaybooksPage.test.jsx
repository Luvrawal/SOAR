import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { PlaybooksPage } from './PlaybooksPage'
import { api } from '../lib/api'

vi.mock('../lib/api', () => ({
  api: {
    get: vi.fn(),
  },
}))

describe('PlaybooksPage', () => {
  it('renders playbook cards from API data', async () => {
    api.get.mockImplementation(async (url) => {
      if (url === '/playbooks') {
        return {
          data: {
            data: {
              items: [
                {
                  id: 'phishing-detection',
                  name: 'Phishing Detection Playbook',
                  type: 'phishing',
                  success_rate: 95,
                  total_runs: 20,
                  failed_count: 1,
                  steps: ['Receive alert'],
                },
              ],
            },
          },
        }
      }

      return {
        data: {
          data: {
            id: 'phishing-detection',
            name: 'Phishing Detection Playbook',
            mitre_technique: 'T1566',
            total_runs: 20,
            success_count: 19,
            failed_count: 1,
            success_rate: 95,
            steps: ['Receive alert'],
          },
        },
      }
    })

    render(<PlaybooksPage />)

    await waitFor(() => {
      expect(screen.getByText('Phishing Detection Playbook')).toBeInTheDocument()
    })

    expect(screen.getByText('Total Runs')).toBeInTheDocument()
    expect(screen.getByText('Failed Executions')).toBeInTheDocument()
  })
})
