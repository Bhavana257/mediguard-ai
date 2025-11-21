'use client'

import { useState } from 'react'
import Sidebar from '@/components/Sidebar'
import PatientInput from '@/components/PatientInput'
import WorkflowVisualization from '@/components/WorkflowVisualization'
import ResultsDisplay from '@/components/ResultsDisplay'

export default function Home() {
  const [results, setResults] = useState<{
    identity?: any
    billing?: any
    discharge?: any
    final?: any
  }>({})
  const [isLoading, setIsLoading] = useState(false)
  const [currentStep, setCurrentStep] = useState<'identity' | 'billing' | 'discharge' | 'complete' | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleAnalyze = async (patientId: string) => {
    setIsLoading(true)
    setError(null)
    setResults({})
    setCurrentStep('identity')

    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ patient_id: patientId }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Analysis failed')
      }

      const data = await response.json()
      
      // Simulate progressive loading for better UX
      if (data.identity) {
        setResults({ identity: data.identity })
        setCurrentStep('billing')
        await new Promise(resolve => setTimeout(resolve, 500))
      }
      
      if (data.billing) {
        setResults(prev => ({ ...prev, billing: data.billing }))
        setCurrentStep('discharge')
        await new Promise(resolve => setTimeout(resolve, 500))
      }
      
      if (data.discharge) {
        setResults(prev => ({ ...prev, discharge: data.discharge }))
        setCurrentStep('complete')
      }
      
      if (data.final) {
        setResults(prev => ({ ...prev, final: data.final }))
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred during analysis')
      setCurrentStep(null)
    } finally {
      setIsLoading(false)
    }
  }

  const loadingState = {
    identity: isLoading && currentStep === 'identity',
    billing: isLoading && currentStep === 'billing',
    discharge: isLoading && currentStep === 'discharge',
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      
      <main className="flex-1 ml-64 p-8">
        <div className="max-w-7xl mx-auto space-y-8">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-gray-800">Health Dashboard</h1>
              <p className="text-gray-600 mt-1">Welcome back! Analyze patient data for fraud detection.</p>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-danger/10 border border-danger/20 text-danger px-4 py-3 rounded-lg">
              <p className="font-medium">Error: {error}</p>
            </div>
          )}

          {/* Patient Input */}
          <PatientInput onAnalyze={handleAnalyze} isLoading={isLoading} />

          {/* Workflow Visualization */}
          {(isLoading || currentStep) && (
            <WorkflowVisualization currentStep={currentStep} />
          )}

          {/* Results Display */}
          {(Object.keys(results).length > 0 || isLoading) && (
            <ResultsDisplay results={results} isLoading={loadingState} />
          )}
        </div>
      </main>
    </div>
  )
}

