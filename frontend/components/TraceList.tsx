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
  const router = useRouter()

  useEffect(() => {
    fetchTraces()
    
    const interval = setInterval(fetchTraces, 5000)
    return () => clearInterval(interval)
  }, [])

  const fetchTraces = async () => {
    try {
      const res = await fetch('http://localhost:8002/search?limit=20')
      const data = await res.json()
      setTraces(data)
    } catch (error) {
      console.error('Failed to fetch traces:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="text-center py-12">Loading traces...</div>

  return (
    <div className="grid gap-4">
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {traces.map((trace) => (
            <li key={trace.traceId} className="px-6 py-4 hover:bg-gray-50 cursor-pointer" 
                onClick={() => router.push(`/traces/${trace.traceId}`)}>
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium text-gray-900 truncate">
                    {trace.traceId.slice(-8)}
                  </div>
                  <div className="text-sm text-gray-500">
                    {trace.rootService} • {trace.services.length} services
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <span className="text-sm font-medium text-gray-900">
                    {trace.totalDuration / 1000}ms
                  </span>
                  {trace.hasError && (
                    <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">
                      ERROR
                    </span>
                  )}
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
