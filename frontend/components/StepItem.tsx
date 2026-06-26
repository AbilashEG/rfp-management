'use client'

import { motion } from 'framer-motion'
import { Check, Loader2 } from 'lucide-react'
import clsx from 'clsx'

interface StepItemProps {
  number: number
  title: string
  description: string
  status: 'pending' | 'active' | 'complete'
  timestamp?: string
  delay?: number
}

export default function StepItem({
  number,
  title,
  description,
  status,
  timestamp,
  delay = 0,
}: StepItemProps) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -16 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4, delay, ease: 'easeOut' }}
      className={clsx(
        'flex gap-4 p-4 rounded-xl border transition-all duration-500',
        status === 'complete' && 'bg-[#F5F1E8] border-[#5C8A4A]/20 shadow-warm-sm',
        status === 'active' && 'bg-[#FDF3E0] border-[#E8A020]/30 shadow-warm-sm',
        status === 'pending' && 'bg-[#F5F1E8]/40 border-[#D4CBB8]/40',
      )}
    >
      {/* Step indicator */}
      <div className="shrink-0 mt-0.5">
        {status === 'complete' && (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', stiffness: 400, damping: 20 }}
            className="w-7 h-7 rounded-full bg-[#5C8A4A] flex items-center justify-center"
          >
            <Check className="w-3.5 h-3.5 text-white" strokeWidth={2.5} />
          </motion.div>
        )}
        {status === 'active' && (
          <div className="w-7 h-7 rounded-full bg-[#E8A020]/15 border border-[#E8A020]/40 flex items-center justify-center">
            <Loader2 className="w-3.5 h-3.5 text-[#E8A020] animate-spin" />
          </div>
        )}
        {status === 'pending' && (
          <div className="w-7 h-7 rounded-full bg-[#EDE8DC] border border-[#D4CBB8] flex items-center justify-center">
            <span className="text-xs text-[#C4B89E] font-medium">{number}</span>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2">
          <span
            className={clsx(
              'text-sm font-medium',
              status === 'pending' ? 'text-[#C4B89E]' : 'text-[#2C2C2C]'
            )}
          >
            {title}
          </span>
          {timestamp && status === 'complete' && (
            <span className="text-xs text-[#7A7265] shrink-0">{timestamp}</span>
          )}
          {status === 'active' && (
            <span className="text-xs text-[#E8A020] animate-pulse">In progress...</span>
          )}
        </div>
        <p
          className={clsx(
            'text-xs mt-0.5 leading-relaxed',
            status === 'pending' ? 'text-[#C4B89E]' : 'text-[#7A7265]'
          )}
        >
          {description}
        </p>
      </div>
    </motion.div>
  )
}
