import { NextRequest, NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const propertyId = id;

    if (!propertyId) {
      return NextResponse.json(
        { error: 'Property ID is required' },
        { status: 400 }
      );
    }

    const backendPath = path.join(process.cwd(), '..', 'backend');
    const scriptPath = path.join(backendPath, 'scripts', 'extract_competitors_api.py');

    exec(
      `python3 "${scriptPath}" "${propertyId}"`,
      {
        cwd: backendPath,
        env: {
          ...process.env,
          PYTHONUNBUFFERED: '1',
        },
      },
      (error) => {
        if (error) {
          console.error('Competitors extraction script error:', error);
        }
      }
    );

    return NextResponse.json({
      success: true,
      property_id: propertyId,
      message: 'Competitors extraction started',
    });
  } catch (error: any) {
    console.error('Error starting competitors extraction:', error);
    return NextResponse.json(
      {
        error: error.message || 'Failed to start competitors extraction',
        success: false,
      },
      { status: 500 }
    );
  }
}


