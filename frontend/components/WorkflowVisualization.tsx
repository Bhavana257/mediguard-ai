'use client'

interface WorkflowVisualizationProps {
  currentStep: 'identity' | 'billing' | 'discharge' | 'complete' | null
}

export default function WorkflowVisualization({ currentStep }: WorkflowVisualizationProps) {
  const steps = [
    { id: 'identity', name: 'Identity & Claims Fraud', icon: '🔍' },
    { id: 'billing', name: 'Billing Fraud', icon: '💰' },
    { id: 'discharge', name: 'Discharge Blockers', icon: '🚪' },
  ]

  const getStepStatus = (stepId: string) => {
    if (!currentStep) return 'pending'
    const stepIndex = steps.findIndex(s => s.id === stepId)
    const currentIndex = steps.findIndex(s => s.id === currentStep)
    
    if (stepIndex < currentIndex) return 'completed'
    if (stepIndex === currentIndex) return 'active'
    return 'pending'
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h2 className="text-xl font-semibold text-gray-800 mb-6">Analysis Workflow</h2>
      
      <div className="space-y-6">
        {steps.map((step, index) => {
          const status = getStepStatus(step.id)
          const isCompleted = status === 'completed'
          const isActive = status === 'active'
          
          return (
            <div key={step.id} className="flex items-start space-x-4">
              {/* Step Icon */}
              <div className={`
                flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center text-xl
                ${isCompleted ? 'bg-success text-white' : ''}
                ${isActive ? 'bg-primary text-white animate-pulse' : ''}
                ${status === 'pending' ? 'bg-gray-200 text-gray-400' : ''}
              `}>
                {isCompleted ? '✓' : step.icon}
              </div>

              {/* Step Content */}
              <div className="flex-1">
                <div className="flex items-center justify-between mb-2">
                  <h3 className={`font-medium ${isActive ? 'text-primary' : isCompleted ? 'text-gray-700' : 'text-gray-400'}`}>
                    {step.name}
                  </h3>
                  {isActive && (
                    <span className="text-xs bg-primary/10 text-primary px-2 py-1 rounded">Processing...</span>
                  )}
                  {isCompleted && (
                    <span className="text-xs bg-success/10 text-success px-2 py-1 rounded">Completed</span>
                  )}
                </div>
                
                {/* Progress Bar */}
                {index < steps.length - 1 && (
                  <div className="ml-6 mt-2">
                    <div className="h-1 w-1 bg-gray-200 rounded-full">
                      <div className={`
                        h-full transition-all duration-500
                        ${isCompleted ? 'w-full bg-success' : isActive ? 'w-1/2 bg-primary' : 'w-0 bg-gray-200'}
                      `}></div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

