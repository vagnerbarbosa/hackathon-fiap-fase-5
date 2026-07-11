import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from '../App'

// Mock do fetch global
const mockFetch = vi.fn()
global.fetch = mockFetch

describe('App Integration', () => {
  beforeEach(() => {
    mockFetch.mockClear()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Busca de Versão', () => {
    it('deve buscar e exibir a versão do sistema ao carregar', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ version: '0.2.0' }),
      })

      render(<App />)

      await waitFor(() => {
        expect(screen.getByTestId('system-version')).toHaveTextContent('v0.2.0')
      })
    })

    it('deve tentar endpoint direto se proxy falhar', async () => {
      mockFetch
        .mockRejectedValueOnce(new Error('Proxy failed'))
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ version: '0.2.0' }),
        })

      render(<App />)

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(2)
      })
    })

    it('deve lidar com falha completa na busca de versão', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'))

      render(<App />)

      // Aguarda um momento para garantir que o erro foi tratado
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled()
      })
    })
  })

  describe('Navegação entre Tabs', () => {
    it('deve iniciar na tab de upload', () => {
      render(<App />)

      expect(screen.getByText('Upload de Diagrama de Arquitetura')).toBeInTheDocument()
    })

    it('deve navegar para tab Sobre ao clicar', async () => {
      render(<App />)

      const sobreButton = screen.getByText('Sobre')
      await userEvent.click(sobreButton)

      expect(screen.getByText('Sobre o Projeto')).toBeInTheDocument()
    })

    it('deve voltar para tab Análise ao clicar', async () => {
      render(<App />)

      await userEvent.click(screen.getByText('Sobre'))
      await userEvent.click(screen.getByText('Análise'))

      expect(screen.getByText('Upload de Diagrama de Arquitetura')).toBeInTheDocument()
    })
  })

  describe('Upload de Arquivo', () => {
    beforeEach(() => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ version: '0.2.0' }),
      })
    })

    it('deve permitir seleção de arquivo', async () => {
      render(<App />)

      const file = new File(['test content'], 'diagrama.png', { type: 'image/png' })
      const input = document.querySelector('input[type="file"]') as HTMLInputElement

      await userEvent.upload(input, file)

      await waitFor(() => {
        expect(screen.getByTestId('filename')).toHaveTextContent('diagrama.png')
      })
    })

    it('deve mostrar botões após seleção de arquivo', async () => {
      render(<App />)

      const file = new File(['test'], 'diagrama.png', { type: 'image/png' })
      const input = document.querySelector('input[type="file"]') as HTMLInputElement

      await userEvent.upload(input, file)

      await waitFor(() => {
        expect(screen.getByTestId('start-analysis')).toBeInTheDocument()
        expect(screen.getByTestId('change-file')).toBeInTheDocument()
      })
    })

    it('deve mostrar tamanho do arquivo em MB', async () => {
      render(<App />)

      const file = new File(['test'], 'diagrama.png', { type: 'image/png' })
      const input = document.querySelector('input[type="file"]') as HTMLInputElement

      await userEvent.upload(input, file)

      await waitFor(() => {
        expect(screen.getByTestId('filesize')).toBeInTheDocument()
      })
    })

    it('deve permitir trocar arquivo após seleção', async () => {
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

  describe('Seção STRIDE', () => {
    it('deve exibir explicação do STRIDE', () => {
      render(<App />)

      expect(screen.getByText('O que é STRIDE?')).toBeInTheDocument()
      expect(screen.getByText('S')).toBeInTheDocument()
      expect(screen.getByText('Spoofing')).toBeInTheDocument()
      expect(screen.getByText('T')).toBeInTheDocument()
      expect(screen.getByText('Tampering')).toBeInTheDocument()
    })

    it('deve exibir todas as categorias do STRIDE', () => {
      render(<App />)

      const categories = [
        'Spoofing',
        'Tampering',
        'Repudiation',
        'Information Disclosure',
        'Denial of Service',
        'Elevation of Privilege',
      ]

      categories.forEach((category) => {
        expect(screen.getByText(category)).toBeInTheDocument()
      })
    })
  })

  describe('Sobre o Projeto', () => {
    it('deve exibir informações do projeto', async () => {
      render(<App />)

      await userEvent.click(screen.getByText('Sobre'))

      expect(screen.getByText('Sobre o Projeto')).toBeInTheDocument()
      expect(screen.getByText(/solução inovadora/)).toBeInTheDocument()
    })

    it('deve exibir integrantes do grupo', async () => {
      render(<App />)

      await userEvent.click(screen.getByText('Sobre'))

      expect(screen.getByText('Adriel Santos')).toBeInTheDocument()
      expect(screen.getByText('Leticia Nepomuceno')).toBeInTheDocument()
      expect(screen.getByText('Lucas Silva')).toBeInTheDocument()
      expect(screen.getByText('Vagner Barbosa')).toBeInTheDocument()
    })

    it('deve exibir tecnologias utilizadas', async () => {
      render(<App />)

      await userEvent.click(screen.getByText('Sobre'))

      expect(screen.getByText('Tecnologias Utilizadas')).toBeInTheDocument()
    })
  })

  describe('Rodapé', () => {
    it('deve exibir copyright', () => {
      render(<App />)

      expect(screen.getByText('© 2026 Grupo 27')).toBeInTheDocument()
    })

    it('deve exibir mensagem de privacidade', () => {
      render(<App />)

      expect(screen.getByText(/não coleta dados pessoais/i)).toBeInTheDocument()
    })
  })
})
