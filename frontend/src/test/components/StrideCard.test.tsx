import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import StrideCard from '../../components/StrideCard'

describe('StrideCard', () => {
  it('deve renderizar corretamente com props básicas', () => {
    render(
      <StrideCard
        letter="S"
        title="Spoofing"
        description="Teste de descrição"
        color="red"
      />
    )

    expect(screen.getByText('S')).toBeInTheDocument()
    expect(screen.getByText('Spoofing')).toBeInTheDocument()
    expect(screen.getByText('Teste de descrição')).toBeInTheDocument()
  })

  it('deve aplicar classes de cor corretamente para cada tipo', () => {
    const { rerender } = render(
      <StrideCard letter="S" title="Test" description="Desc" color="red" />
    )

    let card = screen.getByTestId('stride-card')
    expect(card).toHaveClass('border-red-500/20')

    rerender(<StrideCard letter="T" title="Test" description="Desc" color="orange" />)
    card = screen.getByTestId('stride-card')
    expect(card).toHaveClass('border-orange-500/20')

    rerender(<StrideCard letter="I" title="Test" description="Desc" color="blue" />)
    card = screen.getByTestId('stride-card')
    expect(card).toHaveClass('border-blue-500/20')
  })

  it('deve renderizar todas as letras do STRIDE', () => {
    const strideLetters = [
      { letter: 'S', title: 'Spoofing', color: 'red' as const },
      { letter: 'T', title: 'Tampering', color: 'orange' as const },
      { letter: 'R', title: 'Repudiation', color: 'yellow' as const },
      { letter: 'I', title: 'Information Disclosure', color: 'blue' as const },
      { letter: 'D', title: 'Denial of Service', color: 'purple' as const },
      { letter: 'E', title: 'Elevation of Privilege', color: 'pink' as const },
    ]

    strideLetters.forEach(({ letter, title, color }) => {
      const { unmount } = render(
        <StrideCard
          letter={letter}
          title={title}
          description={`Descrição de ${title}`}
          color={color}
        />
      )

      expect(screen.getByText(letter)).toBeInTheDocument()
      expect(screen.getByText(title)).toBeInTheDocument()

      unmount()
    })
  })
})
