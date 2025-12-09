"use client"
import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import TraceWaterfall from '../../components/TraceWaterfall'

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

export default function TraceDetail() {
  const params = useParams()
  const traceId = params.id as string
  const [trace, setTrace] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (traceId) {
      fetch(`http://localhost:8002/traces/${traceId}`)
        .then(res => res.json())
        .then(data => {
          setTrace(data)
          setLoading(false)
        })
        .catch(err => {
          console.error(err)
          setLoading(false)
        })
    }
  }, [traceId])

  if (loading) return <div className="p-8 text-center">Loading trace...</div>
  if (!trace || trace.error) return <div className="p-8 text-center">Trace not found</div>

  const spans: Span[] = trace.spans || []

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="bg-white shadow rounded-lg p-6 mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Trace {trace.traceId?.slice(-8)}</h1>
          <div className="flex gap-4 text-sm text-gray-600">
            <span>Root: {trace.rootService}</span>
            <span>Duration: {(trace.totalDuration / 1000).toFixed(0)}ms</span>
            <span>{spans.length} spans</span>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">Waterfall Timeline</h2>
              <TraceWaterfall spans={spans} />
            </div>
          </div>
          
          <div className="space-y-4">
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">Services</h2>
              <div className="space-y-2">
                {Array.from(new Set(spans.map(s => s.serviceName))).map(service => (
                  <div key={service} className="flex items-center space-x-2 text-sm">
                    <div className="w-3 h-3 rounded-full" style={{backgroundColor: getServiceColor(service)}} />
                    <span>{service}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">Errors</h2>
              {spans.filter(s => s.statusCode !== 'OK').map(span => (
                <div key={span.spanId} className="p-3 bg-red-50 border border-red-200 rounded text-sm">
                  <div className="font-medium">{span.name}</div>
                  <div className="text-gray-600">{span.serviceName}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function getServiceColor(service: string) {
  const colors = ['#EF4444', '#3B82F6', '#10B981', '#F59E0B', '#8B5CF6']
  let hash = 0
  for (let i = 0; i < service.length; i++) {
    hash = service.charCodeAt(i) + ((hash << 5) - hash)
  }
  return colors[Math.abs(hash) % colors.length]
}
