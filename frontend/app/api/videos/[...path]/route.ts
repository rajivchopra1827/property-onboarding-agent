import { NextRequest, NextResponse } from 'next/server';
import { readFile } from 'fs/promises';
import { join } from 'path';
import { existsSync } from 'fs';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  try {
    const { path: pathArray } = await params;
    const videoPath = pathArray.join('/');
    
    // Security: Only allow paths that start with "reels/"
    if (!videoPath.startsWith('reels/')) {
      return NextResponse.json(
        { error: 'Invalid video path' },
        { status: 400 }
      );
    }

    // Get the backend directory path (assuming frontend and backend are siblings)
    const backendPath = join(process.cwd(), '..', 'backend');
    const fullPath = join(backendPath, videoPath);

    // Security: Ensure the resolved path is within the backend directory
    if (!fullPath.startsWith(backendPath)) {
      return NextResponse.json(
        { error: 'Invalid video path' },
        { status: 400 }
      );
    }

    // Check if file exists
    if (!existsSync(fullPath)) {
      return NextResponse.json(
        { error: 'Video not found' },
        { status: 404 }
      );
    }

    // Read the video file
    const videoBuffer = await readFile(fullPath);

    // Determine content type based on file extension
    const contentType = videoPath.endsWith('.mp4')
      ? 'video/mp4'
      : videoPath.endsWith('.webm')
      ? 'video/webm'
      : 'video/mp4'; // Default to mp4

    // Return the video with appropriate headers
    return new NextResponse(videoBuffer, {
      headers: {
        'Content-Type': contentType,
        'Content-Length': videoBuffer.length.toString(),
        'Cache-Control': 'public, max-age=31536000, immutable',
        'Accept-Ranges': 'bytes',
      },
    });
  } catch (error: any) {
    console.error('Error serving video:', error);
    return NextResponse.json(
      { error: 'Failed to serve video' },
      { status: 500 }
    );
  }
}
