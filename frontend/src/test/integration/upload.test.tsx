import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from '../../App'

const mockFetch = vi.fn()
global.fetch = mockFetch

describe('Upload Flow Integration', () => {
  beforeEach(() => {
    mockFetch.mockClear()
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ version: '0.2.0' }),
    })
  })

  it('deve permitir selecionar arquivo e mostrar preview', async () => {
    render(<App />)

    const file = new File(['test'], 'diagrama.png', { type: 'image/png' })
    const input = document.querySelector('input[type="file"]') as HTMLInputElement

    await userEvent.upload(input, file)

    await waitFor(() => {
      expect(screen.getByTestId('file-selected')).toBeInTheDocument()
      expect(screen.getByTestId('filename')).toHaveTextContent('diagrama.png')
    })
  })

  it('deve permitir reset após seleção', async () => {
    render(<App />)

    const file = new File(['test'], 'diagrama.png', { type: 'image/png' })
    const input = document.querySelector('input[type="file"]') as HTMLInputElement

    await userEvent.upload(input, file)

    await waitFor(() => {
      expect(screen.getByTestId('change-file')).toBeInTheDocument()
    })

    await userEvent.click(screen.getByTestId('change-file'))

    await waitFor(() => {
      expect(screen.getByTestId('upload-dropzone')).toBeInTheDocument()
    })
  })
})
