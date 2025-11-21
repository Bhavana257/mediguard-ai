'use client'

import { useState, useEffect } from 'react'

interface PatientInputProps {
  onAnalyze: (patientId: string) => void
  isLoading: boolean
}

export default function PatientInput({ onAnalyze, isLoading }: PatientInputProps) {
  const [patientId, setPatientId] = useState('')
  const [sampleIds, setSampleIds] = useState<string[]>([])

  useEffect(() => {
    // Fetch sample patient IDs
    fetch('/api/sample-ids')
      .then(res => res.json())
      .then(data => setSampleIds(data.ids || []))
      .catch(() => setSampleIds([]))
  }, [])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (patientId.trim()) {
      onAnalyze(patientId.trim())
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h2 className="text-xl font-semibold text-gray-800 mb-4">Patient Analysis</h2>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="patientId" className="block text-sm font-medium text-gray-700 mb-2">
            Patient ID (UUID)
          </label>
          <input
            type="text"
            id="patientId"
            value={patientId}
            onChange={(e) => setPatientId(e.target.value)}
            placeholder="Enter patient UUID or select from samples"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
            disabled={isLoading}
          />
        </div>

        {sampleIds.length > 0 && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Sample Patient IDs
            </label>
            <div className="grid grid-cols-2 gap-2">
              {sampleIds.slice(0, 4).map((id, index) => (
                <button
                  key={id}
                  type="button"
                  onClick={() => setPatientId(id)}
                  className="text-left px-3 py-2 text-sm bg-gray-50 hover:bg-gray-100 rounded border border-gray-200 text-gray-700 truncate"
                  disabled={isLoading}
                >
                  {id}
                </button>
              ))}
            </div>
          </div>
        )}

        <button
          type="submit"
          disabled={!patientId.trim() || isLoading}
          className="w-full bg-primary hover:bg-primary/90 text-white font-medium py-3 px-4 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center space-x-2"
        >
          {isLoading ? (
            <>
              <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span>Analyzing...</span>
            </>
          ) : (
            <>
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
              </svg>
              <span>Start Analysis</span>
            </>
          )}
        </button>
      </form>
    </div>
  )
}

