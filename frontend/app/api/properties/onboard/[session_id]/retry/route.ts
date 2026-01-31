import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';
import { exec } from 'child_process';
import path from 'path';

// Initialize Supabase client for server-side operations
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

// Map extraction types to their script names
const EXTRACTION_SCRIPT_MAP: Record<string, string> = {
  property_info: 'extract_property_info_api.py',
  images: 'extract_images_api.py',
  brand_identity: 'extract_brand_identity_api.py',
  amenities: 'extract_amenities_api.py',
  floor_plans: 'extract_floor_plans_api.py',
  special_offers: 'extract_special_offers_api.py',
  reviews: 'extract_reviews_api.py',
  competitors: 'extract_competitors_api.py',
};

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ session_id: string }> }
) {
  try {
    const { session_id } = await params;
    const body = await request.json();
    const { extraction_type } = body;

    if (!session_id) {
      return NextResponse.json(
        { error: 'Session ID is required' },
        { status: 400 }
      );
    }

    if (!extraction_type) {
      return NextResponse.json(
        { error: 'Extraction type is required' },
        { status: 400 }
      );
    }

    // Get session from database
    const { data: session, error: sessionError } = await supabase
      .from('onboarding_sessions')
      .select('*')
      .eq('id', session_id)
      .single();

    if (sessionError || !session) {
      return NextResponse.json(
        { error: 'Session not found' },
        { status: 404 }
      );
    }

    // Validate extraction type
    if (!EXTRACTION_SCRIPT_MAP[extraction_type]) {
      return NextResponse.json(
        { error: `Invalid extraction type: ${extraction_type}` },
        { status: 400 }
      );
    }

    // Get property_id if available (needed for some extractions)
    const propertyId = session.property_id;

    // For property_info, we need the URL. For others, we need property_id
    if (extraction_type === 'property_info' && !session.url) {
      return NextResponse.json(
        { error: 'Session URL is required for property_info extraction' },
        { status: 400 }
      );
    }

    if (extraction_type !== 'property_info' && !propertyId) {
      return NextResponse.json(
        { error: 'Property ID is required for this extraction type' },
        { status: 400 }
      );
    }

    // Update session to mark this step as in progress
    const updatedErrors = (session.errors || []).filter(
      (err: any) => err.extraction_type !== extraction_type
    );
    
    const updatedCompletedSteps = (session.completed_steps || []).filter(
      (step: string) => step !== extraction_type
    );

    await supabase
      .from('onboarding_sessions')
      .update({
        current_step: extraction_type,
        errors: updatedErrors,
        completed_steps: updatedCompletedSteps,
        status: 'in_progress',
        updated_at: new Date().toISOString(),
      })
      .eq('id', session_id);

    // Get the backend directory path
    const backendPath = path.join(process.cwd(), '..', 'backend');
    const scriptPath = path.join(backendPath, 'scripts', EXTRACTION_SCRIPT_MAP[extraction_type]);

    // Execute the extraction script
    // For property_info, pass URL. For others, pass property_id
    const scriptArg = extraction_type === 'property_info' ? session.url : propertyId;

    exec(
      `python3 "${scriptPath}" "${scriptArg}"`,
      {
        cwd: backendPath,
        env: {
          ...process.env,
          PYTHONUNBUFFERED: '1',
        },
      },
      (error) => {
        if (error) {
          console.error(`${extraction_type} extraction script error:`, error);
          // Update session with error
          supabase
            .from('onboarding_sessions')
            .update({
              errors: [
                ...updatedErrors,
                {
                  extraction_type,
                  error: error.message || 'Extraction failed',
                },
              ],
              current_step: null,
              updated_at: new Date().toISOString(),
            })
            .eq('id', session_id)
            .then(() => {
              console.log('Session updated with error');
            });
        }
      }
    );

    // Return immediately with success status
    return NextResponse.json({
      success: true,
      message: `${extraction_type} extraction retry started`,
    });
  } catch (error: any) {
    console.error('Error retrying extraction:', error);
    return NextResponse.json(
      {
        error: error.message || 'Failed to retry extraction',
        success: false,
      },
      { status: 500 }
    );
  }
}
