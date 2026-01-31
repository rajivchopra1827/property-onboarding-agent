import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

// Initialize Supabase client for server-side operations
// Reads configuration from .env.local file in project root
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || 
                    process.env.SUPABASE_KEY || 
                    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl) {
  throw new Error(
    'Missing Supabase URL. Please set NEXT_PUBLIC_SUPABASE_URL or SUPABASE_URL in your .env.local file in the project root.'
  );
}

if (!supabaseKey) {
  throw new Error(
    'Missing Supabase key. Please set SUPABASE_SERVICE_ROLE_KEY, SUPABASE_KEY, or NEXT_PUBLIC_SUPABASE_ANON_KEY in your .env.local file in the project root.'
  );
}

const supabase = createClient(supabaseUrl, supabaseKey);

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ session_id: string }> }
) {
  try {
    const { session_id } = await params;

    if (!session_id) {
      return NextResponse.json(
        { error: 'Session ID is required' },
        { status: 400 }
      );
    }

    // Get session from database
    const { data: session, error } = await supabase
      .from('onboarding_sessions')
      .select('*')
      .eq('id', session_id)
      .single();

    if (error || !session) {
      return NextResponse.json(
        { error: 'Session not found' },
        { status: 404 }
      );
    }

    return NextResponse.json({
      success: true,
      session: {
        id: session.id,
        property_id: session.property_id,
        url: session.url,
        status: session.status,
        current_step: session.current_step,
        completed_steps: session.completed_steps || [],
        errors: session.errors || [],
        created_at: session.created_at,
        updated_at: session.updated_at
      }
    });
  } catch (error: any) {
    console.error('Error fetching session status:', error);
    return NextResponse.json(
      {
        error: error.message || 'Failed to fetch session status',
        success: false,
      },
      { status: 500 }
    );
  }
}

