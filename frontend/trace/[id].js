"use client"
import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import TraceWaterfall from '../../../components/TraceWaterfall'

interface Span {
  traceId: string
  spanId: string
  parentSpanId?: string | null
  name: string
  serviceName: string
  startTime: number
  duration: number
  statusCode: string
  attributes: Record<string, any>
}

interface TraceData {
  traceId: string
  rootService: string
  totalDuration: number
  spans: Span[]
  total_spans: number
}

export default function TraceDetail() {
  const params = useParams()
  const router = useRouter()
  const traceId = params.id as string
  const [trace, setTrace] = useState<TraceData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (traceId) {
      fetchTrace()
    }
  }, [traceId])

  const fetchTrace = async () => {
    try {
      const res = await fetch(`http://localhost:8002/traces/${traceId}`)
      
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`)
      }
      
      const data = await res.json()
      
      if (data.error) {
        setError('Trace not found')
      } else {
        setTrace(data)
      }
    } catch (err) {
      console.error('Failed to fetch trace:', err)
      setError('Failed to fetch trace. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading trace...</p>
        </div>
      </div>
    )
  }

  if (error || !trace) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
            <p className="text-red-800 mb-4">{error || 'Trace not found'}</p>
            <button 
              onClick={() => router.push('/')}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Back to Traces
            </button>
          </div>
        </div>
      </div>
    )
  }

  const spans: Span[] = trace.spans || []
  const services = Array.from(new Set(spans.map(s => s.serviceName)))
  const errorSpans = spans.filter(s => s.statusCode !== 'OK')

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-4">
          <button 
            onClick={() => router.push('/')}
            className="text-blue-600 hover:text-blue-800 flex items-center"
          >
            ← Back to Traces
          </button>
        </div>

        {/* Trace Summary */}
        <div className="bg-white shadow rounded-lg p-6 mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Trace Details
          </h1>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <div className="text-gray-500">Trace ID</div>
              <div className="font-mono font-medium">{trace.traceId.slice(-12)}</div>
            </div>
            <div>
              <div className="text-gray-500">Root Service</div>
              <div className="font-medium">{trace.rootService}</div>
            </div>
            <div>
              <div className="text-gray-500">Duration</div>
              <div className="font-medium">{(trace.totalDuration / 1000).toFixed(2)}ms</div>
            </div>
            <div>
              <div className="text-gray-500">Spans</div>
              <div className="font-medium">{spans.length}</div>
            </div>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Waterfall */}
          <div className="lg:col-span-2">
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">Waterfall Timeline</h2>
              {spans.length > 0 ? (
                <TraceWaterfall spans={spans} />
              ) : (
                <p className="text-gray-500">No span data available</p>
              )}
            </div>
          </div>
          
          {/* Sidebar */}
          <div className="space-y-4">
            {/* Services */}
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">Services</h2>
              <div className="space-y-2">
                {services.map(service => (
                  <div key={service} className="flex items-center space-x-2 text-sm">
                    <div 
                      className="w-3 h-3 rounded-full" 
                      style={{backgroundColor: getServiceColor(service)}} 
                    />
                    <span className="font-medium">{service}</span>
                    <span className="text-gray-500">
                      ({spans.filter(s => s.serviceName === service).length})
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Errors */}
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">
                Errors {errorSpans.length > 0 && `(${errorSpans.length})`}
              </h2>
              {errorSpans.length > 0 ? (
                <div className="space-y-2">
                  {errorSpans.map(span => (
                    <div key={span.spanId} className="p-3 bg-red-50 border border-red-200 rounded text-sm">
                      <div className="font-medium text-red-900">{span.name}</div>
                      <div className="text-red-700">{span.serviceName}</div>
                      <div className="text-xs text-red-600 mt-1">
                        {span.statusCode}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-sm">No errors detected</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function getServiceColor(service: string): string {
  const colors = ['#EF4444', '#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899', '#6366F1']
  let hash = 0
  for (let i = 0; i < service.length; i++) {
    hash = service.charCodeAt(i) + ((hash << 5) - hash)
  }
  return colors[Math.abs(hash) % colors.length]
}