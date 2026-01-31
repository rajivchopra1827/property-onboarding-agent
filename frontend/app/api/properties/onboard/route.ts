import { NextRequest, NextResponse } from 'next/server';


export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { url, force_reonboard } = body;

    if (!url || typeof url !== 'string') {
      return NextResponse.json(
        { error: 'URL is required' },
        { status: 400 }
      );
    }

    // Validate URL format
    try {
      const urlObj = new URL(url);
      if (!urlObj.protocol.startsWith('http')) {
        return NextResponse.json(
          { error: 'URL must start with http:// or https://' },
          { status: 400 }
        );
      }
    } catch {
      return NextResponse.json(
        { error: 'Invalid URL format' },
        { status: 400 }
      );
    }

    // Call FastAPI server to start onboarding workflow
    // The API will handle session creation and return session_id
    const apiUrl = process.env.BACKEND_API_URL || 'http://localhost:8000';
    
    try {
      // Add timeout to prevent hanging (10 seconds)
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000);
      
      const response = await fetch(`${apiUrl}/api/onboard`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: url,
          force_reonboard: force_reonboard || false,
        }),
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error('Onboarding API error:', errorData);
        
        return NextResponse.json(
          { 
            error: errorData.detail || 'Failed to start onboarding',
            success: false 
          },
          { status: response.status }
        );
      }

      // Workflow started successfully - API returns session_id
      const result = await response.json();
      
      // Return immediately with session ID from API response
      return NextResponse.json({
        success: result.success,
        session_id: result.session_id,
        property_id: result.property_id,
        status: result.status,
        message: result.message
      });
    } catch (error: any) {
      console.error('Error calling onboarding API:', error);
      
      // Handle timeout specifically
      if (error.name === 'AbortError') {
        return NextResponse.json(
          {
            error: 'Request timed out. The backend may be slow. Please try again or check the backend server.',
            success: false,
          },
          { status: 504 }
        );
      }
      
      return NextResponse.json(
        {
          error: error.message || 'Failed to start onboarding',
          success: false,
        },
        { status: 500 }
      );
    }

  } catch (error: any) {
    console.error('Error starting onboarding:', error);
    return NextResponse.json(
      {
        error: error.message || 'Failed to start onboarding',
        success: false,
      },
      { status: 500 }
    );
  }
}

