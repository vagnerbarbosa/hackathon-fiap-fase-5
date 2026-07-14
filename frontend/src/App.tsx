import { useState, useRef, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Shield, Upload, Info, AlertTriangle, Github, FileImage, Loader2, XCircle } from 'lucide-react'
import StrideCard from './components/StrideCard'
import TechBadge from './components/TechBadge'
import ThreatReport from './components/ThreatReport'
import './App.css'

// API Key é adicionada pelo proxy reverso (nginx) - não exposta no frontend
const createHeaders = (contentType?: string): HeadersInit => {
  const headers: HeadersInit = {}
  if (contentType) {
    headers['Content-Type'] = contentType
  }
  return headers
}

// Tipos para a resposta da API
interface UploadResponse {
  job_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  message: string
}

interface JobStatusResponse {
  job_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress?: number
  result?: {
    threats_count: number
    report_url: string
  }
  error?: string
}

// API functions
const fetchSystemVersion = async (): Promise<string> => {
  try {
    const response = await fetch('/version', { headers: createHeaders() })
    if (response.ok) {
      const data = await response.json()
      return data.version
    }
  } catch {
    // Fallback para porta direta
    try {
      const response = await fetch('http://localhost:8001/version', { headers: createHeaders() })
      if (response.ok) {
        const data = await response.json()
        return data.version
      }
    } catch {
      // Silenciar erro em produção
    }
  }
  return ''
}

const fetchJobStatus = async (jobId: string): Promise<JobStatusResponse> => {
  const response = await fetch(`/api/v1/threat-model/${jobId}`, {
    headers: createHeaders(),
  })
  if (!response.ok) {
    throw new Error('Failed to fetch job status')
  }
  return response.json()
}

const uploadFile = async (file: File): Promise<UploadResponse> => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch('/api/v1/threat-model/analyze', {
    method: 'POST',
    headers: createHeaders(),
    body: formData,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.detail || `Erro ${response.status}: Falha no upload`)
  }

  return response.json()
}

