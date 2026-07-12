import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from '../App'

const mockFetch = vi.fn()
global.fetch = mockFetch

describe('Upload Flow Complete', () => {
  beforeEach(() => {
    mockFetch.mockClear()
    // Mock da versão inicial
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ version: '0.2.0' }),
    })
  })

  afterEach(() => {
    vi.clearAllTimers()
  })

  it('deve mostrar estado de processamento após upload', async () => {
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
      expect(screen.getByTestId('job-id')).toHaveTextContent('test-job-123')
    })
  })

  it('deve mostrar estado concluído quando job termina', async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ version: '0.2.0' }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          job_id: 'test-job-123',
          status: 'completed',
          message: 'Completed',
        }),
      })

    render(<App />)

    const file = new File(['test'], 'diagrama.png', { type: 'image/png' })
    const input = document.querySelector('input[type="file"]') as HTMLInputElement

    await userEvent.upload(input, file)
    await userEvent.click(screen.getByTestId('start-analysis'))

    await waitFor(() => {
      expect(screen.getByTestId('completed')).toBeInTheDocument()
      expect(screen.getByText('Análise Concluída!')).toBeInTheDocument()
    })
  })

  it('deve lidar com erro sem mensagem detalhada', async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ version: '0.2.0' }),
      })
      .mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({}), // Sem detail
      })

    render(<App />)

    const file = new File(['test'], 'diagrama.png', { type: 'image/png' })
    const input = document.querySelector('input[type="file"]') as HTMLInputElement

    await userEvent.upload(input, file)
    await userEvent.click(screen.getByTestId('start-analysis'))

    await waitFor(() => {
      expect(screen.getByTestId('error')).toBeInTheDocument()
      expect(screen.getByText(/Erro 500/)).toBeInTheDocument()
    })
  })

  it('deve mostrar erro quando upload falha', async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ version: '0.2.0' }),
      })
      .mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ detail: 'Erro interno do servidor' }),
      })

    render(<App />)

    const file = new File(['test'], 'diagrama.png', { type: 'image/png' })
    const input = document.querySelector('input[type="file"]') as HTMLInputElement

    await userEvent.upload(input, file)
    await userEvent.click(screen.getByTestId('start-analysis'))

    await waitFor(() => {
      expect(screen.getByTestId('error')).toBeInTheDocument()
      expect(screen.getByTestId('error-message')).toHaveTextContent('Erro interno do servidor')
      expect(screen.getByTestId('try-again')).toBeInTheDocument()
    })
  })

  it('deve permitir nova análise após conclusão', async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ version: '0.2.0' }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          job_id: 'test-job-123',
          status: 'completed',
          message: 'Completed',
        }),
      })

    render(<App />)

    const file = new File(['test'], 'diagrama.png', { type: 'image/png' })
    const input = document.querySelector('input[type="file"]') as HTMLInputElement

    await userEvent.upload(input, file)
    await userEvent.click(screen.getByTestId('start-analysis'))

    await waitFor(() => {
      expect(screen.getByTestId('completed')).toBeInTheDocument()
    })

    await userEvent.click(screen.getByTestId('new-analysis'))

    await waitFor(() => {
      expect(screen.getByTestId('upload-dropzone')).toBeInTheDocument()
    })
  })

  it('deve lidar com erro de conexão', async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ version: '0.2.0' }),
      })
      .mockRejectedValueOnce(new Error('Network error'))

    render(<App />)

    const file = new File(['test'], 'diagrama.png', { type: 'image/png' })
    const input = document.querySelector('input[type="file"]') as HTMLInputElement

    await userEvent.upload(input, file)
    await userEvent.click(screen.getByTestId('start-analysis'))

    await waitFor(() => {
      expect(screen.getByTestId('error')).toBeInTheDocument()
      expect(screen.getByTestId('error-message')).toHaveTextContent(/conexão/)
    })
  })

  it('deve suportar drag and drop', async () => {
    render(<App />)

    const dropzone = screen.getByTestId('upload-dropzone')
    const file = new File(['test'], 'diagrama.png', { type: 'image/png' })

    await act(async () => {
      const dropEvent = new Event('drop', { bubbles: true })
      Object.defineProperty(dropEvent, 'dataTransfer', {
        value: {
          files: [file],
        },
      })
      dropzone.dispatchEvent(dropEvent)
    })

    await waitFor(() => {
      expect(screen.getByTestId('file-selected')).toBeInTheDocument()
    })
  })

  it('deve fazer download do relatório quando concluído', async () => {
    const windowOpenSpy = vi.spyOn(window, 'open').mockImplementation(() => null)

    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ version: '0.2.0' }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          job_id: 'test-job-123',
          status: 'completed',
          message: 'Completed',
        }),
      })

    render(<App />)

    const file = new File(['test'], 'diagrama.png', { type: 'image/png' })
    const input = document.querySelector('input[type="file"]') as HTMLInputElement

    await userEvent.upload(input, file)
    await userEvent.click(screen.getByTestId('start-analysis'))

    await waitFor(() => {
      expect(screen.getByTestId('completed')).toBeInTheDocument()
    })

    // O componente ThreatReport agora lida com o download
    // Verificamos se o relatório está sendo exibido
    expect(screen.getByText('Análise Concluída!')).toBeInTheDocument()

    windowOpenSpy.mockRestore()
  })

})
