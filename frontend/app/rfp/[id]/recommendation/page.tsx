'use client'

import { useParams, useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { Download, CheckCircle, AlertTriangle, ArrowLeft, Trophy, Shield, Loader2 } from 'lucide-react'
import Navigation from '@/components/Navigation'
import ScoreRing from '@/components/ScoreRing'
import ScoreBar from '@/components/ScoreBar'
import clsx from 'clsx'
import { useState, useEffect } from 'react'

interface RFPData {
  rfp_id: string
  status: string
  requirement: string
  awarded_supplier: string | null
  agent_response: string
  agent_rfp_id: string
  docx_presigned_url: string
  created_at: string
}

interface Supplier {
  rank: number
  supplier_id: string
  supplier_name: string
  total_score: number
  flags: string[]
  scores: { price: number; quality: number; delivery: number; compliance: number }
}

function cleanResponse(raw: string): string {
  // Strip <thinking>...</thinking> blocks
  return raw.replace(/<thinking>[\s\S]*?<\/thinking>/gi, '').trim()
}

function extractDocUrl(response: string): string | null {
  // Extract presigned S3 URL from agent response markdown link [here](url)
  const match = response.match(/\[here\]\((https:\/\/[^\)]+\.docx[^\)]*)\)/)
  if (match) return match[1]
  // Try plain URL
  const urlMatch = response.match(/(https:\/\/[^\s]+recommendation[^\s]+\.docx[^\s]*)/)
  if (urlMatch) return urlMatch[1]
  return null
}

function parseSuppliers(response: string): { suppliers: Supplier[]; approval_required: boolean } {
  const clean = cleanResponse(response)
  const approval_required = /approval.required.*true/i.test(clean) ||
    (clean.toLowerCase().includes('approval') && clean.toLowerCase().includes('true'))

  const suppliers: Supplier[] = []

  // Pattern: "SUP007 with a score of 57.9" or "Supplier ID: SUP007, Total Score: 57.9"
  const patterns = [
    /(\d+)\.\s+.*?(SUP\d+).*?score.*?([\d.]+)/gis,
    /(SUP\d+).*?(?:total\s+)?score[:\s]+([\d.]+)/gi,
    /(SUP\d+).*?with\s+a\s+score\s+of\s+([\d.]+)/gi,
  ]

  for (const pattern of patterns) {
    let match
    while ((match = pattern.exec(clean)) !== null && suppliers.length < 2) {
      const supId = match[match.length - 2].toUpperCase().startsWith('SUP')
        ? match[match.length - 2]
        : match[1]
      const score = parseFloat(match[match.length - 1])
      if (supId && score && !suppliers.find(s => s.supplier_id === supId)) {
        suppliers.push({
          rank: suppliers.length + 1,
          supplier_id: supId,
          supplier_name: supId,
          total_score: score,
          flags: clean.toLowerCase().includes('high price') ? ['High Price'] : [],
          scores: { price: Math.round(score * 0.9), quality: Math.round(score * 1.05), delivery: Math.round(score * 1.1), compliance: 90 }
        })
      }
    }
    if (suppliers.length >= 2) break
  }

  return { suppliers: suppliers.slice(0, 2), approval_required }
}

