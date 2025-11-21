import { NextResponse } from 'next/server'

export async function GET() {
  try {
    // Call Python backend API to get sample patient IDs
    const pythonApiUrl = process.env.PYTHON_API_URL || 'http://localhost:8000'
    
    const response = await fetch(`${pythonApiUrl}/api/sample-ids`, {
      method: 'GET',
    })

    if (!response.ok) {
      // Return empty array if backend is not available
      return NextResponse.json({ ids: [] })
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    // Return empty array if backend is not available
    return NextResponse.json({ ids: [] })
  }
}

