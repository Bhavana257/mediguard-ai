'use client'

import AgentCard from './AgentCard'

interface ResultsDisplayProps {
  results: {
    identity?: any
    billing?: any
    discharge?: any
    final?: any
  }
  isLoading: {
    identity: boolean
    billing: boolean
    discharge: boolean
  }
}

export default function ResultsDisplay({ results, isLoading }: ResultsDisplayProps) {
  if (!results.identity && !isLoading.identity) return null

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-800">Analysis Results</h2>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Agent 1: Identity & Claims Fraud */}
        <AgentCard
          title="Identity & Claims Fraud"
          icon="🔍"
          data={results.identity}
          isLoading={isLoading.identity}
        />

        {/* Agent 2: Billing Fraud */}
        <AgentCard
          title="Billing Fraud"
          icon="💰"
          data={results.billing}
          isLoading={isLoading.billing}
        />

        {/* Agent 3: Discharge Blockers */}
        <AgentCard
          title="Discharge Blockers"
          icon="🚪"
          data={results.discharge}
          isLoading={isLoading.discharge}
        />
      </div>

      {/* Final Summary */}
      {results.final && (
        <div className="bg-gradient-to-r from-primary/10 to-secondary/10 rounded-lg shadow-sm border border-primary/20 p-6">
          <h3 className="text-xl font-semibold text-gray-800 mb-4">Final Summary</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {results.final.fraud_risk_score !== undefined && (
              <div>
                <span className="text-sm text-gray-600">Overall Fraud Risk: </span>
                <span className="font-bold text-lg">
                  {results.final.fraud_risk_score}/100
                </span>
              </div>
            )}
            {results.final.identity_misuse_flag !== undefined && (
              <div>
                <span className="text-sm text-gray-600">Identity Misuse: </span>
                <span className={`font-medium ${results.final.identity_misuse_flag ? 'text-danger' : 'text-success'}`}>
                  {results.final.identity_misuse_flag ? 'Detected' : 'Not Detected'}
                </span>
              </div>
            )}
            {results.final.discharge_ready !== undefined && (
              <div>
                <span className="text-sm text-gray-600">Discharge Status: </span>
                <span className={`font-medium ${results.final.discharge_ready ? 'text-success' : 'text-warning'}`}>
                  {results.final.discharge_ready ? 'Ready' : 'Not Ready'}
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

