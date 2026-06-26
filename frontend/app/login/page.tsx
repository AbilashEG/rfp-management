'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { Loader2, Eye, EyeOff } from 'lucide-react'

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPass, setShowPass] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email || !password) { setError('Please enter your credentials'); return }
    setLoading(true)
    setError('')
    // Simulate auth delay for demo
    await new Promise(r => setTimeout(r, 1200))
    localStorage.setItem('rfp_auth', 'true')
    router.push('/')
  }

  return (
    <div className="min-h-screen bg-[#EDE8DC] flex flex-col items-center justify-center px-4">
      {/* Top brand */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="mb-10 text-center"
      >
        <div className="w-12 h-12 rounded-xl bg-[#2C2C2C] flex items-center justify-center mx-auto mb-4">
          <span className="text-[#EDE8DC] text-xl font-semibold">Q</span>
        </div>
        <h1 className="text-2xl font-light text-[#2C2C2C] tracking-tight">RFP Management</h1>
        <p className="text-xs tracking-[0.2em] uppercase text-[#E8A020] mt-1 font-medium">
          Powered by AWS Bedrock AgentCore
        </p>
      </motion.div>

      {/* Login card */}
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="w-full max-w-sm bg-[#F5F1E8] border border-[#D4CBB8]/50 rounded-2xl shadow-warm p-8"
      >
        <h2 className="text-lg font-medium text-[#2C2C2C] mb-1">Sign in</h2>
        <p className="text-sm text-[#7A7265] mb-6">Access your procurement dashboard</p>

        <form onSubmit={handleLogin} className="flex flex-col gap-4">
          <div>
            <label className="block text-xs tracking-[0.1em] uppercase text-[#7A7265] mb-1.5">Email</label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="you@quadra.com"
              className="w-full bg-white border border-[#D4CBB8]/60 rounded-lg px-3 py-2.5 text-sm text-[#2C2C2C] placeholder-[#C4B89E] focus:outline-none focus:border-[#E8A020]/60 focus:ring-1 focus:ring-[#E8A020]/20 transition-all"
            />
          </div>

          <div>
            <label className="block text-xs tracking-[0.1em] uppercase text-[#7A7265] mb-1.5">Password</label>
            <div className="relative">
              <input
                type={showPass ? 'text' : 'password'}
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-white border border-[#D4CBB8]/60 rounded-lg px-3 py-2.5 text-sm text-[#2C2C2C] placeholder-[#C4B89E] focus:outline-none focus:border-[#E8A020]/60 focus:ring-1 focus:ring-[#E8A020]/20 transition-all pr-10"
              />
              <button type="button" onClick={() => setShowPass(!showPass)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[#C4B89E] hover:text-[#7A7265] transition-colors">
                {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {error && <p className="text-xs text-[#A63D2F] bg-[#FDF2F0] border border-[#A63D2F]/20 rounded-lg px-3 py-2">{error}</p>}

          <button type="submit" disabled={loading}
            className="w-full h-11 rounded-xl bg-[#E8A020] text-white text-sm font-medium flex items-center justify-center gap-2 hover:bg-[#C97B1A] transition-colors mt-1 disabled:opacity-70">
            {loading ? <><Loader2 className="w-4 h-4 animate-spin" />Signing in...</> : 'Sign in'}
          </button>
        </form>

        <div className="mt-4 pt-4 border-t border-[#D4CBB8]/40">
          <p className="text-xs text-[#7A7265] text-center">
            Demo credentials: <span className="text-[#2C2C2C] font-medium">any email + any password</span>
          </p>
        </div>
      </motion.div>

      {/* Footer */}
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
        className="text-xs text-[#C4B89E] mt-8"
      >
        © 2026 Quadra Systems · Confidential
      </motion.p>
    </div>
  )
}
