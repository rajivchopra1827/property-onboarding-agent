import { NextRequest, NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';

const execAsync = promisify(exec);

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

    // Get the backend directory path (assuming frontend and backend are siblings)
    const backendPath = path.join(process.cwd(), '..', 'backend');
    const scriptPath = path.join(backendPath, 'scripts', 'extract_images_api.py');

    // Execute Python script asynchronously (don't wait for completion)
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
          console.error('Image extraction script error:', error);
        }
      }
    );

    // Return immediately with success status
    return NextResponse.json({
      success: true,
      property_id: propertyId,
      message: 'Image extraction started',
    });
  } catch (error: any) {
    console.error('Error starting image extraction:', error);
    return NextResponse.json(
      {
        error: error.message || 'Failed to start image extraction',
        success: false,
      },
      { status: 500 }
    );
  }
}


