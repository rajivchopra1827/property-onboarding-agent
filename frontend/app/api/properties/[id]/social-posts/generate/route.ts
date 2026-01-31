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

    // Parse optional request body for post_count
    let postCount = 8;
    try {
      const body = await request.json().catch(() => ({}));
      if (body.post_count && typeof body.post_count === 'number') {
        postCount = Math.max(5, Math.min(10, body.post_count));
      }
    } catch {
      // No body provided, use default
    }

    // Get the backend directory path (assuming frontend and backend are siblings)
    const backendPath = path.join(process.cwd(), '..', 'backend');
    const scriptPath = path.join(backendPath, 'scripts', 'generate_social_posts_api.py');

    // Execute Python script
    let stdout: string;
    let stderr: string;
    
    try {
      const result = await execAsync(
        `python3 "${scriptPath}" "${propertyId}" ${postCount}`,
        {
          cwd: backendPath,
          env: {
            ...process.env,
            PYTHONUNBUFFERED: '1',
          },
          maxBuffer: 10 * 1024 * 1024, // 10MB buffer
        }
      );
      stdout = result.stdout;
      stderr = result.stderr;
    } catch (error: any) {
      // If the command failed, try to parse error output
      const errorOutput = error.stdout || error.stderr || error.message;
      console.error('Python script execution error:', errorOutput);
      
      // Try to parse JSON from stdout if available
      if (error.stdout) {
        try {
          const errorResult = JSON.parse(error.stdout.trim());
          return NextResponse.json(
            {
              error: errorResult.error || 'Failed to generate social posts',
              success: false,
            },
            { status: 500 }
          );
        } catch {
          // Not JSON, fall through to generic error
        }
      }
      
      return NextResponse.json(
        {
          error: error.message || 'Failed to execute generation script',
          success: false,
        },
        { status: 500 }
      );
    }

    // Filter out warnings from stderr
    if (stderr && !stderr.includes('Warning') && !stderr.includes('NotOpenSSLWarning')) {
      console.error('Python script stderr:', stderr);
    }

    // Parse JSON output from Python script
    let result;
    try {
      const trimmedOutput = stdout.trim();
      // Find the last JSON object in the output (in case there are print statements before it)
      // Look for JSON object starting with { and ending with }
      const lines = trimmedOutput.split('\n');
      let jsonString = '';
      
      // Try to find JSON in the last few lines
      for (let i = lines.length - 1; i >= 0; i--) {
        const line = lines[i].trim();
        if (line.startsWith('{')) {
          // Found start of JSON, try to parse from here
          jsonString = lines.slice(i).join('\n');
          break;
        }
      }
      
      // If no JSON found, try parsing the whole output
      if (!jsonString) {
        jsonString = trimmedOutput;
      }
      
      // Try to extract just the JSON object (handle nested objects)
      const jsonMatch = jsonString.match(/\{[\s\S]*\}/);
      const finalJson = jsonMatch ? jsonMatch[0] : jsonString;
      
      result = JSON.parse(finalJson);
    } catch (parseError: any) {
      console.error('Failed to parse Python script output:', {
        stdout: stdout.substring(0, 500), // First 500 chars
        stderr: stderr?.substring(0, 500),
        parseError: parseError.message,
      });
      return NextResponse.json(
        {
          error: `Invalid response from generation service: ${parseError.message}. Check server logs for details.`,
          success: false,
        },
        { status: 500 }
      );
    }

    if (!result.success) {
      return NextResponse.json(
        {
          error: result.error || 'Failed to generate social posts',
          success: false,
        },
        { status: 500 }
      );
    }

    return NextResponse.json({
      success: true,
      count: result.count || 0,
      property_id: result.property_id,
      message: `Successfully generated ${result.count || 0} social media posts`,
    });
  } catch (error: any) {
    console.error('Error generating social posts:', error);

    // Handle JSON parse errors
    if (error.message?.includes('JSON')) {
      return NextResponse.json(
        {
          error: 'Invalid response from generation service',
          success: false,
        },
        { status: 500 }
      );
    }

    return NextResponse.json(
      {
        error: error.message || 'Failed to generate social posts',
        success: false,
      },
      { status: 500 }
    );
  }
}

