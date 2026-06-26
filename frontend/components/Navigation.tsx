'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { LogOut } from 'lucide-react'
import clsx from 'clsx'

export default function Navigation() {
  const pathname = usePathname()
  const router = useRouter()

  const links = [
    { href: '/', label: 'New RFP' },
    { href: '/rfps', label: 'Active RFPs' },
    { href: '/suppliers', label: 'Suppliers' },
  ]

  const handleLogout = () => {
    localStorage.removeItem('rfp_auth')
    router.push('/login')
  }

  return (
    <nav className="w-full border-b border-[#D4CBB8]/50 bg-[#EDE8DC]/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-md bg-[#2C2C2C] flex items-center justify-center">
            <span className="text-[#EDE8DC] text-xs font-semibold">Q</span>
          </div>
          <span className="text-[#2C2C2C] font-medium text-sm tracking-tight">RFP Management</span>
        </Link>

        {/* Nav links */}
        <div className="flex items-center gap-1">
          {links.map((link) => (
            <Link key={link.href} href={link.href}
              className={clsx('px-3 py-1.5 rounded-md text-sm transition-all duration-200',
                pathname === link.href
                  ? 'bg-[#F5F1E8] text-[#2C2C2C] font-medium shadow-warm-sm'
                  : 'text-[#7A7265] hover:text-[#2C2C2C] hover:bg-[#F5F1E8]/60'
              )}>
              {link.label}
            </Link>
          ))}
        </div>

        {/* Right */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-full bg-[#E8A020] flex items-center justify-center">
              <span className="text-white text-xs font-semibold">PM</span>
            </div>
            <span className="text-xs text-[#7A7265] hidden sm:block">Procurement Manager</span>
          </div>
          <button onClick={handleLogout}
            className="w-7 h-7 flex items-center justify-center rounded-md hover:bg-[#D4CBB8]/50 transition-colors"
            title="Sign out">
            <LogOut className="w-3.5 h-3.5 text-[#7A7265]" />
          </button>
        </div>
      </div>
    </nav>
  )
}