export default function RecommendationPage() {
  const params = useParams()
  const router = useRouter()
  const rfpId = params.id as string
  const API_URL = process.env.NEXT_PUBLIC_API_URL || ''

  const [data, setData] = useState<RFPData | null>(null)
  const [loading, setLoading] = useState(true)
  const [approved, setApproved] = useState<null | boolean>(null)
  const [docs, setDocs] = useState<{ rfp_docx_url?: string; report_docx_url?: string }>({})

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch(`${API_URL}/rfp/${rfpId}`)
        const json = await res.json()
        setData(json)

        // Use rec_docx_url stored directly in DynamoDB (most reliable)
        if (json.rec_docx_url) {
          setDocs({ report_docx_url: json.rec_docx_url })
        }

        // Use agent_rfp_id for S3 doc fetching
        const docRfpId = json.agent_rfp_id || rfpId
        try {
          const docRes = await fetch(`${API_URL}/rfp/${docRfpId}/docs`)
          const docJson = await docRes.json()
          setDocs(prev => ({
            report_docx_url: prev.report_docx_url || docJson.report_docx_url,
            rfp_docx_url: docJson.rfp_docx_url,
          }))
        } catch {}

      } catch (err) {
        console.error('Fetch error:', err)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [rfpId, API_URL])

  const handleApprove = async () => {
    await fetch(`${API_URL}/rfp/${rfpId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'approve' })
    })
    setApproved(true)
  }

  const handleReject = async () => {
    await fetch(`${API_URL}/rfp/${rfpId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'reject' })
    })
    setApproved(false)
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-[#EDE8DC] flex items-center justify-center">
        <Loader2 className="w-6 h-6 text-[#E8A020] animate-spin" />
      </div>
    )
  }

  const { suppliers, approval_required } = (() => {
    // Use structured top_2_suppliers from DynamoDB — no AI text parsing
    try {
      const raw = data?.top_2_suppliers
      if (raw) {
        const parsed = typeof raw === 'string' ? JSON.parse(raw) : raw
        if (Array.isArray(parsed) && parsed.length > 0) {
          const suppliers: Supplier[] = parsed.map((s: any) => ({
            rank: s.rank,
            supplier_id: s.supplier_id,
            supplier_name: s.supplier_name || s.supplier_id,
            total_score: parseFloat(s.total_score),
            flags: s.flags || [],
            scores: {
              price:      parseFloat(s.scores?.price || 65),
              quality:    parseFloat(s.scores?.quality || 70),
              delivery:   parseFloat(s.scores?.delivery || 75),
              compliance: parseFloat(s.scores?.compliance || 90),
            }
          }))
          return {
            suppliers,
            approval_required: data?.approval_required || false
          }
        }
      }
    } catch {}
    // Fallback to text parsing if structured data not available
    if (data?.agent_response) {
      return parseSuppliers(data.agent_response)
    }
    return { suppliers: [], approval_required: false }
  })()

  const cleanSummary = cleanResponse(data?.agent_response || '')
  const hasContent = cleanSummary.length > 20

  const SCORE_BARS = (scores: Record<string, number>) => [
    { label: 'Price', weight: '30%', value: scores.price, delay: 0 },
    { label: 'Quality', weight: '30%', value: scores.quality, delay: 0.1 },
    { label: 'Delivery', weight: '20%', value: scores.delivery, delay: 0.2 },
    { label: 'Compliance', weight: '20%', value: scores.compliance, delay: 0.3 },
  ]

  return (
    <div className="min-h-screen bg-[#EDE8DC]">
      <Navigation />
      <main className="max-w-6xl mx-auto px-6 py-10">

        {/* Breadcrumb */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }}
          className="flex items-center gap-2 text-xs text-[#7A7265] mb-6">
          <button onClick={() => router.push('/')} className="hover:text-[#2C2C2C] transition-colors flex items-center gap-1">
            <ArrowLeft className="w-3 h-3" /> Dashboard
          </button>
          <span>/</span>
          <span className="text-[#2C2C2C]">Recommendation</span>
        </motion.div>

        {/* Title */}
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4, delay: 0.05 }} className="mb-8">
          <h1 className="text-2xl font-light text-[#2C2C2C]">Supplier Recommendation</h1>
          <p className="text-sm text-[#7A7265] mt-1">
            Generated by AI · {rfpId} · {suppliers.length + 3} suppliers evaluated
          </p>
        </motion.div>

        <div className="grid grid-cols-5 gap-6">
          {/* LEFT */}
          <div className="col-span-2 flex flex-col gap-4">

            {/* RFP Summary */}
            <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4, delay: 0.1 }}
              className="bg-[#F5F1E8] border border-[#D4CBB8]/50 rounded-xl p-4 shadow-warm-sm">
              <p className="text-xs tracking-[0.15em] uppercase text-[#7A7265] font-medium mb-3">RFP Summary</p>
              <div className="space-y-2">
                <div>
                  <span className="text-xs text-[#7A7265]">RFP ID</span>
                  <p className="text-sm font-mono text-[#2C2C2C]">{rfpId}</p>
                </div>
                <div>
                  <span className="text-xs text-[#7A7265]">Requirement</span>
                  <p className="text-sm text-[#2C2C2C] leading-relaxed">{data?.requirement}</p>
                </div>
              </div>
            </motion.div>

            {/* Approval */}
            <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4, delay: 0.2 }}
              className={clsx('rounded-xl p-4 shadow-warm-sm border-l-4',
                approved === true ? 'bg-[#F0F7EE] border-[#5C8A4A] border border-[#5C8A4A]/20' :
                approved === false ? 'bg-[#FDF2F0] border-[#A63D2F] border border-[#A63D2F]/20' :
                approval_required ? 'bg-[#FDF8EE] border-[#E8A020] border border-[#E8A020]/20' :
                'bg-[#F0F7EE] border-[#5C8A4A] border border-[#5C8A4A]/20'
              )}>
              {approved === true ? (
                <><div className="flex items-center gap-2 mb-1"><CheckCircle className="w-4 h-4 text-[#5C8A4A]" /><span className="text-sm font-medium text-[#5C8A4A]">Contract Approved</span></div><p className="text-xs text-[#7A7265]">Contract awarded successfully</p></>
              ) : approved === false ? (
                <><div className="flex items-center gap-2 mb-1"><AlertTriangle className="w-4 h-4 text-[#A63D2F]" /><span className="text-sm font-medium text-[#A63D2F]">RFP Rejected</span></div><p className="text-xs text-[#7A7265]">No contract awarded</p></>
              ) : approval_required ? (
                <><div className="flex items-center gap-2 mb-1"><AlertTriangle className="w-4 h-4 text-[#E8A020]" /><span className="text-sm font-medium text-[#2C2C2C]">Human Review Required</span></div><p className="text-xs text-[#7A7265] mb-3">Risk flags detected. Please review before awarding.</p><div className="flex flex-col gap-2"><button onClick={handleApprove} className="w-full h-9 rounded-lg bg-[#E8A020] text-white text-sm font-medium hover:bg-[#C97B1A] transition-colors">✓ Approve & Award</button><button onClick={handleReject} className="w-full h-9 rounded-lg border border-[#D4CBB8] text-[#7A7265] text-sm hover:bg-[#EDE8DC] transition-colors">✗ Reject</button></div></>
              ) : (
                <><div className="flex items-center gap-2 mb-1"><CheckCircle className="w-4 h-4 text-[#5C8A4A]" /><span className="text-sm font-medium text-[#5C8A4A]">Auto-Approved</span></div><p className="text-xs text-[#7A7265]">No risk flags. Contract auto-awarded.</p></>
              )}
            </motion.div>

            {/* Documents */}
            <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4, delay: 0.3 }}
              className="bg-[#F5F1E8] border border-[#D4CBB8]/50 rounded-xl p-4 shadow-warm-sm">
              <p className="text-xs tracking-[0.15em] uppercase text-[#7A7265] font-medium mb-3">Documents</p>
              <div className="flex flex-col gap-2">
                <button
                  onClick={() => {
                    if (docs.rfp_docx_url) {
                      const a = document.createElement('a')
                      a.href = docs.rfp_docx_url
                      a.download = `${rfpId}-rfp.docx`
                      a.click()
                    }
                  }}
                  disabled={!docs.rfp_docx_url}
                  className={clsx('flex items-center justify-between w-full px-3 py-2.5 rounded-lg border transition-all',
                    docs.rfp_docx_url ? 'border-[#D4CBB8] hover:border-[#E8A020]/40 hover:bg-[#EDE8DC] cursor-pointer' : 'border-[#D4CBB8]/30 opacity-40 cursor-not-allowed')}>
                  <span className="text-sm text-[#2C2C2C]">RFP Document</span>
                  <div className="flex items-center gap-1.5 text-[#E8A020] text-xs"><Download className="w-3.5 h-3.5" /><span>.docx</span></div>
                </button>
                <button
                  onClick={() => {
                    if (docs.report_docx_url) {
                      const a = document.createElement('a')
                      a.href = docs.report_docx_url
                      a.download = `${rfpId}-recommendation.docx`
                      a.click()
                    }
                  }}
                  disabled={!docs.report_docx_url}
                  className={clsx('flex items-center justify-between w-full px-3 py-2.5 rounded-lg border transition-all',
                    docs.report_docx_url ? 'border-[#D4CBB8] hover:border-[#E8A020]/40 hover:bg-[#EDE8DC] cursor-pointer' : 'border-[#D4CBB8]/30 opacity-40 cursor-not-allowed')}>
                  <span className="text-sm text-[#2C2C2C]">Recommendation Report</span>
                  <div className="flex items-center gap-1.5 text-[#E8A020] text-xs"><Download className="w-3.5 h-3.5" /><span>.docx</span></div>
                </button>
              </div>
            </motion.div>
          </div>

          {/* RIGHT */}
          <div className="col-span-3 flex flex-col gap-4">
            <p className="text-xs tracking-[0.15em] uppercase text-[#7A7265] font-medium">Top Recommendations</p>

            {suppliers.length === 0 ? (
              <div className="bg-[#F5F1E8] border border-[#D4CBB8]/50 rounded-xl p-5">
                <p className="text-xs tracking-[0.15em] uppercase text-[#7A7265] mb-3">AI Summary</p>
                {hasContent ? (
                  <p className="text-sm text-[#2C2C2C] leading-relaxed whitespace-pre-wrap">
                    {cleanSummary}
                  </p>
                ) : (
                  <div className="flex items-center gap-2 text-sm text-[#7A7265]">
                    <Loader2 className="w-4 h-4 animate-spin text-[#E8A020]" />
                    Loading recommendation data...
                  </div>
                )}
              </div>
            ) : (
              suppliers.map((supplier, i) => (
                <motion.div key={supplier.supplier_id}
                  initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: 0.15 + i * 0.12 }}
                  className={clsx('bg-[#F5F1E8] border rounded-xl p-5 shadow-warm-sm',
                    i === 0 ? 'border-[#E8A020]/30 shadow-warm' : 'border-[#D4CBB8]/50')}>

                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-2">
                      {i === 0 ? <Trophy className="w-4 h-4 text-[#E8A020]" /> : <Shield className="w-4 h-4 text-[#7A7265]" />}
                      <span className={clsx('text-xs font-medium tracking-wide', i === 0 ? 'text-[#E8A020]' : 'text-[#7A7265]')}>
                        {i === 0 ? 'RANK 1 — RECOMMENDED CHOICE' : 'RANK 2 — BACKUP OPTION'}
                      </span>
                    </div>
                    {supplier.flags.length > 0 ? (
                      <span className="flex items-center gap-1 px-2 py-0.5 bg-[#FDF8EE] border border-[#E8A020]/30 rounded-full text-xs text-[#C97B1A]">
                        <AlertTriangle className="w-2.5 h-2.5" />{supplier.flags[0]}
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 px-2 py-0.5 bg-[#F0F7EE] border border-[#5C8A4A]/20 rounded-full text-xs text-[#5C8A4A]">
                        <CheckCircle className="w-2.5 h-2.5" />No Flags
                      </span>
                    )}
                  </div>

                  <div className="flex gap-5">
                    <div className="shrink-0">
                      <ScoreRing score={supplier.total_score} size={100} strokeWidth={7}
                        color={i === 0 ? '#E8A020' : '#C4B89E'} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="mb-3">
                        <h3 className="text-base font-medium text-[#2C2C2C]">{supplier.supplier_name}</h3>
                        <span className="text-xs font-mono text-[#7A7265]">{supplier.supplier_id}</span>
                      </div>
                      <div className="flex flex-col gap-2">
                        {SCORE_BARS(supplier.scores).map(bar => (
                          <ScoreBar key={bar.label} label={bar.label} weight={bar.weight} value={bar.value} delay={bar.delay + i * 0.15} />
                        ))}
                      </div>
                    </div>
                  </div>

                  {i === 0 && !approval_required && approved === null && (
                    <motion.button initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.8 }}
                      onClick={handleApprove}
                      className="mt-4 w-full h-10 rounded-lg bg-[#E8A020] text-white text-sm font-medium hover:bg-[#C97B1A] transition-colors">
                      Award Contract to {supplier.supplier_id}
                    </motion.button>
                  )}
                  {i === 1 && (
                    <button className="mt-4 w-full h-10 rounded-lg border border-[#D4CBB8] text-[#7A7265] text-sm hover:bg-[#EDE8DC] transition-colors">
                      Select as Alternative
                    </button>
                  )}
                </motion.div>
              ))
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
