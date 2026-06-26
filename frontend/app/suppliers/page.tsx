'use client'

import { motion } from 'framer-motion'
import Navigation from '@/components/Navigation'

const MOCK_SUPPLIERS = [
  { id: 'SUP001', name: 'BrakeTech Industries', category: 'Brakes', rating: 4.8, status: 'Active' },
  { id: 'SUP003', name: 'Continental Tech', category: 'Sensors', rating: 4.7, status: 'Active' },
  { id: 'SUP005', name: 'AutoSensor Global', category: 'Sensors', rating: 4.9, status: 'Active' },
  { id: 'SUP007', name: 'ElectroAuto Systems', category: 'Electronics', rating: 4.1, status: 'Active' },
  { id: 'SUP009', name: 'HydroFlow Parts', category: 'Hydraulics', rating: 4.5, status: 'Active' },
]

export default function SuppliersPage() {
  return (
    <div className="min-h-screen bg-[#EDE8DC]">
      <Navigation />
      <main className="max-w-6xl mx-auto px-6 py-10">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="mb-8"
        >
          <h1 className="text-2xl font-light text-[#2C2C2C]">Suppliers</h1>
          <p className="text-sm text-[#7A7265] mt-1">{MOCK_SUPPLIERS.length} registered suppliers</p>
        </motion.div>

        {/* Search */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, delay: 0.08 }}
          className="mb-4"
        >
          <input
            type="text"
            placeholder="Search suppliers..."
            className="w-full max-w-sm bg-[#F5F1E8] border border-[#D4CBB8]/60 rounded-lg px-3 py-2 text-sm text-[#2C2C2C] placeholder-[#C4B89E] focus:outline-none focus:border-[#E8A020]/60 transition-all"
          />
        </motion.div>

        {/* Table */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.12 }}
          className="bg-[#F5F1E8] border border-[#D4CBB8]/50 rounded-xl overflow-hidden shadow-warm-sm"
        >
          <table className="w-full">
            <thead>
              <tr className="border-b border-[#D4CBB8]/40">
                {['Supplier ID', 'Name', 'Category', 'Rating', 'Status'].map(h => (
                  <th key={h} className="text-left px-4 py-3 text-xs tracking-[0.1em] uppercase text-[#7A7265] font-medium">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {MOCK_SUPPLIERS.map((s, i) => (
                <motion.tr
                  key={s.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.15 + i * 0.05 }}
                  className="border-b border-[#D4CBB8]/20 last:border-0 hover:bg-[#EDE8DC]/50 transition-colors"
                >
                  <td className="px-4 py-3 text-sm font-mono text-[#2C2C2C]">{s.id}</td>
                  <td className="px-4 py-3 text-sm text-[#2C2C2C]">{s.name}</td>
                  <td className="px-4 py-3">
                    <span className="text-xs px-2 py-0.5 bg-[#EDE8DC] border border-[#D4CBB8] rounded-full text-[#7A7265]">
                      {s.category}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1.5">
                      <div className="flex gap-0.5">
                        {[1,2,3,4,5].map(dot => (
                          <div key={dot} className={`w-2 h-2 rounded-full ${dot <= Math.floor(s.rating) ? 'bg-[#E8A020]' : 'bg-[#D4CBB8]'}`} />
                        ))}
                      </div>
                      <span className="text-xs text-[#7A7265]">{s.rating}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-xs px-2 py-0.5 bg-[#F0F7EE] border border-[#5C8A4A]/20 rounded-full text-[#5C8A4A]">
                      {s.status}
                    </span>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </motion.div>
      </main>
    </div>
  )
}
