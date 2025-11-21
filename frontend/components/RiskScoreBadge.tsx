'use client'

interface RiskScoreBadgeProps {
  score: number
  label?: string
}

export default function RiskScoreBadge({ score, label = 'Risk Score' }: RiskScoreBadgeProps) {
  const getColor = (score: number) => {
    if (score >= 70) return 'danger'
    if (score >= 40) return 'warning'
    return 'success'
  }

  const color = getColor(score)
  const colorClasses = {
    success: 'bg-success/10 text-success border-success/20',
    warning: 'bg-warning/10 text-warning border-warning/20',
    danger: 'bg-danger/10 text-danger border-danger/20',
  }

  return (
    <div className={`inline-flex items-center space-x-2 px-4 py-2 rounded-lg border ${colorClasses[color]}`}>
      <span className="text-sm font-medium">{label}:</span>
      <span className="text-lg font-bold">{score}</span>
      <span className="text-xs">/100</span>
    </div>
  )
}

