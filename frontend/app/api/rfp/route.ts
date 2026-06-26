import { NextRequest, NextResponse } from 'next/server'

const API_GATEWAY_URL = process.env.NEXT_PUBLIC_API_URL || ''

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()

    if (!body.message) {
      return NextResponse.json({ error: 'message required' }, { status: 400 })
    }

    const res = await fetch(`${API_GATEWAY_URL}/rfp`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: body.message }),
    })

    const data = await res.json()
    return NextResponse.json(data, { status: res.status })

  } catch (error) {
    console.error('API error:', error)
    return NextResponse.json({ error: 'Failed to reach backend' }, { status: 500 })
  }
}

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url)
    const id = searchParams.get('id')

    if (!id) {
      return NextResponse.json({ error: 'id required' }, { status: 400 })
    }

    const res = await fetch(`${API_GATEWAY_URL}/rfp/${id}`)
    const data = await res.json()
    return NextResponse.json(data, { status: res.status })

  } catch (error) {
    console.error('API error:', error)
    return NextResponse.json({ error: 'Failed to reach backend' }, { status: 500 })
  }
}
