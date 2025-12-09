"use client"
import React from "react"

interface Span {
  spanId: string
  parentSpanId?: string | null
  name: string
  startTime: number // in microseconds
  duration: number  // in microseconds
  serviceName: string
  statusCode: string
}

interface Props {
  spans: Span[]
}

const COLORS = [
  "#EF4444", "#3B82F6", "#10B981", "#F59E0B",
  "#8B5CF6", "#EC4899", "#6366F1", "#22D3EE"
]

function getColor(serviceName: string) {
  let hash = 0
  for (let i = 0; i < serviceName.length; i++) {
    hash = serviceName.charCodeAt(i) + ((hash << 5) - hash)
  }
  const index = Math.abs(hash) % COLORS.length
  return COLORS[index]
}

export default function TraceWaterfall({ spans }: Props) {
  if (!spans || spans.length === 0) return <p>No span data</p>

  // Find start time of trace
  const minStart = Math.min(...spans.map(s => s.startTime))
  const maxEnd = Math.max(...spans.map(s => s.startTime + s.duration))
  const totalDuration = maxEnd - minStart

  return (
    <div className="space-y-2">
      {spans.map((span) => {
        const leftPercent = ((span.startTime - minStart) / totalDuration) * 100
        const widthPercent = (span.duration / totalDuration) * 100
        const color = getColor(span.serviceName)

        return (
          <div key={span.spanId} className="relative h-8 bg-gray-100 rounded">
            <span
              className="absolute h-8 rounded"
              style={{
                left: `${leftPercent}%`,
                width: `${widthPercent}%`,
                backgroundColor: color,
              }}
              title={`${span.name} (${span.serviceName}) ${span.duration / 1000} ms`}
            />
            <div className="absolute left-1 top-1 text-xs font-mono text-white">
              {span.name}
            </div>
          </div>
        )
      })}
    </div>
  )
}
