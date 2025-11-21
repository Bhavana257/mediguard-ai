import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'MediGuard AI - Healthcare Fraud Detection',
  description: 'Multi-agent AI system for healthcare fraud detection and discharge management',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}

