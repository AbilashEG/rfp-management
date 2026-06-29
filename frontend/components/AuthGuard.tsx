'use client'

import { useEffect, useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const [ready, setReady] = useState(false)

  useEffect(() => {
    const isAuth = localStorage.getItem('rfp_auth')

    if (pathname === '/login') {
      // On login page — if already auth, go to dashboard
      if (isAuth) {
        router.replace('/')
      } else {
        setReady(true)
      }
      return
    }

    // On any other page — if not auth, go to login
    if (!isAuth) {
      router.replace('/login')
    } else {
      setReady(true)
    }
  }, [pathname, router])

  // Show nothing until auth check completes — prevents flash
  if (!ready) return null

  return <>{children}</>
}
