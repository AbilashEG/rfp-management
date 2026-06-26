'use client'

import { useRef } from 'react'
import { motion, useInView } from 'framer-motion'

interface ScoreBarProps {
  label: string
  weight: string
  value: number
  delay?: number
}

export default function ScoreBar({ label, weight, value, delay = 0 }: ScoreBarProps) {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true })

  return (
    <div ref={ref} className="flex items-center gap-3">
      <div className="w-28 shrink-0">
        <span className="text-xs text-[#7A7265]">{label}</span>
        <span className="text-xs text-[#C4B89E] ml-1">({weight})</span>
      </div>
      <div className="flex-1 h-1.5 bg-[#D4CBB8]/50 rounded-full overflow-hidden">
        <motion.div
          className="h-full bg-[#E8A020] rounded-full"
          initial={{ width: 0 }}
          animate={inView ? { width: `${value}%` } : { width: 0 }}
          transition={{ duration: 0.8, delay, ease: 'easeOut' }}
        />
      </div>
      <span className="text-xs text-[#2C2C2C] font-medium w-8 text-right">
        {value.toFixed(1)}
      </span>
    </div>
  )
}
