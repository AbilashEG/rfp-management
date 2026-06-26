'use client'

import { useEffect, useRef } from 'react'
import { motion, useInView, useMotionValue, useTransform, animate } from 'framer-motion'

interface ScoreRingProps {
  score: number
  size?: number
  strokeWidth?: number
  color?: string
}

export default function ScoreRing({
  score,
  size = 120,
  strokeWidth = 8,
  color = '#E8A020',
}: ScoreRingProps) {
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const count = useMotionValue(0)
  const displayScore = useTransform(count, (v) => Math.round(v).toFixed(1))
  const ref = useRef(null)
  const inView = useInView(ref, { once: true })

  useEffect(() => {
    if (inView) {
      animate(count, score, { duration: 1.4, ease: 'easeOut' })
    }
  }, [inView, score, count])

  const strokeDashoffset = useTransform(
    count,
    [0, 100],
    [circumference, circumference - (circumference * score) / 100]
  )

  return (
    <div ref={ref} className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        {/* Background ring */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#D4CBB8"
          strokeWidth={strokeWidth}
        />
        {/* Animated ring */}
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          style={{ strokeDashoffset }}
        />
      </svg>
      {/* Score text */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <motion.span className="text-3xl font-light text-[#2C2C2C] leading-none">
          {displayScore}
        </motion.span>
        <span className="text-xs text-[#7A7265] mt-0.5">/100</span>
      </div>
    </div>
  )
}
