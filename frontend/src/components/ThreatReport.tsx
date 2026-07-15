import { useState, useEffect } from 'react'
import {
  Shield,
  AlertTriangle,
  Download,
  FileJson,
  FileText,
  FileCode,
  FileSpreadsheet,
  FileType,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Loader2
} from 'lucide-react'

interface Threat {
  id: string
  category: 'S' | 'T' | 'R' | 'I' | 'D' | 'E'
  title: string
  description: string
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  component: string
  cwe_id?: string
  cwe_name?: string
  countermeasures: string[]
}

interface Component {
  id: string
  type: string
  name: string
}

interface ReportData {
  job_id: string
  created_at: string
  image_url?: string
  components: Component[]
  threats: Threat[]
  stride_matrix: Record<string, boolean[]>
}

interface ThreatReportProps {
  jobId: string
  reportData?: ReportData
  onNewAnalysis: () => void
}

const STRIDE_CATEGORIES = {
  S: { label: 'Spoofing', color: 'red', bgColor: 'bg-red-500/20', textColor: 'text-red-400', borderColor: 'border-red-500/30' },
  T: { label: 'Tampering', color: 'orange', bgColor: 'bg-orange-500/20', textColor: 'text-orange-400', borderColor: 'border-orange-500/30' },
  R: { label: 'Repudiation', color: 'yellow', bgColor: 'bg-yellow-500/20', textColor: 'text-yellow-400', borderColor: 'border-yellow-500/30' },
  I: { label: 'Info Disclosure', color: 'blue', bgColor: 'bg-blue-500/20', textColor: 'text-blue-400', borderColor: 'border-blue-500/30' },
  D: { label: 'Denial of Service', color: 'purple', bgColor: 'bg-purple-500/20', textColor: 'text-purple-400', borderColor: 'border-purple-500/30' },
  E: { label: 'Elevation of Privilege', color: 'pink', bgColor: 'bg-pink-500/20', textColor: 'text-pink-400', borderColor: 'border-pink-500/30' },
}

const SEVERITY_CONFIG: Record<string, { label: string; color: string; bgColor: string; borderColor: string; icon: React.ComponentType<{ className?: string }> }> = {
  critical: { label: 'Crítica', color: 'text-red-400', bgColor: 'bg-red-500/20', borderColor: 'border-red-500/30', icon: XCircle },
  high: { label: 'Alta', color: 'text-orange-400', bgColor: 'bg-orange-500/20', borderColor: 'border-orange-500/30', icon: AlertTriangle },
  medium: { label: 'Média', color: 'text-yellow-400', bgColor: 'bg-yellow-500/20', borderColor: 'border-yellow-500/30', icon: AlertTriangle },
  low: { label: 'Baixa', color: 'text-blue-400', bgColor: 'bg-blue-500/20', borderColor: 'border-blue-500/30', icon: Shield },
  info: { label: 'Info', color: 'text-slate-400', bgColor: 'bg-slate-500/20', borderColor: 'border-slate-500/30', icon: Shield },
}

const DEFAULT_SEVERITY = { label: 'Desconhecida', color: 'text-slate-400', bgColor: 'bg-slate-500/20', borderColor: 'border-slate-500/30', icon: Shield }

