"use client"
import { useState, useEffect } from 'react'
import TraceList from '../components/TraceList'

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h1 className="text-4xl font-extrabold text-gray-900 sm:text-5xl md:text-6xl">
            Distributed Tracing
          </h1>
          <p className="mt-3 max-w-md mx-auto text-xl text-gray-500 sm:text-2xl">
            Honeycomb-style observability platform
          </p>
        </div>
        <div className="mt-12">
          <TraceList />
        </div>
      </div>
    </main>
  )
}
