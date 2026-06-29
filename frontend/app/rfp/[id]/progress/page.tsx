'use client'

import { useEffect, useState, useRef } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { Copy, Check, ArrowRight } from 'lucide-react'
import Navigation from '@/components/Navigation'
import StepItem from '@/components/StepItem'

type StepStatus = 'pending' | 'active' | 'complete'

interface Step {
  id: number
  title: string
  description: string
  status: StepStatus
  timestamp?: string
}

const STEPS: Step[] = [
  { id: 1, title: 'Supplier Discovery', description: 'Searching supplier database by category and rating', status: 'pending' },
  { id: 2, title: 'RFP Document Created', description: 'Generating Word document with full specifications', status: 'pending' },
  { id: 3, title: 'Emails Dispatched', description: 'Sending RFP to qualified suppliers via SES', status: 'pending' },
  { id: 4, title: 'Proposals Collected', description: 'Retrieving supplier proposals from database', status: 'pending' },
  { id: 5, title: 'Proposals Scored', description: 'Price 30%, Quality 30%, Delivery 20%, Compliance 20%', status: 'pending' },
  { id: 6, title: 'Recommendation Ready', description: 'Top 2 suppliers identified and ranked', status: 'pending' },
]

function getTimestamp() {
  return new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

export default function ProgressPage() {
  const params = useParams()
  const router = useRouter()
  const rfpId = params.id as string
  const API_URL = process.env.NEXT_PUBLIC_API_URL || ''

  const [steps, setSteps] = useState<Step[]>(STEPS.map(s => ({ ...s })))
  const [copied, setCopied] = useState(false)
  const [complete, setComplete] = useState(false)
  const [suppliers, setSuppliers] = useState<string[]>([])
  const [agentResponse, setAgentResponse] = useState('')
  const pollRef = useRef<NodeJS.Timeout | null>(null)
  const stepTimerRef = useRef<NodeJS.Timeout[]>([])
  const completedRef = useRef(false)

  // Show steps as active one by one — never mark complete until API confirms
  useEffect(() => {
    let current = 0
    const advance = () => {
      if (completedRef.current) return
      setSteps(prev => {
        const next = [...prev]
        // Set previous active to pending again (don't mark complete yet)
        if (current > 0) {
          next[current - 1] = { ...next[current - 1], status: 'pending' }
        }
        if (current < next.length) {
          next[current] = { ...next[current], status: 'active' }
          current++
        }
        return next
      })
    }

    const delays = [500, 12000, 22000, 35000, 50000, 65000]
    stepTimerRef.current = delays.map((d) => setTimeout(advance, d))
    return () => stepTimerRef.current.forEach(clearTimeout)
  }, [])

  // Poll real API for completion
  useEffect(() => {
    const poll = async () => {
      try {
        const res = await fetch(`${API_URL}/rfp/${rfpId}`)
        const data = await res.json()

        if (data.status === 'complete' || data.status === 'error') {
          if (!completedRef.current) {
            completedRef.current = true
            setSteps(prev => prev.map(s => ({
              ...s,
              status: 'complete' as StepStatus,
              timestamp: s.timestamp || getTimestamp()
            })))
            setAgentResponse(data.agent_response || '')

            // Extract real supplier IDs from agent response
            const supMatches = (data.agent_response || '').match(/SUP\d+/g)
            if (supMatches) {
              const unique = [...new Set(supMatches)] as string[]
              setSuppliers(unique.slice(0, 5))
            }

            setComplete(true)
            if (pollRef.current) clearInterval(pollRef.current)
          }
        }
      } catch (err) {
        console.error('Poll error:', err)
      }
    }

    // Start polling after 10 seconds
    const startTimer = setTimeout(() => {
      poll() // immediate first poll
      pollRef.current = setInterval(poll, 5000)
    }, 10000)

    return () => {
      clearTimeout(startTimer)
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [rfpId, API_URL])

  const handleCopy = () => {
    navigator.clipboard.writeText(rfpId)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const completedCount = steps.filter(s => s.status === 'complete').length

  return (
    <div className="min-h-screen bg-[#EDE8DC]">
      <Navigation />
      <main className="max-w-6xl mx-auto px-6 py-10">

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="flex items-center justify-between mb-8"
        >
          <div>
            <p className="text-xs tracking-[0.15em] uppercase text-[#7A7265] mb-1">RFP Process</p>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-mono font-medium text-[#2C2C2C]">{rfpId}</h1>
              <button onClick={handleCopy} className="w-7 h-7 flex items-center justify-center rounded-md hover:bg-[#D4CBB8]/50 transition-colors">
                {copied ? <Check className="w-3.5 h-3.5 text-[#5C8A4A]" /> : <Copy className="w-3.5 h-3.5 text-[#7A7265]" />}
              </button>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {complete ? (
              <span className="px-3 py-1 bg-[#5C8A4A]/10 border border-[#5C8A4A]/20 text-[#5C8A4A] text-xs font-medium rounded-full">Complete</span>
            ) : (
              <span className="px-3 py-1 bg-[#E8A020]/10 border border-[#E8A020]/20 text-[#E8A020] text-xs font-medium rounded-full animate-pulse">In Progress</span>
            )}
            <span className="text-xs text-[#7A7265]">{completedCount} / {steps.length} steps</span>
          </div>
        </motion.div>

        <div className="grid grid-cols-3 gap-6">
          {/* Steps */}
          <div className="col-span-2 flex flex-col gap-2">
            {steps.map((step, i) => (
              <StepItem
                key={step.id}
                number={step.id}
                title={step.title}
                description={step.description}
                status={step.status}
                timestamp={step.timestamp}
                delay={i * 0.05}
              />
            ))}

            <AnimatePresence>
              {complete && (
                <motion.div
                  initial={{ opacity: 0, y: 16, scale: 0.97 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  transition={{ duration: 0.5, ease: 'easeOut' }}
                  className="mt-2 p-4 bg-[#F5F1E8] border border-[#5C8A4A]/20 rounded-xl flex items-center justify-between shadow-warm-sm"
                >
                  <div>
                    <p className="text-sm font-medium text-[#2C2C2C]">Analysis Complete</p>
                    <p className="text-xs text-[#7A7265] mt-0.5">All 6 steps finished · AI recommendation ready</p>
                  </div>
                  <button
                    onClick={() => router.push(`/rfp/${rfpId}/recommendation`)}
                    className="flex items-center gap-2 px-4 py-2 bg-[#E8A020] text-white text-sm font-medium rounded-lg hover:bg-[#C97B1A] transition-colors shadow-sm"
                  >
                    View Report
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Suppliers panel */}
          <div>
            <p className="text-xs tracking-[0.15em] uppercase text-[#7A7265] font-medium mb-3">Suppliers Found</p>
            <div className="flex flex-col gap-2">
              <AnimatePresence>
                {suppliers.length === 0 ? (
                  [1, 2, 3].map(i => <div key={i} className="h-14 rounded-xl shimmer" />)
                ) : (
                  suppliers.map((sup, i) => (
                    <motion.div
                      key={sup}
                      initial={{ opacity: 0, x: 16 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.4, delay: i * 0.12 }}
                      className="p-3 bg-[#F5F1E8] border border-[#D4CBB8]/40 rounded-xl border-l-2 border-l-[#E8A020]/60"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-mono text-[#2C2C2C]">{sup}</span>
                        <span className="text-xs px-2 py-0.5 bg-[#EDE8DC] rounded-full text-[#7A7265]">Sensors</span>
                      </div>
                      <div className="flex items-center gap-0.5 mt-1">
                        {[1, 2, 3, 4, 5].map(s => (
                          <div key={s} className={`w-2 h-2 rounded-full ${s <= 4 ? 'bg-[#E8A020]' : 'bg-[#D4CBB8]'}`} />
                        ))}
                        <span className="text-xs text-[#7A7265] ml-1">4.0</span>
                      </div>
                    </motion.div>
                  ))
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
