import { useState } from 'react'
import { Shield, Upload, Info, AlertTriangle, Github } from 'lucide-react'
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState<'upload' | 'about'>('upload')

  return (
    <div className="min-h-screen bg-gradient-to-br from-fiap-gray-900 via-fiap-black to-fiap-gray-900">
      {/* Header */}
      <header className="bg-slate-900/80 backdrop-blur-md border-b border-slate-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <Shield className="w-8 h-8 text-fiap-pink" />
              <div>
                <h1 className="text-xl font-bold text-white">FIAP STRIDE</h1>
                <p className="text-xs text-slate-400">Grupo 27 - Hackathon Fase 5</p>
              </div>
            </div>
            <nav className="flex space-x-4">
              <button
                onClick={() => setActiveTab('upload')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  activeTab === 'upload'
                    ? 'bg-fiap-pink/20 text-fiap-pink'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800'
                }`}
              >
                <span className="flex items-center space-x-2">
                  <Upload className="w-4 h-4" />
                  <span>Análise</span>
                </span>
              </button>
              <button
                onClick={() => setActiveTab('about')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  activeTab === 'about'
                    ? 'bg-fiap-pink/20 text-fiap-pink'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800'
                }`}
              >
                <span className="flex items-center space-x-2">
                  <Info className="w-4 h-4" />
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
          <div className="space-y-6">
            {/* Hero Section */}
            <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-8">
              <div className="flex items-start space-x-4">
                <div className="p-3 bg-fiap-pink/10 rounded-xl">
                  <Shield className="w-8 h-8 text-fiap-pink" />
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
            </div>

            {/* Upload Section */}
            <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-8">
              <div className="text-center py-12">
                <div className="inline-flex items-center justify-center w-20 h-20 bg-slate-700/50 rounded-full mb-6">
                  <Upload className="w-10 h-10 text-slate-400" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">
                  Upload de Diagrama de Arquitetura
                </h3>
                <p className="text-slate-400 mb-6 max-w-md mx-auto">
                  Arraste e solte uma imagem do diagrama ou clique para selecionar.
                  Formatos suportados: PNG, JPG, JPEG (máx. 50MB)
                </p>
                <button
                  disabled
                  className="px-6 py-3 bg-slate-700 text-slate-400 rounded-lg font-medium cursor-not-allowed"
                >
                  Selecionar Arquivo
                </button>
                <p className="text-sm text-slate-500 mt-4">
                  🔒 Os arquivos são processados localmente e não são persistidos
                </p>
              </div>
            </div>

            {/* STRIDE Explanation */}
            <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-8">
              <div className="flex items-center space-x-3 mb-6">
                <AlertTriangle className="w-6 h-6 text-amber-400" />
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
            </div>
          </div>
        ) : (
          <AboutSection />
        )}
      </main>

      {/* Footer */}
      <footer className="bg-slate-900 border-t border-slate-800 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <Shield className="w-5 h-5 text-fiap-pink" />
                <span className="font-semibold text-white">FIAP STRIDE</span>
              </div>
              <p className="text-sm text-slate-400">
                Modelagem de ameaças automatizada usando IA e metodologia STRIDE.
                Desenvolvido durante o Hackathon FIAP Fase 5.
              </p>
            </div>
            <div className="md:text-right">
              <p className="text-sm text-slate-500 mb-2">
                © 2026 FIAP STRIDE - Grupo 27
              </p>
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

interface StrideCardProps {
  letter: string
  title: string
  description: string
  color: 'red' | 'orange' | 'yellow' | 'blue' | 'purple' | 'pink'
}

function StrideCard({ letter, title, description, color }: StrideCardProps) {
  const colorClasses = {
    red: 'bg-red-500/10 border-red-500/20 text-red-400',
    orange: 'bg-orange-500/10 border-orange-500/20 text-orange-400',
    yellow: 'bg-yellow-500/10 border-yellow-500/20 text-yellow-400',
    blue: 'bg-blue-500/10 border-blue-500/20 text-blue-400',
    purple: 'bg-purple-500/10 border-purple-500/20 text-purple-400',
    pink: 'bg-pink-500/10 border-pink-500/20 text-pink-400',
  }

  return (
    <div className={`p-4 rounded-xl border ${colorClasses[color]} hover:bg-opacity-20 transition-colors`}>
      <div className="flex items-center space-x-3 mb-2">
        <span className="text-2xl font-bold">{letter}</span>
        <span className="font-semibold">{title}</span>
      </div>
      <p className="text-sm text-slate-400">{description}</p>
    </div>
  )
}

function AboutSection() {
  return (
    <div className="space-y-6">
      <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-8">
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
            >
              <Github className="w-5 h-5 text-slate-400" />
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
            >
              <Github className="w-5 h-5 text-slate-400" />
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
            >
              <Github className="w-5 h-5 text-slate-400" />
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
            >
              <Github className="w-5 h-5 text-slate-400" />
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
          >
            <Github className="w-5 h-5" />
            <span>github.com/vagnerbarbosa/hackathon-fiap-fase-5</span>
          </a>
        </div>
      </div>

      <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-8">
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
      </div>
    </div>
  )
}

interface TechBadgeProps {
  name: string
  color: 'emerald' | 'blue' | 'cyan' | 'red' | 'purple' | 'orange'
}

function TechBadge({ name, color }: TechBadgeProps) {
  const colorClasses = {
    emerald: 'bg-fiap-pink/10 border-fiap-pink/20 text-fiap-pink',
    blue: 'bg-blue-500/10 border-blue-500/20 text-blue-400',
    cyan: 'bg-cyan-500/10 border-cyan-500/20 text-cyan-400',
    red: 'bg-red-500/10 border-red-500/20 text-red-400',
    purple: 'bg-purple-500/10 border-purple-500/20 text-purple-400',
    orange: 'bg-orange-500/10 border-orange-500/20 text-orange-400',
  }

  return (
    <div className={`px-4 py-2 rounded-lg border text-center font-medium ${colorClasses[color]}`}>
      {name}
    </div>
  )
}

export default App
