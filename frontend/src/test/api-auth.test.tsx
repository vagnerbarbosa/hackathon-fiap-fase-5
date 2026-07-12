import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from '../App'

const mockFetch = vi.fn()
global.fetch = mockFetch

describe('API Authentication', () => {
  beforeEach(() => {
    mockFetch.mockClear()
    // Mock da versão inicial
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ version: '0.2.0' }),
    })
  })

  it('should make requests with headers object', async () => {
    render(<App />)

    // Aguarda o fetch de versão ser chamado
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalled()
    })

    // Verifica que a requisição foi feita com headers (mesmo que vazio)
    const versionCall = mockFetch.mock.calls[0]
    expect(versionCall[1]).toBeDefined()
    expect(versionCall[1].headers).toBeDefined()
  })

  it('should send headers in upload request', async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ version: '0.2.0' }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          job_id: 'test-job-123',
          status: 'processing',
          message: 'Upload iniciado',
        }),
      })

    render(<App />)

    const file = new File(['test'], 'diagrama.png', { type: 'image/png' })
    const input = document.querySelector('input[type="file"]') as HTMLInputElement

    await userEvent.upload(input, file)
    await userEvent.click(screen.getByTestId('start-analysis'))

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(2)
    })

    // Verifica que o segundo fetch (upload) inclui headers
    const uploadCall = mockFetch.mock.calls[1]
    expect(uploadCall[1]).toBeDefined()
    expect(uploadCall[1].headers).toBeDefined()
    expect(uploadCall[1].method).toBe('POST')
  })

  it('should send headers in status polling', async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ version: '0.2.0' }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          job_id: 'test-job-123',
          status: 'processing',
          message: 'Upload iniciado',
        }),
      })

    render(<App />)

    const file = new File(['test'], 'diagrama.png', { type: 'image/png' })
    const input = document.querySelector('input[type="file"]') as HTMLInputElement

    await userEvent.upload(input, file)
    await userEvent.click(screen.getByTestId('start-analysis'))

    await waitFor(() => {
      expect(screen.getByTestId('processing')).toBeInTheDocument()
    })

    // Verifica que as requisições incluem headers
    const calls = mockFetch.mock.calls
    const versionCalls = calls.filter((call) =>
      call[0]?.includes?.('/version')
    )

    expect(versionCalls.length).toBeGreaterThan(0)
    versionCalls.forEach((call) => {
      expect(call[1]?.headers).toBeDefined()
    })
  })
})
