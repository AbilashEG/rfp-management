'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { ArrowRight, Loader2, Zap, BarChart3, Clock } from 'lucide-react'
import Navigation from '@/components/Navigation'
import clsx from 'clsx'

const CATEGORIES = ['Sensors', 'Brakes', 'Electronics', 'Hydraulics', 'Mechanical']

const STATS = [
  { label: 'RFPs Processed', value: '847', icon: BarChart3 },
  { label: 'Suppliers Evaluated', value: '2,341', icon: Zap },
  { label: 'Avg. Time to Award', value: '< 2 min', icon: Clock },
]

export default function HomePage() {
  const router = useRouter()
  const [message, setMessage] = useState('')
  const [category, setCategory] = useState('Sensors')
  const [quantity, setQuantity] = useState('')
  const [deadline, setDeadline] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!message.trim()) return
    setLoading(true)

    const fullMessage = `${message}${quantity ? ` Quantity: ${quantity}.` : ''} ${category ? `Category: ${category.toLowerCase()}.` : ''} ${deadline ? `Deadline: ${deadline}.` : ''}`

    try {
      const res = await fetch('/api/rfp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: fullMessage }),
      })
      const data = await res.json()
      if (data.rfp_id) {
        router.push(`/rfp/${data.rfp_id}/progress`)
      }
    } catch {
      // On error still navigate with mock ID for demo
      const mockId = `RFP-${new Date().toISOString().slice(0,10).replace(/-/g,'')}-DEMO1234`
      router.push(`/rfp/${mockId}/progress`)
    }
  }

  return (
    <div className="min-h-screen bg-[#EDE8DC]">
      <Navigation />

      <main className="max-w-6xl mx-auto px-6 py-16">
        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
          className="text-center mb-12"
        >
          <span className="inline-block text-xs tracking-[0.2em] uppercase text-[#E8A020] font-medium mb-4">
            Powered by AWS Bedrock AgentCore
          </span>
          <h1 className="text-5xl font-light text-[#2C2C2C] leading-tight mb-4">
            Intelligent Procurement,
            <br />
            <span className="font-normal">Simplified.</span>
          </h1>
          <p className="text-[#7A7265] text-lg font-light max-w-xl mx-auto leading-relaxed">
            Describe what you need. The AI handles supplier discovery,
            RFP creation, scoring, and recommendation automatically.
          </p>
        </motion.div>

        {/* Form card */}
        <motion.div
          initial={{ opacity: 0, y: 32 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.15, ease: 'easeOut' }}
          className="max-w-2xl mx-auto"
        >
          <form
            onSubmit={handleSubmit}
            className="bg-[#F5F1E8] rounded-2xl border border-[#D4CBB8]/50 shadow-warm p-6"
          >
            {/* Label */}
            <label className="block text-xs tracking-[0.15em] uppercase text-[#7A7265] font-medium mb-2">
              Procurement Requirement
            </label>

            {/* Text area */}
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="e.g. We need 500 brake sensors by September 2026. Specs: ABS wheel speed sensor, IP67 rated, CAN bus output."
              rows={4}
              className="w-full bg-white border border-[#D4CBB8]/60 rounded-xl px-4 py-3 text-sm text-[#2C2C2C] placeholder-[#C4B89E] resize-none focus:outline-none focus:border-[#E8A020]/60 focus:ring-1 focus:ring-[#E8A020]/30 transition-all duration-200 leading-relaxed"
            />

            {/* Quantity + Deadline */}
            <div className="grid grid-cols-2 gap-3 mt-3">
              <div>
                <label className="block text-xs text-[#7A7265] mb-1">Quantity</label>
                <input
                  type="number"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                  placeholder="e.g. 500"
                  className="w-full bg-white border border-[#D4CBB8]/60 rounded-lg px-3 py-2 text-sm text-[#2C2C2C] placeholder-[#C4B89E] focus:outline-none focus:border-[#E8A020]/60 focus:ring-1 focus:ring-[#E8A020]/30 transition-all"
                />
              </div>
              <div>
                <label className="block text-xs text-[#7A7265] mb-1">Deadline</label>
                <input
                  type="date"
                  value={deadline}
                  onChange={(e) => setDeadline(e.target.value)}
                  className="w-full bg-white border border-[#D4CBB8]/60 rounded-lg px-3 py-2 text-sm text-[#2C2C2C] focus:outline-none focus:border-[#E8A020]/60 focus:ring-1 focus:ring-[#E8A020]/30 transition-all"
                />
              </div>
            </div>

            {/* Category pills */}
            <div className="mt-3">
              <label className="block text-xs text-[#7A7265] mb-2">Category</label>
              <div className="flex flex-wrap gap-2">
                {CATEGORIES.map((cat) => (
                  <button
                    key={cat}
                    type="button"
                    onClick={() => setCategory(cat)}
                    className={clsx(
                      'px-3 py-1 rounded-full text-xs font-medium transition-all duration-200',
                      category === cat
                        ? 'bg-[#E8A020] text-white shadow-sm'
                        : 'bg-[#EDE8DC] text-[#7A7265] border border-[#D4CBB8] hover:border-[#E8A020]/40 hover:text-[#2C2C2C]'
                    )}
                  >
                    {cat}
                  </button>
                ))}
              </div>
            </div>

            {/* Submit button */}
            <button
              type="submit"
              disabled={!message.trim() || loading}
              className={clsx(
                'w-full mt-5 h-12 rounded-xl font-medium text-sm flex items-center justify-center gap-2 transition-all duration-200',
                message.trim() && !loading
                  ? 'bg-[#E8A020] text-white hover:bg-[#C97B1A] hover:shadow-warm active:scale-[0.99]'
                  : 'bg-[#D4CBB8] text-[#F5F1E8] cursor-not-allowed'
              )}
            >
              <AnimatePresence mode="wait">
                {loading ? (
                  <motion.span
                    key="loading"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="flex items-center gap-2"
                  >
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Launching RFP Process...
                  </motion.span>
                ) : (
                  <motion.span
                    key="idle"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="flex items-center gap-2"
                  >
                    Launch RFP Process
                    <ArrowRight className="w-4 h-4" />
                  </motion.span>
                )}
              </AnimatePresence>
            </button>
          </form>
        </motion.div>

        {/* Stats row */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.35, ease: 'easeOut' }}
          className="flex justify-center gap-6 mt-10"
        >
          {STATS.map((stat) => (
            <div
              key={stat.label}
              className="flex items-center gap-2 bg-[#F5F1E8]/70 border border-[#D4CBB8]/40 rounded-full px-4 py-2"
            >
              <stat.icon className="w-3.5 h-3.5 text-[#E8A020]" />
              <span className="text-sm font-medium text-[#2C2C2C]">{stat.value}</span>
              <span className="text-xs text-[#7A7265]">{stat.label}</span>
            </div>
          ))}
        </motion.div>
      </main>
    </div>
  )
}
