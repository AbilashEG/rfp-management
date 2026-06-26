'use client'

import { useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    const isAuth = localStorage.getItem('rfp_auth')
    if (!isAuth && pathname !== '/login') {
      router.replace('/login')
    }
  }, [pathname, router])

  return <>{children}</>
}
