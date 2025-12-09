import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Distributed Tracing - Observability Platform',
  description: 'High-cardinality distributed tracing system with OpenTelemetry',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <nav className="bg-white shadow-sm border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16 items-center">
              <div className="flex items-center">
                <div className="text-2xl font-bold text-blue-600">
                  🔍 Tracing
                </div>
                <div className="ml-4 text-sm text-gray-500">
                  Distributed Observability Platform
                </div>
              </div>
              <div className="flex space-x-4">
                <a href="/" className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium">
                  Traces
                </a>
                <a href="#" className="text-gray-400 px-3 py-2 rounded-md text-sm font-medium cursor-not-allowed">
                  Services
                </a>
                <a href="#" className="text-gray-400 px-3 py-2 rounded-md text-sm font-medium cursor-not-allowed">
                  Analytics
                </a>
              </div>
            </div>
          </div>
        </nav>
        {children}
      </body>
    </html>
  )
}