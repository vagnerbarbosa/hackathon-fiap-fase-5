import { useState } from 'react'
import {
  Shield,
  AlertTriangle,
  Download,
  FileJson,
  FileText,
  FileCode,
  FileSpreadsheet,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  XCircle
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

const SEVERITY_CONFIG = {
  critical: { label: 'Crítica', color: 'text-red-400', bgColor: 'bg-red-500/20', borderColor: 'border-red-500/30', icon: XCircle },
  high: { label: 'Alta', color: 'text-orange-400', bgColor: 'bg-orange-500/20', borderColor: 'border-orange-500/30', icon: AlertTriangle },
  medium: { label: 'Média', color: 'text-yellow-400', bgColor: 'bg-yellow-500/20', borderColor: 'border-yellow-500/30', icon: AlertTriangle },
  low: { label: 'Baixa', color: 'text-blue-400', bgColor: 'bg-blue-500/20', borderColor: 'border-blue-500/30', icon: Shield },
  info: { label: 'Info', color: 'text-slate-400', bgColor: 'bg-slate-500/20', borderColor: 'border-slate-500/30', icon: Shield },
}

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

  const data = reportData || getMockReportData(jobId)
  const threatsByCategory = Object.keys(STRIDE_CATEGORIES).map(cat => ({
    category: cat as keyof typeof STRIDE_CATEGORIES,
    threats: data.threats.filter(t => t.category === cat),
    count: data.threats.filter(t => t.category === cat).length
  }))

  const criticalCount = data.threats.filter(t => t.severity === 'critical').length
  const highCount = data.threats.filter(t => t.severity === 'high').length
  const mediumCount = data.threats.filter(t => t.severity === 'medium').length
  const lowCount = data.threats.filter(t => t.severity === 'low' || t.severity === 'info').length

  const handleExport = (format: string) => {
    window.open(`/api/v1/threat-model/${jobId}/report?format=${format}`, '_blank')
    setExportMenuOpen(false)
  }

  return (
    <div className="space-y-6">
      {/* Header com informações do relatório */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <CheckCircle2 className="w-6 h-6 text-emerald-400" />
              <h2 className="text-2xl font-bold text-white">Análise Concluída</h2>
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
            {/* Menu de exportação */}
            <div className="relative">
              <button
                onClick={() => setExportMenuOpen(!exportMenuOpen)}
                className="flex items-center gap-2 px-4 py-2 bg-fiap-pink hover:bg-fiap-pink/80 text-white rounded-lg font-medium transition-colors"
              >
                <Download className="w-4 h-4" />
                Exportar
                {exportMenuOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </button>

              {exportMenuOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-slate-800 border border-slate-700 rounded-lg shadow-lg z-10">
                  <button onClick={() => handleExport('json')} className="flex items-center gap-2 w-full px-4 py-2 text-left text-slate-300 hover:bg-slate-700 transition-colors">
                    <FileJson className="w-4 h-4 text-blue-400" /> JSON
                  </button>
                  <button onClick={() => handleExport('md')} className="flex items-center gap-2 w-full px-4 py-2 text-left text-slate-300 hover:bg-slate-700 transition-colors">
                    <FileText className="w-4 h-4 text-slate-400" /> Markdown
                  </button>
                  <button onClick={() => handleExport('html')} className="flex items-center gap-2 w-full px-4 py-2 text-left text-slate-300 hover:bg-slate-700 transition-colors">
                    <FileCode className="w-4 h-4 text-orange-400" /> HTML
                  </button>
                  <button onClick={() => handleExport('csv')} className="flex items-center gap-2 w-full px-4 py-2 text-left text-slate-300 hover:bg-slate-700 transition-colors">
                    <FileSpreadsheet className="w-4 h-4 text-green-400" /> CSV
                  </button>
                </div>
              )}
            </div>

            <button
              onClick={onNewAnalysis}
              className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-medium transition-colors"
            >
              Nova Análise
            </button>
          </div>
        </div>
      </div>

      {/* Cards de resumo */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-1">
            <XCircle className="w-5 h-5 text-red-400" />
            <span className="text-red-400 font-semibold">{criticalCount}</span>
          </div>
          <span className="text-slate-400 text-sm">Ameaças Críticas</span>
        </div>
        <div className="bg-orange-500/10 border border-orange-500/30 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-1">
            <AlertTriangle className="w-5 h-5 text-orange-400" />
            <span className="text-orange-400 font-semibold">{highCount}</span>
          </div>
          <span className="text-slate-400 text-sm">Ameaças Altas</span>
        </div>
        <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-1">
            <Shield className="w-5 h-5 text-yellow-400" />
            <span className="text-yellow-400 font-semibold">{mediumCount}</span>
          </div>
          <span className="text-slate-400 text-sm">Ameaças Médias</span>
        </div>
        <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-1">
            <Shield className="w-5 h-5 text-blue-400" />
            <span className="text-blue-400 font-semibold">{lowCount}</span>
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
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left py-3 px-4 text-slate-400 font-medium">Componente</th>
                {Object.entries(STRIDE_CATEGORIES).map(([key, config]) => (
                  <th key={key} className="text-center py-3 px-2">
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
                    const severity = SEVERITY_CONFIG[threat.severity]
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

                          <button className="text-slate-400 hover:text-white transition-colors ml-4">
                            {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
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