// Mock report data for development
const getMockReportData = (jobId: string): ReportData => ({
  job_id: jobId,
  created_at: new Date().toISOString(),
  components: [
    { id: '1', type: 'user', name: 'Usuário' },
    { id: '2', type: 'api', name: 'API Gateway' },
    { id: '3', type: 'database', name: 'PostgreSQL' },
  ],
  threats: [
    {
      id: '1',
      category: 'S',
      title: 'Spoofing de Identidade',
      description: 'Risco de falsificação de credenciais de usuário no acesso à API',
      severity: 'high',
      component: 'API Gateway',
      cwe_id: 'CWE-287',
      cwe_name: 'Improper Authentication',
      countermeasures: [
        'Implementar autenticação multifator (MFA)',
        'Utilizar tokens JWT com tempo de expiração curto',
        'Implementar rate limiting por IP/usuário'
      ]
    },
    {
      id: '2',
      category: 'T',
      title: 'Tampering de Dados',
      description: 'Possibilidade de modificação não autorizada de dados em trânsito',
      severity: 'critical',
      component: 'PostgreSQL',
      cwe_id: 'CWE-20',
      cwe_name: 'Improper Input Validation',
      countermeasures: [
        'Utilizar TLS 1.3 para comunicação',
        'Implementar assinatura digital de payloads',
        'Validar integridade dos dados no receptor'
      ]
    },
    {
      id: '3',
      category: 'I',
      title: 'Vazamento de Informações',
      description: 'Exposição de dados sensíveis em logs e mensagens de erro',
      severity: 'medium',
      component: 'API Gateway',
      cwe_id: 'CWE-200',
      cwe_name: 'Exposure of Sensitive Information',
      countermeasures: [
        'Sanitizar logs antes de persistir',
        'Implementar mensagens de erro genéricas',
        'Criptografar dados sensíveis em repouso'
      ]
    },
    {
      id: '4',
      category: 'D',
      title: 'Negação de Serviço',
      description: 'Vulnerabilidade a ataques DDoS por falta de rate limiting',
      severity: 'high',
      component: 'API Gateway',
      countermeasures: [
        'Implementar rate limiting por IP',
        'Configurar CDN com proteção DDoS',
        'Adicionar circuit breaker para serviços externos'
      ]
    },
    {
      id: '5',
      category: 'E',
      title: 'Elevação de Privilégios',
      description: 'Possibilidade de escalar privilégios através de injeção SQL',
      severity: 'critical',
      component: 'PostgreSQL',
      cwe_id: 'CWE-89',
      cwe_name: 'SQL Injection',
      countermeasures: [
        'Utilizar prepared statements',
        'Implementar princípio do menor privilégio',
        'Auditar queries sensíveis'
      ]
    },
  ],
  stride_matrix: {
    'Usuário': [true, false, false, true, false, false],
    'API Gateway': [true, true, true, true, true, true],
    'PostgreSQL': [false, true, false, true, true, true],
  }
})

