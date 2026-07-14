interface StrideCardProps {
  letter: string
  title: string
  description: string
  color: 'red' | 'orange' | 'yellow' | 'blue' | 'purple' | 'pink'
}

export default function StrideCard({ letter, title, description, color }: StrideCardProps) {
  const colorClasses = {
    red: 'bg-red-500/10 border-red-500/20 text-red-400',
    orange: 'bg-orange-500/10 border-orange-500/20 text-orange-400',
    yellow: 'bg-yellow-500/10 border-yellow-500/20 text-yellow-400',
    blue: 'bg-blue-500/10 border-blue-500/20 text-blue-400',
    purple: 'bg-purple-500/10 border-purple-500/20 text-purple-400',
    pink: 'bg-pink-500/10 border-pink-500/20 text-pink-400',
  }

  return (
    <div
      data-testid="stride-card"
      className={`p-4 rounded-xl border ${colorClasses[color]} hover:bg-opacity-20 transition-colors`}
    >
      <div className="flex items-center space-x-3 mb-2">
        <span className="text-2xl font-bold">{letter}</span>
        <span className="font-semibold">{title}</span>
      </div>
      <p className="text-sm text-slate-400">{description}</p>
    </div>
  )
}
