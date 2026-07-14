import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import TechBadge from '../../components/TechBadge'

describe('TechBadge', () => {
  it('deve renderizar o nome da tecnologia', () => {
    render(<TechBadge name="React" color="blue" />)

    expect(screen.getByText('React')).toBeInTheDocument()
  })

  it('deve aplicar classes de cor corretamente', () => {
    const { rerender } = render(<TechBadge name="Test" color="emerald" />)

    let badge = screen.getByTestId('tech-badge')
    expect(badge).toHaveClass('border-fiap-pink/20')

    rerender(<TechBadge name="Test" color="blue" />)
    badge = screen.getByTestId('tech-badge')
    expect(badge).toHaveClass('border-blue-500/20')

    rerender(<TechBadge name="Test" color="red" />)
    badge = screen.getByTestId('tech-badge')
    expect(badge).toHaveClass('border-red-500/20')
  })

  it('deve renderizar diferentes tecnologias', () => {
    const technologies = [
      { name: 'FastAPI', color: 'emerald' as const },
      { name: 'React', color: 'blue' as const },
      { name: 'TypeScript', color: 'blue' as const },
      { name: 'Tailwind CSS', color: 'cyan' as const },
      { name: 'PostgreSQL', color: 'blue' as const },
      { name: 'Redis', color: 'red' as const },
      { name: 'YOLOv11', color: 'purple' as const },
      { name: 'PyTorch', color: 'orange' as const },
    ]

    technologies.forEach(({ name, color }) => {
      const { unmount } = render(<TechBadge name={name} color={color} />)

      expect(screen.getByText(name)).toBeInTheDocument()

      unmount()
    })
  })
})