function App() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'upload' | 'about'>('upload')

  // Estados do upload
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'processing' | 'completed' | 'error'>('idle')
  const [jobId, setJobId] = useState<string>('')
  const [errorMessage, setErrorMessage] = useState<string>('')
  const [uploadProgress, setUploadProgress] = useState<number>(0)

  const fileInputRef = useRef<HTMLInputElement>(null)
  const progressIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const isMountedRef = useRef(true)

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      isMountedRef.current = false
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current)
      }
    }
  }, [])

  // React Query: Buscar versão do sistema (com cache)
  const { data: systemVersion } = useQuery({
    queryKey: ['systemVersion'],
    queryFn: fetchSystemVersion,
    staleTime: 1000 * 60 * 5, // 5 minutos
  })

  // React Query: Polling do status do job (com backoff)
  const { data: jobStatusData } = useQuery({
    queryKey: ['jobStatus', jobId],
    queryFn: () => fetchJobStatus(jobId),
    enabled: !!jobId && uploadStatus === 'processing',
    refetchInterval: (query) => {
      // Polling adaptativo: mais frequente no início, depois espaça
      const data = query.state.data
      if (data?.status === 'completed' || data?.status === 'failed') {
        return false // Para o polling
      }
      return 2000 // 2 segundos
    },
    retry: false,
  })

  // Handle job status changes
  useEffect(() => {
    if (jobStatusData) {
      if (jobStatusData.status === 'completed' || jobStatusData.status === 'failed') {
        setUploadStatus(jobStatusData.status === 'completed' ? 'completed' : 'error')
        if (jobStatusData.error) {
          setErrorMessage(jobStatusData.error)
        }
        // Remover query da cache quando job terminar para liberar memória
        if (jobId) {
          queryClient.removeQueries({ queryKey: ['jobStatus', jobId] })
        }
      }
    }
  }, [jobStatusData, jobId, queryClient])

  // Helper para limpar intervalo de progresso
  const clearProgressInterval = () => {
    if (progressIntervalRef.current) {
      clearInterval(progressIntervalRef.current)
      progressIntervalRef.current = null
    }
  }

  // React Query: Mutation para upload
  const uploadMutation = useMutation({
    mutationFn: uploadFile,
    onMutate: () => {
      if (!isMountedRef.current) return

      setUploadStatus('uploading')
      setUploadProgress(0)
      setErrorMessage('')

      // Limpar intervalo anterior se existir
      clearProgressInterval()

      // Simular progresso
      progressIntervalRef.current = setInterval(() => {
        if (!isMountedRef.current) {
          clearProgressInterval()
          return
        }
        setUploadProgress((prev) => {
          if (prev >= 90) {
            clearProgressInterval()
            return 90
          }
          return prev + 10
        })
      }, 200)
    },
    onSuccess: (data) => {
      clearProgressInterval()
      if (!isMountedRef.current) return

      setUploadProgress(100)
      setJobId(data.job_id)
      setUploadStatus('processing')

      if (data.status === 'completed') {
        setUploadStatus('completed')
      }

      // Invalidar cache para forçar novo fetch
      queryClient.invalidateQueries({ queryKey: ['jobStatus', data.job_id] })
    },
    onError: (error: Error) => {
      clearProgressInterval()
      if (!isMountedRef.current) return

      setErrorMessage(error.message || 'Erro de conexão com o servidor')
      setUploadStatus('error')
    },
  })

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      validateAndSetFile(file)
    }
  }

  const validateAndSetFile = (file: File) => {
    // Validar tipo MIME
    const validTypes = ['image/png', 'image/jpeg', 'image/jpg']
    if (!validTypes.includes(file.type)) {
      setErrorMessage('Formato inválido. Use PNG, JPG ou JPEG.')
      setUploadStatus('error')
      return
    }

    // Validar tamanho (50MB)
    const maxSize = 50 * 1024 * 1024
    if (file.size > maxSize) {
      setErrorMessage('Arquivo muito grande. Máximo 50MB.')
      setUploadStatus('error')
      return
    }

    setSelectedFile(file)
    setErrorMessage('')
    setUploadStatus('idle')

    // Gerar preview da imagem (com validação XSS)
    const reader = new FileReader()
    reader.onload = (e) => {
      if (!isMountedRef.current) return
      const result = e.target?.result
      if (typeof result === 'string' && result.startsWith('data:image/')) {
        setPreviewUrl(result)
      } else {
        setErrorMessage('Erro ao processar imagem. Tente outro arquivo.')
        setUploadStatus('error')
      }
    }
    reader.onerror = () => {
      if (!isMountedRef.current) return
      setErrorMessage('Erro ao ler arquivo. Verifique o formato.')
      setUploadStatus('error')
    }
    reader.readAsDataURL(file)
  }

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    const file = event.dataTransfer.files?.[0]
    if (file) {
      validateAndSetFile(file)
    }
  }

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
  }

  const handleUpload = () => {
    if (!selectedFile) return
    uploadMutation.mutate(selectedFile)
  }

  const handleReset = () => {
    // Limpar intervalo pendente
    clearProgressInterval()
    // Remover query da cache ao resetar para liberar memória
    if (jobId) {
      queryClient.removeQueries({ queryKey: ['jobStatus', jobId] })
    }
    setSelectedFile(null)
    setPreviewUrl(null)
    setUploadStatus('idle')
    setJobId('')
    setErrorMessage('')
    setUploadProgress(0)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-fiap-gray-900 via-fiap-black to-fiap-gray-900">
      {/* Header */}
      <header className="bg-slate-900/80 backdrop-blur-md border-b border-slate-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <Shield className="w-8 h-8 text-fiap-pink" aria-hidden="true" />
              <div>
                <h1 className="text-xl font-bold text-white">FIAP STRIDE</h1>
                <p className="text-xs text-slate-400">Grupo 27 - Hackathon Fase 5</p>
              </div>
            </div>
            <nav className="flex space-x-4" role="tablist" aria-label="Navegação principal">
              <button
                role="tab"
                aria-selected={activeTab === 'upload'}
                aria-controls="upload-panel"
                id="upload-tab"
                onClick={() => setActiveTab('upload')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  activeTab === 'upload'
                    ? 'bg-fiap-pink/20 text-fiap-pink'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800'
                }`}
              >
                <span className="flex items-center space-x-2">
                  <Upload className="w-4 h-4" aria-hidden="true" />
                  <span>Análise</span>
                </span>
              </button>
              <button
                role="tab"
                aria-selected={activeTab === 'about'}
                aria-controls="about-panel"
                id="about-tab"
                onClick={() => setActiveTab('about')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  activeTab === 'about'
                    ? 'bg-fiap-pink/20 text-fiap-pink'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800'
                }`}
              >
                <span className="flex items-center space-x-2">
                  <Info className="w-4 h-4" aria-hidden="true" />
                  <span>Sobre</span>
                </span>
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'upload' ? (
          <div id="upload-panel" role="tabpanel" aria-labelledby="upload-tab" className="space-y-6">
            {/* Hero Section */}
            <section className="bg-slate-800/50 border border-slate-700 rounded-2xl p-8">
              <div className="flex items-start space-x-4">
                <div className="p-3 bg-fiap-pink/10 rounded-xl">
                  <Shield className="w-8 h-8 text-fiap-pink" aria-hidden="true" />
                </div>
                <div className="flex-1">
                  <h2 className="text-2xl font-bold text-white mb-2">
                    Modelagem de Ameaças com IA
                  </h2>
                  <p className="text-slate-400 leading-relaxed">
                    Sistema automatizado de análise de segurança baseado na metodologia{' '}
                    <span className="text-fiap-pink font-semibold">STRIDE</span> da Microsoft.
                    Faça upload de diagramas de arquitetura e receba um relatório completo de
                    vulnerabilidades e contramedidas.
                  </p>
                </div>
              </div>
            </section>

            {/* Upload Section */}
            <section className="bg-slate-800/50 border border-slate-700 rounded-2xl p-8">
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileSelect}
                accept=".png,.jpg,.jpeg"
                className="hidden"
                data-testid="file-input"
                aria-label="Selecionar arquivo de imagem"
              />

              {uploadStatus === 'idle' && !selectedFile && (
                <div
                  className="text-center py-12 border-2 border-dashed border-slate-600 rounded-xl hover:border-fiap-pink/50 transition-colors cursor-pointer"
                  onClick={() => fileInputRef.current?.click()}
                  onDrop={handleDrop}
                  onDragOver={handleDragOver}
                  data-testid="upload-dropzone"
                  role="button"
                  aria-label="Área de upload de imagem"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      fileInputRef.current?.click()
                    }
                  }}
                >
                  <div className="inline-flex items-center justify-center w-20 h-20 bg-slate-700/50 rounded-full mb-6">
                    <Upload className="w-10 h-10 text-slate-400" aria-hidden="true" />
                  </div>
                  <h3 className="text-xl font-semibold text-white mb-2">
                    Upload de Diagrama de Arquitetura
                  </h3>
                  <p className="text-slate-400 mb-6 max-w-md mx-auto">
                    Arraste e solte uma imagem do diagrama ou clique para selecionar.
                    Formatos suportados: PNG, JPG, JPEG (máx. 50MB)
                  </p>
                  <button
                    className="px-6 py-3 bg-fiap-pink hover:bg-fiap-pink/80 text-white rounded-lg font-medium transition-colors"
                    aria-label="Abrir seletor de arquivo"
                  >
                    Selecionar Arquivo
                  </button>
                  <p className="text-sm text-slate-500 mt-4">
                    🔒 Os arquivos são processados localmente e não são persistidos
                  </p>
                </div>
              )}

              {/* Arquivo selecionado, aguardando upload */}
              {uploadStatus === 'idle' && selectedFile && (
                <div className="text-center py-12" data-testid="file-selected">
                  <div className="mb-6">
                    {previewUrl ? (
                      <img
                        src={previewUrl}
                        alt="Pré-visualização do diagrama selecionado"
                        className="max-h-48 max-w-full mx-auto rounded-lg shadow-lg border-2 border-fiap-pink/30"
                        data-testid="image-preview"
                      />
                    ) : (
                      <div className="inline-flex items-center justify-center w-20 h-20 bg-fiap-pink/10 rounded-full">
                        <FileImage className="w-10 h-10 text-fiap-pink" aria-hidden="true" />
                      </div>
                    )}
                  </div>
                  <h3 className="text-xl font-semibold text-white mb-2">
                    Arquivo Selecionado
                  </h3>
                  <p className="text-slate-300 mb-2" data-testid="filename">{selectedFile.name}</p>
                  <p className="text-slate-500 text-sm mb-6" data-testid="filesize">
                    {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                  <div className="flex justify-center space-x-4">
                    <button
                      onClick={handleUpload}
                      className="px-6 py-3 bg-fiap-pink hover:bg-fiap-pink/80 text-white rounded-lg font-medium transition-colors"
                      data-testid="start-analysis"
                      aria-label="Iniciar análise de segurança"
                    >
                      Iniciar Análise
                    </button>
                    <button
                      onClick={handleReset}
                      className="px-6 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-medium transition-colors"
                      data-testid="change-file"
                      aria-label="Trocar arquivo selecionado"
                    >
                      Trocar Arquivo
                    </button>
                  </div>
                </div>
              )}

              {/* Upload em progresso */}
              {uploadStatus === 'uploading' && (
                <div className="text-center py-12" data-testid="uploading" role="status" aria-live="polite">
                  <div className="inline-flex items-center justify-center w-20 h-20 bg-fiap-pink/10 rounded-full mb-6">
                    <Loader2 className="w-10 h-10 text-fiap-pink animate-spin" aria-hidden="true" />
                  </div>
                  <h3 className="text-xl font-semibold text-white mb-2">
                    Enviando Arquivo...
                  </h3>
                  <div className="max-w-md mx-auto mb-4">
                    <div
                      className="bg-slate-700 rounded-full h-2 overflow-hidden"
                      role="progressbar"
                      aria-valuenow={uploadProgress}
                      aria-valuemin={0}
                      aria-valuemax={100}
                      aria-label="Progresso do upload"
                    >
                      <div
                        className="bg-fiap-pink h-full transition-all duration-300"
                        style={{ width: `${uploadProgress}%` }}
                        data-testid="progress-bar"
                      />
                    </div>
                    <p className="text-slate-400 mt-2" data-testid="progress-text">{uploadProgress}%</p>
                  </div>
                </div>
              )}

              {/* Processando análise */}
              {uploadStatus === 'processing' && (
                <div className="text-center py-12" data-testid="processing" role="status" aria-live="polite">
                  <div className="inline-flex items-center justify-center w-20 h-20 bg-fiap-pink/10 rounded-full mb-6">
                    <Loader2 className="w-10 h-10 text-fiap-pink animate-spin" aria-hidden="true" />
                  </div>
                  <h3 className="text-xl font-semibold text-white mb-2">
                    Analisando Diagrama...
                  </h3>
                  <p className="text-slate-400 mb-4 max-w-md mx-auto">
                    Detectando componentes e aplicando modelagem STRIDE.
                    Isso pode levar alguns minutos.
                  </p>
                  <div className="max-w-md mx-auto">
                    <div
                      className="bg-slate-700 rounded-full h-2 overflow-hidden"
                      role="progressbar"
                      aria-valuenow={60}
                      aria-valuemin={0}
                      aria-valuemax={100}
                      aria-label="Progresso da análise"
                    >
                      <div
                        className="bg-fiap-pink h-full animate-pulse"
                        style={{ width: '60%' }}
                      />
                    </div>
                  </div>
                  {jobId && (
                    <p className="text-slate-500 text-sm mt-4" data-testid="job-id">
                      Job ID: {jobId}
                    </p>
                  )}
                </div>
              )}

              {/* Upload concluído */}
              {uploadStatus === 'completed' && jobId && (
                <div data-testid="completed">
                  <ThreatReport
                    jobId={jobId}
                    onNewAnalysis={handleReset}
                  />
                </div>
              )}

              {/* Erro */}
              {uploadStatus === 'error' && (
                <div className="text-center py-12" data-testid="error" role="alert" aria-live="assertive">
                  <div className="inline-flex items-center justify-center w-20 h-20 bg-red-500/10 rounded-full mb-6">
                    <XCircle className="w-10 h-10 text-red-500" aria-hidden="true" />
                  </div>
                  <h3 className="text-xl font-semibold text-white mb-2">
                    Erro na Análise
                  </h3>
                  <p className="text-red-400 mb-6 max-w-md mx-auto" data-testid="error-message">
                    {errorMessage || 'Ocorreu um erro ao processar o arquivo. Tente novamente.'}
                  </p>
                  <div className="flex justify-center space-x-4">
                    <button
                      onClick={handleReset}
                      className="px-6 py-3 bg-fiap-pink hover:bg-fiap-pink/80 text-white rounded-lg font-medium transition-colors"
                      data-testid="try-again"
                      aria-label="Tentar análise novamente"
                    >
                      Tentar Novamente
                    </button>
                  </div>
                </div>
              )}
            </section>

            {/* STRIDE Explanation */}
            <section className="bg-slate-800/50 border border-slate-700 rounded-2xl p-8">
              <div className="flex items-center space-x-3 mb-6">
                <AlertTriangle className="w-6 h-6 text-amber-400" aria-hidden="true" />
                <h3 className="text-xl font-bold text-white">O que é STRIDE?</h3>
              </div>
              <p className="text-slate-400 leading-relaxed mb-6">
                STRIDE é uma metodologia de modelagem de ameaças desenvolvida pela Microsoft que
                categoriza as ameaças de segurança em seis tipos distintos. Cada letra representa
                uma categoria de ameaça que viola uma propriedade específica de segurança:
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <StrideCard
                  letter="S"
                  title="Spoofing"
                  description="Falsificação de identidade - viola a Autenticação"
                  color="red"
                />
                <StrideCard
                  letter="T"
                  title="Tampering"
                  description="Modificação não autorizada de dados - viola a Integridade"
                  color="orange"
                />
                <StrideCard
                  letter="R"
                  title="Repudiation"
                  description="Negação de ações realizadas - viola a Não-repudiação"
                  color="yellow"
                />
                <StrideCard
                  letter="I"
                  title="Information Disclosure"
                  description="Vazamento de informações - viola a Confidencialidade"
                  color="blue"
                />
                <StrideCard
                  letter="D"
                  title="Denial of Service"
                  description="Indisponibilidade do sistema - viola a Disponibilidade"
                  color="purple"
                />
                <StrideCard
                  letter="E"
                  title="Elevation of Privilege"
                  description="Escalonamento de privilégios - viola a Autorização"
                  color="pink"
                />
              </div>
            </section>
          </div>
        ) : (
          <div id="about-panel" role="tabpanel" aria-labelledby="about-tab">
            <AboutSection />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-slate-900 border-t border-slate-800 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <Shield className="w-5 h-5 text-emerald-400" aria-hidden="true" />
                <span className="font-semibold text-white">STRIDE</span>
              </div>
              <p className="text-sm text-slate-400">
                Modelagem de ameaças automatizada usando IA e metodologia STRIDE.
                Desenvolvido durante o Hackathon Fase 5.
              </p>
            </div>
            <div className="md:text-right">
              <p className="text-sm text-slate-500 mb-2">
                © 2026 Grupo 27
              </p>
              {systemVersion && (
                <p className="text-xs text-slate-600 mb-2" data-testid="system-version">
                  v{systemVersion}
                </p>
              )}
              <p className="text-xs text-slate-600 max-w-md md:ml-auto">
                Este site não coleta dados pessoais, não utiliza cookies de rastreamento
                e não armazena informações dos visitantes.
              </p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

function AboutSection() {
  return (
    <div className="space-y-6">
      <section className="bg-slate-800/50 border border-slate-700 rounded-2xl p-8">
        <h2 className="text-2xl font-bold text-white mb-6">Sobre o Projeto</h2>
        <div className="prose prose-invert max-w-none">
          <p className="text-slate-400 leading-relaxed mb-4">
            O <strong className="text-fiap-pink">FIAP STRIDE</strong> é uma solução inovadora
            desenvolvida durante o Hackathon da Fase 5 da FIAP, que utiliza Inteligência
            Artificial para automatizar a modelagem de ameaças em software.
          </p>
          <p className="text-slate-400 leading-relaxed mb-4">
            Através de técnicas de Computer Vision com YOLOv11, o sistema detecta componentes
            em diagramas de arquitetura e aplica automaticamente as 6 categorias da
            metodologia STRIDE para identificar potenciais vulnerabilidades.
          </p>
          <h3 className="text-xl font-semibold text-white mt-6 mb-4">Metodologia STRIDE</h3>
          <p className="text-slate-400 leading-relaxed mb-4">
            STRIDE é um framework de modelagem de ameaças criado pela Microsoft que organiza
            as ameaças de segurança em seis categorias baseadas nas propriedades de segurança
            que elas violam:
          </p>
          <ul className="space-y-2 text-slate-400">
            <li><strong className="text-red-400">S - Spoofing:</strong> Ameaças de falsificação de identidade (viola Autenticação)</li>
            <li><strong className="text-orange-400">T - Tampering:</strong> Modificação não autorizada (viola Integridade)</li>
            <li><strong className="text-yellow-400">R - Repudiation:</strong> Negação de responsabilidade (viola Não-repudiação)</li>
            <li><strong className="text-blue-400">I - Information Disclosure:</strong> Vazamento de dados (viola Confidencialidade)</li>
            <li><strong className="text-purple-400">D - Denial of Service:</strong> Indisponibilidade (viola Disponibilidade)</li>
            <li><strong className="text-pink-400">E - Elevation of Privilege:</strong> Escalonamento de privilégios (viola Autorização)</li>
          </ul>
          <h3 className="text-xl font-semibold text-white mt-6 mb-4">Grupo 27</h3>
          <p className="text-slate-400 leading-relaxed mb-4">
            Este projeto foi desenvolvido pelo <strong className="text-fiap-pink">Grupo 27</strong> como
            parte do desafio proposto na Fase 5 do curso de Software Security da FIAP.
            A solução combina FastAPI, React, PostgreSQL, Redis, YOLOv11 e PyTorch para
            entregar uma plataforma completa de análise de segurança.
          </p>

          <h4 className="text-lg font-semibold text-white mt-6 mb-3">Integrantes</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <a
              href="https://github.com/AdrielCandido"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center space-x-3 p-3 bg-slate-700/50 rounded-lg hover:bg-slate-700 transition-colors"
              aria-label="Perfil GitHub de Adriel Santos"
            >
              <Github className="w-5 h-5 text-slate-400" aria-hidden="true" />
              <div>
                <p className="text-white font-medium">Adriel Santos</p>
                <p className="text-sm text-slate-500">@AdrielCandido</p>
              </div>
            </a>
            <a
              href="https://github.com/LeticiaNepomucena"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center space-x-3 p-3 bg-slate-700/50 rounded-lg hover:bg-slate-700 transition-colors"
              aria-label="Perfil GitHub de Leticia Nepomuceno"
            >
              <Github className="w-5 h-5 text-slate-400" aria-hidden="true" />
              <div>
                <p className="text-white font-medium">Leticia Nepomuceno</p>
                <p className="text-sm text-slate-500">@LeticiaNepomucena</p>
              </div>
            </a>
            <a
              href="https://github.com/lucfsilva"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center space-x-3 p-3 bg-slate-700/50 rounded-lg hover:bg-slate-700 transition-colors"
              aria-label="Perfil GitHub de Lucas Silva"
            >
              <Github className="w-5 h-5 text-slate-400" aria-hidden="true" />
              <div>
                <p className="text-white font-medium">Lucas Silva</p>
                <p className="text-sm text-slate-500">@lucfsilva</p>
              </div>
            </a>
            <a
              href="https://github.com/vagnerbarbosa"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center space-x-3 p-3 bg-slate-700/50 rounded-lg hover:bg-slate-700 transition-colors"
              aria-label="Perfil GitHub de Vagner Barbosa"
            >
              <Github className="w-5 h-5 text-slate-400" aria-hidden="true" />
              <div>
                <p className="text-white font-medium">Vagner Barbosa</p>
                <p className="text-sm text-slate-500">@vagnerbarbosa</p>
              </div>
            </a>
          </div>

          <h4 className="text-lg font-semibold text-white mt-6 mb-3">Repositório</h4>
          <a
            href="https://github.com/vagnerbarbosa/hackathon-fiap-fase-5"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center space-x-2 px-4 py-3 bg-fiap-pink/10 border border-fiap-pink/20 rounded-lg text-fiap-pink hover:bg-fiap-pink/20 transition-colors"
            aria-label="Acessar repositório no GitHub"
          >
            <Github className="w-5 h-5" aria-hidden="true" />
            <span>github.com/vagnerbarbosa/hackathon-fiap-fase-5</span>
          </a>
        </div>
      </section>

      <section className="bg-slate-800/50 border border-slate-700 rounded-2xl p-8">
        <h2 className="text-2xl font-bold text-white mb-6">Tecnologias Utilizadas</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <TechBadge name="FastAPI" color="emerald" />
          <TechBadge name="React" color="blue" />
          <TechBadge name="TypeScript" color="blue" />
          <TechBadge name="Tailwind CSS" color="cyan" />
          <TechBadge name="PostgreSQL" color="blue" />
          <TechBadge name="Redis" color="red" />
          <TechBadge name="YOLOv11" color="purple" />
          <TechBadge name="PyTorch" color="orange" />
        </div>
      </section>
    </div>
  )
}

export default App
