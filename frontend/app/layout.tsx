import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'RFP Management — Quadra',
  description: 'AI-powered supplier procurement and RFP management',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-[#EDE8DC]">
        {children}
      </body>
    </html>
  )
}
