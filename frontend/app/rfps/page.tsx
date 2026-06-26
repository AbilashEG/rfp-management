'use client'

import { motion } from 'framer-motion'
import { useRouter } from 'next/navigation'
import Navigation from '@/components/Navigation'
import clsx from 'clsx'

const MOCK_RFPS = [
  { id: 'RFP-20260625-B81BD7CF', requirement: '500 brake sensors, ABS wheel speed, IP67', category: 'Sensors', status: 'awarded', supplier: 'SUP005', date: 'Jun 25, 2026' },
  { id: 'RFP-20260619-F8A56AB6', requirement: '200 hydraulic pumps, ISO 4401, 350 bar', category: 'Hydraulics', status: 'pending_approval', supplier: null, date: 'Jun 19, 2026' },
  { id: 'RFP-20260618-CC4FF7E7', requirement: '1000 circuit boards, RoHS, SMD mounted', category: 'Electronics', status: 'in_progress', supplier: null, date: 'Jun 18, 2026' },
]

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  awarded: { label: 'Awarded', color: 'text-[#5C8A4A]', bg: 'bg-[#F0F7EE] border-[#5C8A4A]/20' },
  pending_approval: { label: 'Pending Approval', color: 'text-[#C97B1A]', bg: 'bg-[#FDF8EE] border-[#E8A020]/20' },
  in_progress: { label: 'In Progress', color: 'text-[#E8A020]', bg: 'bg-[#FDF3E0] border-[#E8A020]/20' },
}

export default function RFPsPage() {
  const router = useRouter()

  return (
    <div className="min-h-screen bg-[#EDE8DC]">
      <Navigation />
      <main className="max-w-6xl mx-auto px-6 py-10">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="flex items-center justify-between mb-8"
        >
          <div>
            <h1 className="text-2xl font-light text-[#2C2C2C]">Active RFPs</h1>
            <p className="text-sm text-[#7A7265] mt-1">{MOCK_RFPS.length} procurement requests</p>
          </div>
          <button
            onClick={() => router.push('/')}
            className="px-4 py-2 bg-[#E8A020] text-white text-sm font-medium rounded-lg hover:bg-[#C97B1A] transition-colors"
          >
            + New RFP
          </button>
        </motion.div>

        <div className="flex flex-col gap-3">
          {MOCK_RFPS.map((rfp, i) => {
            const st = STATUS_CONFIG[rfp.status]
            return (
              <motion.div
                key={rfp.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.35, delay: i * 0.08 }}
                onClick={() => router.push(`/rfp/${rfp.id}/recommendation`)}
                className="bg-[#F5F1E8] border border-[#D4CBB8]/50 rounded-xl p-4 shadow-warm-sm hover:shadow-warm cursor-pointer transition-all hover:border-[#E8A020]/20 group"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-mono text-[#2C2C2C]">{rfp.id}</span>
                      <span className="text-xs px-2 py-0.5 bg-[#EDE8DC] border border-[#D4CBB8] rounded-full text-[#7A7265]">
                        {rfp.category}
                      </span>
                    </div>
                    <p className="text-sm text-[#7A7265]">{rfp.requirement}</p>
                    {rfp.supplier && (
                      <p className="text-xs text-[#5C8A4A] mt-1">Awarded to {rfp.supplier}</p>
                    )}
                  </div>
                  <div className="flex flex-col items-end gap-2 shrink-0 ml-4">
                    <span className={clsx('text-xs px-2.5 py-1 rounded-full border font-medium', st.color, st.bg)}>
                      {st.label}
                    </span>
                    <span className="text-xs text-[#7A7265]">{rfp.date}</span>
                  </div>
                </div>
              </motion.div>
            )
          })}
        </div>
      </main>
    </div>
  )
}
