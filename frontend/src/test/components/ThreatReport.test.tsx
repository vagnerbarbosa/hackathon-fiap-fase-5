import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import ThreatReport from '../../components/ThreatReport'

// Mock do fetch global
global.fetch = vi.fn()

global.window.open = vi.fn()

describe('ThreatReport', () => {
  const mockJobId = 'test-job-123'
  const mockOnNewAnalysis = vi.fn()

  const mockReportData = {
    job_id: mockJobId,
    created_at: new Date().toISOString(),
    components: [
      { id: '1', type: 'user', name: 'Usuário' },
      { id: '2', type: 'api', name: 'API Gateway' },
    ],
    threats: [
      {
        id: '1',
        category: 'S' as const,
        title: 'Spoofing de Identidade',
        description: 'Risco de falsificação',
        severity: 'high' as const,
        component: 'API Gateway',
        cwe_id: 'CWE-287',
        cwe_name: 'Improper Authentication',
        countermeasures: ['Implementar MFA']
      }
    ],
    stride_matrix: {
      'API Gateway': [true, false, false, false, false, false],
    }
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Renderização', () => {
    it('deve renderizar o relatório com dados mockados', () => {
      render(
        <ThreatReport
          jobId={mockJobId}
          reportData={mockReportData}
          onNewAnalysis={mockOnNewAnalysis}
        />
      )

      // Usar getAllByText para elementos que aparecem múltiplas vezes
      expect(screen.getByText('Análise Concluída!')).toBeInTheDocument()
      expect(screen.getByText('Exportar')).toBeInTheDocument()

      // Verificar que o Job ID está presente (pode estar em múltiplos lugares)
      const jobIdElements = screen.getAllByText((content) => content.includes(mockJobId))
      expect(jobIdElements.length).toBeGreaterThan(0)
    })

    it('deve renderizar contadores de ameaças corretamente', () => {
      render(
        <ThreatReport
          jobId={mockJobId}
          reportData={mockReportData}
          onNewAnalysis={mockOnNewAnalysis}
        />
      )

      // Verificar cards de contagem de ameaças
      expect(screen.getByText('Ameaças Críticas')).toBeInTheDocument()
      expect(screen.getByText('Ameaças Altas')).toBeInTheDocument()
    })
  })

  describe('Exportação - Fallback', () => {
    it('deve abrir download quando endpoint estiver disponível', async () => {
      // Mock fetch retornando sucesso (200)
      vi.mocked(fetch).mockResolvedValueOnce({
        status: 200,
        ok: true,
      } as Response)

      render(
        <ThreatReport
          jobId={mockJobId}
          reportData={mockReportData}
          onNewAnalysis={mockOnNewAnalysis}
        />
      )

      // Clicar no botão Exportar
      fireEvent.click(screen.getByText('Exportar'))

      // Aguardar menu aparecer
      await waitFor(() => {
        expect(screen.getByText('JSON')).toBeInTheDocument()
      })

      // Clicar em JSON
      fireEvent.click(screen.getByText('JSON'))

      // Verificar se window.open foi chamado
      await waitFor(() => {
        expect(window.open).toHaveBeenCalledWith(
          `/api/v1/threat-model/${mockJobId}/report?format=json`,
          '_blank'
        )
      })
    })

    it('deve mostrar mensagem amigável quando endpoint retornar 404', async () => {
      // Mock fetch retornando 404
      vi.mocked(fetch).mockResolvedValueOnce({
        status: 404,
        ok: false,
      } as Response)

      render(
        <ThreatReport
          jobId={mockJobId}
          reportData={mockReportData}
          onNewAnalysis={mockOnNewAnalysis}
        />
      )

      // Clicar no botão Exportar
      fireEvent.click(screen.getByText('Exportar'))

      // Aguardar menu aparecer
      await waitFor(() => {
        expect(screen.getByText('JSON')).toBeInTheDocument()
      })

      // Clicar em JSON
      fireEvent.click(screen.getByText('JSON'))

      // Verificar se mensagem de erro aparece
      await waitFor(() => {
        expect(screen.getByText(/Exportação em JSON ainda não está disponível/)).toBeInTheDocument()
      })

      // Verificar que window.open NÃO foi chamado
      expect(window.open).not.toHaveBeenCalled()
    })

    it('deve mostrar mensagem amigável quando endpoint retornar 501', async () => {
      // Mock fetch retornando 501 (Not Implemented)
      vi.mocked(fetch).mockResolvedValueOnce({
        status: 501,
        ok: false,
      } as Response)

      render(
        <ThreatReport
          jobId={mockJobId}
          reportData={mockReportData}
          onNewAnalysis={mockOnNewAnalysis}
        />
      )

      // Clicar no botão Exportar
      fireEvent.click(screen.getByText('Exportar'))

      // Aguardar menu aparecer
      await waitFor(() => {
        expect(screen.getByText('PDF')).toBeInTheDocument()
      })

      // Clicar em PDF
      fireEvent.click(screen.getByText('PDF'))

      // Verificar se mensagem de erro aparece
      await waitFor(() => {
        expect(screen.getByText(/Exportação em PDF ainda não está disponível/)).toBeInTheDocument()
      })
    })

    it('deve tentar abrir download mesmo com erro de conexão (fallback)', async () => {
      // Mock fetch lançando erro (ex: CORS, network error)
      vi.mocked(fetch).mockRejectedValueOnce(new Error('Network error'))

      render(
        <ThreatReport
          jobId={mockJobId}
          reportData={mockReportData}
          onNewAnalysis={mockOnNewAnalysis}
        />
      )

      // Clicar no botão Exportar
      fireEvent.click(screen.getByText('Exportar'))

      // Aguardar menu aparecer
      await waitFor(() => {
        expect(screen.getByText('Markdown')).toBeInTheDocument()
      })

      // Clicar em Markdown
      fireEvent.click(screen.getByText('Markdown'))

      // Verificar se window.open foi chamado mesmo com erro (fallback)
      await waitFor(() => {
        expect(window.open).toHaveBeenCalledWith(
          `/api/v1/threat-model/${mockJobId}/report?format=md`,
          '_blank'
        )
      })
    })

    it('deve fechar mensagem de erro ao clicar em Fechar', async () => {
      // Mock fetch retornando 404
      vi.mocked(fetch).mockResolvedValueOnce({
        status: 404,
        ok: false,
      } as Response)

      render(
        <ThreatReport
          jobId={mockJobId}
          reportData={mockReportData}
          onNewAnalysis={mockOnNewAnalysis}
        />
      )

      // Abrir menu e clicar em JSON
      fireEvent.click(screen.getByText('Exportar'))
      await waitFor(() => expect(screen.getByText('JSON')).toBeInTheDocument())
      fireEvent.click(screen.getByText('JSON'))

      // Aguardar mensagem de erro
      await waitFor(() => {
        expect(screen.getByText(/Exportação em JSON ainda não está disponível/)).toBeInTheDocument()
      })

      // Clicar em Fechar
      fireEvent.click(screen.getByText('Fechar'))

      // Verificar que mensagem sumiu
      await waitFor(() => {
        expect(screen.queryByText(/Exportação em JSON ainda não está disponível/)).not.toBeInTheDocument()
      })
    })
  })

  describe('Interação com Ameaças', () => {
    it('deve expandir ameaça ao clicar', () => {
      render(
        <ThreatReport
          jobId={mockJobId}
          reportData={mockReportData}
          onNewAnalysis={mockOnNewAnalysis}
        />
      )

      const threatTitle = screen.getByText('Spoofing de Identidade')
      fireEvent.click(threatTitle)

      // Verificar se contramedidas apareceram
      expect(screen.getByText('Contramedidas OWASP')).toBeInTheDocument()
      expect(screen.getByText('Implementar MFA')).toBeInTheDocument()
    })

    it('deve chamar onNewAnalysis ao clicar em Nova Análise', () => {
      render(
        <ThreatReport
          jobId={mockJobId}
          reportData={mockReportData}
          onNewAnalysis={mockOnNewAnalysis}
        />
      )

      const newAnalysisButton = screen.getByTestId('new-analysis')
      fireEvent.click(newAnalysisButton)

      expect(mockOnNewAnalysis).toHaveBeenCalledTimes(1)
    })
  })
})
