"use client"
import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

interface Trace {
  traceId: string
  rootService: string
  totalDuration: number
  hasError: boolean
  services: string[]
}

export default function TraceList() {
  const [traces, setTraces] = useState<Trace[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()

  useEffect(() => {
    fetchTraces()
    
    const interval = setInterval(fetchTraces, 5000)
    return () => clearInterval(interval)
  }, [])

  const fetchTraces = async () => {
    try {
      const res = await fetch('http://localhost:8002/search?limit=20')
      
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`)
      }
      
      const data = await res.json()
      setTraces(data)
      setError(null)
    } catch (err) {
      console.error('Failed to fetch traces:', err)
      setError('Failed to fetch traces. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
        <p className="mt-4 text-gray-600">Loading traces...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 max-w-md mx-auto">
          <p className="text-red-800">{error}</p>
          <button 
            onClick={fetchTraces}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (traces.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">No traces found. Generate some traffic to see traces.</p>
        <button 
          onClick={fetchTraces}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Refresh
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold text-gray-900">Recent Traces</h2>
        <button 
          onClick={fetchTraces}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Refresh
        </button>
      </div>

      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {traces.map((trace) => (
            <li 
              key={trace.traceId} 
              className="px-6 py-4 hover:bg-gray-50 cursor-pointer transition-colors" 
              onClick={() => router.push(`/traces/${trace.traceId}`)}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3">
                    <div className="text-sm font-mono font-medium text-gray-900">
                      {trace.traceId.slice(-12)}
                    </div>
                    {trace.hasError && (
                      <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">
                        ERROR
                      </span>
                    )}
                  </div>
                  <div className="mt-1 text-sm text-gray-500">
                    <span className="font-medium">{trace.rootService}</span>
                    {' • '}
                    {trace.services.length} service{trace.services.length !== 1 ? 's' : ''}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium text-gray-900">
                    {(trace.totalDuration / 1000).toFixed(2)}ms
                  </div>
                  <div className="text-xs text-gray-500">
                    {trace.services.join(', ')}
                  </div>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

