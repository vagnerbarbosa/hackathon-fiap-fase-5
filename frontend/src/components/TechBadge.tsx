interface TechBadgeProps {
  name: string
  color: 'emerald' | 'blue' | 'cyan' | 'red' | 'purple' | 'orange'
}

export default function TechBadge({ name, color }: TechBadgeProps) {
  const colorClasses = {
    emerald: 'bg-fiap-pink/10 border-fiap-pink/20 text-fiap-pink',
    blue: 'bg-blue-500/10 border-blue-500/20 text-blue-400',
    cyan: 'bg-cyan-500/10 border-cyan-500/20 text-cyan-400',
    red: 'bg-red-500/10 border-red-500/20 text-red-400',
    purple: 'bg-purple-500/10 border-purple-500/20 text-purple-400',
    orange: 'bg-orange-500/10 border-orange-500/20 text-orange-400',
  }

  return (
    <div
      data-testid="tech-badge"
      className={`px-4 py-2 rounded-lg border text-center font-medium ${colorClasses[color]}`}
    >
      {name}
    </div>
  )
}
