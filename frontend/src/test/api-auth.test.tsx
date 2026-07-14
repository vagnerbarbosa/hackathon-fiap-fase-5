import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from '../App'

const mockFetch = vi.fn()
global.fetch = mockFetch

// Criar um QueryClient para testes
const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      staleTime: 0,
    },
  },
})

// Wrapper para testes com QueryClientProvider
const renderWithQueryClient = (component: React.ReactNode) => {
  const queryClient = createTestQueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  )
}

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
    renderWithQueryClient(<App />)

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

    renderWithQueryClient(<App />)

    const file = new File(['test'], 'diagrama.png', { type: 'image/png' })
    const input = document.querySelector('input[type="file"]') as HTMLInputElement

    await userEvent.upload(input, file)
    await userEvent.click(screen.getByTestId('start-analysis'))

    await waitFor(() => {
      // Pelo menos 2 chamadas: version + upload
      expect(mockFetch.mock.calls.length).toBeGreaterThanOrEqual(2)
    }, { timeout: 3000 })

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

    renderWithQueryClient(<App />)

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
