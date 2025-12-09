"use client"
import React from "react"

interface Span {
  spanId: string
  parentSpanId?: string | null
  name: string
  startTimeUnixNano: number
  endTimeUnixNano: number
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
  return COLORS[Math.abs(hash) % COLORS.length]
}

export default function TraceWaterfall({ spans }: Props) {
  if (!spans || spans.length === 0) return <p>No span data</p>

  const minStart = Math.min(...spans.map(s => s.startTimeUnixNano))
  const maxEnd = Math.max(...spans.map(s => s.endTimeUnixNano))
  const totalDuration = maxEnd - minStart

  return (
    <div className="space-y-2">
      {spans.map((span) => {
        const leftPercent = ((span.startTimeUnixNano - minStart) / totalDuration) * 100
        const widthPercent = ((span.endTimeUnixNano - span.startTimeUnixNano) / totalDuration) * 100
        const color = getColor(span.serviceName)
        const spanDuration = (span.endTimeUnixNano - span.startTimeUnixNano) / 1_000_000

        return (
          <div
            key={span.spanId}
            className="relative h-8 bg-gray-100 rounded group"
            title={`${span.name} - ${span.serviceName} - ${spanDuration.toFixed(2)}ms`}
          >
            <span
              className="absolute h-8 rounded opacity-80 hover:opacity-100 transition"
              style={{
                left: `${leftPercent}%`,
                width: `${widthPercent}%`,
                backgroundColor: color,
                border: span.statusCode === 'ERROR' ? '2px solid red' : 'none'
              }}
            />
            <div className="absolute left-1 top-1 text-xs font-mono text-white truncate">
              {span.name}
            </div>
            <div className="absolute right-1 top-1 text-xs text-white font-semibold">
              {spanDuration.toFixed(2)}ms
            </div>
          </div>
        )
      })}
    </div>
  )
}