export default function ThreatReport({ jobId, reportData, onNewAnalysis }: ThreatReportProps) {
  const [expandedThreat, setExpandedThreat] = useState<string | null>(null)
  const [exportMenuOpen, setExportMenuOpen] = useState(false)
  const [exportError, setExportError] = useState<string | null>(null)
  const [isExporting, setIsExporting] = useState(false)
  const [apiData, setApiData] = useState<ReportData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Buscar dados da API
  useEffect(() => {
    const fetchReport = async () => {
      try {
        // API Key é adicionada pelo proxy reverso (nginx)
        const response = await fetch(`/api/v1/threat-model/${jobId}/report?format=json`, {
          headers: { 'Accept': 'application/json' }
        })
        if (!response.ok) {
          if (response.status === 401 || response.status === 403) {
            throw new Error('Erro de autenticação')
          }
          throw new Error(`Erro ${response.status}: Falha ao carregar relatório`)
        }
        const data = await response.json()

        // Converter dados da API para formato do componente
        const converted: ReportData = {
          job_id: data.job_id,
          created_at: new Date().toISOString(),
          components: data.threats?.map((t: any) => ({
            id: t.id,
            type: t.component_type,
            name: t.component_type
          })) || [],
          threats: data.threats?.map((t: any) => ({
            id: t.id,
            category: t.category,
            title: t.category_name,
            description: t.description,
            severity: t.severity,
            component: t.component_type,
            cwe_id: t.cwe_id,
            cwe_name: t.cwe_name,
            countermeasures: t.countermeasures?.map((c: any) => c.title) || []
          })) || [],
          stride_matrix: {}
        }

        // Construir matriz STRIDE
        const componentTypes: string[] = data.threats?.map((t: any) => String(t.component_type)) || []
        const uniqueComponents: string[] = Array.from(new Set(componentTypes))
        uniqueComponents.forEach((comp: string) => {
          const compThreats = data.threats?.filter((t: any) => String(t.component_type) === comp) || []
          converted.stride_matrix[comp] = ['S', 'T', 'R', 'I', 'D', 'E'].map((cat: string) =>
            compThreats.some((t: any) => String(t.category) === cat)
          )
        })

        setApiData(converted)
      } catch (err) {
        setError('Usando dados de demonstração')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    fetchReport()
  }, [jobId])

  const data = apiData || reportData || getMockReportData(jobId)
  const threatsByCategory = Object.keys(STRIDE_CATEGORIES).map(cat => ({
    category: cat as keyof typeof STRIDE_CATEGORIES,
    threats: data.threats.filter(t => t.category === cat),
    count: data.threats.filter(t => t.category === cat).length
  }))

  const criticalCount = data.threats.filter(t => t.severity === 'critical').length
  const highCount = data.threats.filter(t => t.severity === 'high').length
  const mediumCount = data.threats.filter(t => t.severity === 'medium').length
  const lowCount = data.threats.filter(t => t.severity === 'low' || t.severity === 'info').length

  const handleExport = async (format: string) => {
    setIsExporting(true)
    setExportError(null)

    try {
      // Para HTML, abrir em nova aba
      if (format === 'html') {
        window.open(`/api/v1/threat-model/${jobId}/report?format=html`, '_blank')
        setExportMenuOpen(false)
        setIsExporting(false)
        return
      }

      // Fazer download via fetch (API key adicionada pelo proxy)
      const response = await fetch(`/api/v1/threat-model/${jobId}/report?format=${format}`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json'
        }
      })

      // Tratar erros de autenticação ou endpoint não implementado
      if (response.status === 404 || response.status === 501 || response.status === 401 || response.status === 403) {
        setExportError(`Exportação em ${format.toUpperCase()} ainda não está disponível.`)
        setExportMenuOpen(false)
        return
      }

      if (!response.ok) {
        setExportError(`Erro ao exportar em ${format.toUpperCase()}: ${response.statusText}`)
        setExportMenuOpen(false)
        return
      }

      // Obter o blob da resposta
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)

      // Criar link temporário para download
      const link = document.createElement('a')
      link.href = url

      // Definir nome do arquivo baseado no formato
      const filename = `relatorio-${jobId}.${format === 'md' ? 'md' : format}`
      link.download = filename

      // Trigger do download
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)

      // Limpar URL
      window.URL.revokeObjectURL(url)
      setExportMenuOpen(false)
    } catch (error) {
      // Erro de conexão ou CORS
      setExportError(`Exportação em ${format.toUpperCase()} ainda não está disponível.`)
      setExportMenuOpen(false)
    } finally {
      setIsExporting(false)
    }
  }

  const clearExportError = () => setExportError(null)

  // Mostrar loading enquanto busca dados
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Loader2 className="w-8 h-8 text-fiap-pink animate-spin mb-4" />
        <p className="text-slate-400">Carregando relatório...</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Alerta de dados mockados ou erro */}
      {(error || !apiData) && (
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-amber-200 font-medium text-sm">
                {error ? 'Usando dados de demonstração' : 'Relatório de Demonstração'}
              </p>
              <p className="text-amber-200/70 text-sm mt-1">
                {error || 'Os dados exibidos são simulados. O relatório real será gerado quando a API retornar dados.'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Header com informações do relatório */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <CheckCircle2 className="w-6 h-6 text-emerald-400" />
              <h2 className="text-2xl font-bold text-white">Análise Concluída!</h2>
            </div>
            <p className="text-slate-400">
              Job ID: <span className="text-slate-300 font-mono text-sm">{jobId}</span>
            </p>
            <p className="text-slate-500 text-sm mt-1">
              Gerado em: {new Date(data.created_at).toLocaleString('pt-BR')}
            </p>
          </div>

          {/* Botões de ação */}
          <div className="flex flex-wrap gap-3">
            {/* Alerta de erro de exportação */}
            {exportError && (
              <div className="absolute top-full right-0 mt-2 w-80 bg-amber-500/10 border border-amber-500/30 rounded-lg p-4 shadow-lg z-20">
                <div className="flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-amber-200 text-sm">{exportError}</p>
                    <button
                      onClick={clearExportError}
                      className="text-amber-400 text-xs hover:text-amber-300 mt-2 underline"
                    >
                      Fechar
                    </button>
                  </div>
                </div>
              </div>
            )}
            {/* Menu de exportação */}
            <div className="relative">
              <button
                onClick={() => setExportMenuOpen(!exportMenuOpen)}
                disabled={isExporting}
                aria-expanded={exportMenuOpen}
                aria-haspopup="menu"
                aria-label="Abrir menu de exportação"
                className="flex items-center gap-2 px-4 py-2 bg-fiap-pink hover:bg-fiap-pink/80 disabled:bg-fiap-pink/50 text-white rounded-lg font-medium transition-colors"
              >
                {isExporting ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" aria-hidden="true" />
                    Verificando...
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4" aria-hidden="true" />
                    Exportar
                    {exportMenuOpen ? <ChevronUp className="w-4 h-4" aria-hidden="true" /> : <ChevronDown className="w-4 h-4" aria-hidden="true" />}
                  </>
                )}
              </button>

              {exportMenuOpen && (
                <div
                  className="absolute right-0 mt-2 w-48 bg-slate-800 border border-slate-700 rounded-lg shadow-lg z-10"
                  role="menu"
                  aria-label="Opções de exportação"
                >
                  <button
                    disabled={isExporting}
                    onClick={() => handleExport('json')}
                    role="menuitem"
                    aria-label="Exportar em formato JSON"
                    className="flex items-center gap-2 w-full px-4 py-2 text-left text-slate-300 hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <FileJson className="w-4 h-4 text-blue-400" aria-hidden="true" /> JSON
                  </button>
                  <button
                    disabled={isExporting}
                    onClick={() => handleExport('md')}
                    role="menuitem"
                    aria-label="Exportar em formato Markdown"
                    className="flex items-center gap-2 w-full px-4 py-2 text-left text-slate-300 hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <FileText className="w-4 h-4 text-slate-400" aria-hidden="true" /> Markdown
                  </button>
                  <button
                    disabled={isExporting}
                    onClick={() => handleExport('html')}
                    role="menuitem"
                    aria-label="Exportar em formato HTML"
                    className="flex items-center gap-2 w-full px-4 py-2 text-left text-slate-300 hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <FileCode className="w-4 h-4 text-orange-400" aria-hidden="true" /> HTML
                  </button>
                  <button
                    disabled={isExporting}
                    onClick={() => handleExport('csv')}
                    role="menuitem"
                    aria-label="Exportar em formato CSV"
                    className="flex items-center gap-2 w-full px-4 py-2 text-left text-slate-300 hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <FileSpreadsheet className="w-4 h-4 text-green-400" aria-hidden="true" /> CSV
                  </button>
                  <button
                    disabled={isExporting}
                    onClick={() => handleExport('pdf')}
                    role="menuitem"
                    aria-label="Exportar em formato PDF"
                    className="flex items-center gap-2 w-full px-4 py-2 text-left text-slate-300 hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <FileType className="w-4 h-4 text-red-400" aria-hidden="true" /> PDF
                  </button>
                </div>
              )}
            </div>

            <button
              data-testid="new-analysis"
              onClick={onNewAnalysis}
              aria-label="Iniciar nova análise"
              className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-medium transition-colors"
            >
              Nova Análise
            </button>
          </div>
        </div>
      </div>

      {/* Cards de resumo */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4" role="region" aria-label="Resumo de ameaças por severidade">
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-1">
            <XCircle className="w-5 h-5 text-red-400" aria-hidden="true" />
            <span className="text-red-400 font-semibold" aria-label={`${criticalCount} ameaças críticas`}>{criticalCount}</span>
          </div>
          <span className="text-slate-400 text-sm">Ameaças Críticas</span>
        </div>
        <div className="bg-orange-500/10 border border-orange-500/30 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-1">
            <AlertTriangle className="w-5 h-5 text-orange-400" aria-hidden="true" />
            <span className="text-orange-400 font-semibold" aria-label={`${highCount} ameaças altas`}>{highCount}</span>
          </div>
          <span className="text-slate-400 text-sm">Ameaças Altas</span>
        </div>
        <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-1">
            <Shield className="w-5 h-5 text-yellow-400" aria-hidden="true" />
            <span className="text-yellow-400 font-semibold" aria-label={`${mediumCount} ameaças médias`}>{mediumCount}</span>
          </div>
          <span className="text-slate-400 text-sm">Ameaças Médias</span>
        </div>
        <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-1">
            <Shield className="w-5 h-5 text-blue-400" aria-hidden="true" />
            <span className="text-blue-400 font-semibold" aria-label={`${lowCount} ameaças baixas`}>{lowCount}</span>
          </div>
          <span className="text-slate-400 text-sm">Ameaças Baixas</span>
        </div>
      </div>

      {/* Matriz STRIDE */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-6">
        <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <Shield className="w-5 h-5 text-fiap-pink" />
          Matriz STRIDE
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full" role="table" aria-label="Matriz de ameaças STRIDE por componente">
            <thead>
              <tr className="border-b border-slate-700">
                <th scope="col" className="text-left py-3 px-4 text-slate-400 font-medium">Componente</th>
                {Object.entries(STRIDE_CATEGORIES).map(([key, config]) => (
                  <th key={key} scope="col" className="text-center py-3 px-2">
                    <div className={`inline-flex flex-col items-center p-2 rounded-lg ${config.bgColor} ${config.borderColor} border`}>
                      <span className={`text-lg font-bold ${config.textColor}`}>{key}</span>
                      <span className={`text-xs ${config.textColor} opacity-80`}>{config.label.split(' ')[0]}</span>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {Object.entries(data.stride_matrix).map(([component, values]) => (
                <tr key={component} className="border-b border-slate-700/50 last:border-0">
                  <td className="py-3 px-4 text-slate-300 font-medium">{component}</td>
                  {values.map((hasThreat, idx) => (
                    <td key={idx} className="text-center py-3 px-2">
                      {hasThreat ? (
                        <div className="inline-flex items-center justify-center w-8 h-8 bg-fiap-pink/20 rounded-full">
                          <AlertTriangle className="w-4 h-4 text-fiap-pink" />
                        </div>
                      ) : (
                        <div className="inline-flex items-center justify-center w-8 h-8">
                          <span className="text-slate-600">-</span>
                        </div>
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Lista de Ameaças */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-6">
        <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-fiap-pink" />
          Ameaças Identificadas ({data.threats.length})
        </h3>

        <div className="space-y-4">
          {threatsByCategory.map(({ category, threats, count }) => {
            if (count === 0) return null
            const config = STRIDE_CATEGORIES[category]

            return (
              <div key={category} className={`border ${config.borderColor} rounded-xl overflow-hidden`}>
                <div className={`${config.bgColor} px-4 py-3 flex items-center justify-between`}>
                  <div className="flex items-center gap-3">
                    <span className={`text-lg font-bold ${config.textColor}`}>{category}</span>
                    <span className={`font-medium ${config.textColor}`}>{config.label}</span>
                    <span className="bg-slate-800/50 text-slate-300 px-2 py-0.5 rounded-full text-sm">{count}</span>
                  </div>
                </div>

                <div className="divide-y divide-slate-700/50">
                  {threats.map((threat) => {
                    const severity = SEVERITY_CONFIG[threat.severity] || DEFAULT_SEVERITY
                    const isExpanded = expandedThreat === threat.id
                    const Icon = severity.icon

                    return (
                      <div key={threat.id} className="p-4 hover:bg-slate-700/30 transition-colors">
                        <div
                          className="flex items-start justify-between cursor-pointer"
                          onClick={() => setExpandedThreat(isExpanded ? null : threat.id)}
                        >
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${severity.bgColor} ${severity.color} border ${severity.borderColor}`}>
                                <Icon className="w-3 h-3" />
                                {severity.label}
                              </span>
                              <span className="text-slate-400 text-sm">{threat.component}</span>
                            </div>
                            <h4 className="text-white font-semibold mb-1">{threat.title}</h4>
                            <p className="text-slate-400 text-sm">{threat.description}</p>

                            {threat.cwe_id && (
                              <div className="mt-2 flex items-center gap-2">
                                <span className="text-xs bg-slate-700 text-slate-300 px-2 py-1 rounded">
                                  {threat.cwe_id}
                                </span>
                                <span className="text-slate-500 text-xs">{threat.cwe_name}</span>
                              </div>
                            )}
                          </div>

                          <button
                            className="text-slate-400 hover:text-white transition-colors ml-4"
                            aria-label={isExpanded ? "Recolher detalhes da ameaça" : "Expandir detalhes da ameaça"}
                            aria-expanded={isExpanded}
                          >
                            {isExpanded ? <ChevronUp className="w-5 h-5" aria-hidden="true" /> : <ChevronDown className="w-5 h-5" aria-hidden="true" />}
                          </button>
                        </div>

                        {isExpanded && threat.countermeasures.length > 0 && (
                          <div className="mt-4 pt-4 border-t border-slate-700/50">
                            <h5 className="text-sm font-medium text-slate-300 mb-2 flex items-center gap-2">
                              <Shield className="w-4 h-4 text-emerald-400" />
                              Contramedidas OWASP
                            </h5>
                            <ul className="space-y-2">
                              {threat.countermeasures.map((measure, idx) => (
                                <li key={idx} className="flex items-start gap-2 text-sm text-slate-400">
                                  <span className="text-emerald-400 mt-1">✓</span>
                                  {measure}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
