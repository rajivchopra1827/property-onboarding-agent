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

    // Parse request body
    let imageIds: string[] = [];
    let theme = 'lifestyle';
    
    try {
      const body = await request.json();
      if (!body.image_ids || !Array.isArray(body.image_ids) || body.image_ids.length === 0) {
        return NextResponse.json(
          { error: 'image_ids array is required and must contain at least one image ID' },
          { status: 400 }
        );
      }
      imageIds = body.image_ids;
      
      if (body.theme && typeof body.theme === 'string') {
        const validThemes = ['lifestyle', 'amenities', 'floor_plans', 'special_offers', 'reviews', 'location'];
        if (validThemes.includes(body.theme)) {
          theme = body.theme;
        }
      }
    } catch (error: any) {
      return NextResponse.json(
        { error: 'Invalid request body. Expected JSON with image_ids array and optional theme.' },
        { status: 400 }
      );
    }

    // Get the backend directory path (assuming frontend and backend are siblings)
    const backendPath = path.join(process.cwd(), '..', 'backend');
    const scriptPath = path.join(backendPath, 'scripts', 'generate_videos_api.py');

    // Execute Python script
    let stdout: string;
    let stderr: string;
    
    try {
      // Pass image_ids as JSON string
      const imageIdsJson = JSON.stringify(imageIds);
      const result = await execAsync(
        `python3 "${scriptPath}" "${propertyId}" '${imageIdsJson}' "${theme}"`,
        {
          cwd: backendPath,
          env: {
            ...process.env,
            PYTHONUNBUFFERED: '1',
          },
          maxBuffer: 50 * 1024 * 1024, // 50MB buffer (videos generate lots of output)
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
              error: errorResult.error || 'Failed to generate videos',
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
          error: error.message || 'Failed to execute video generation script',
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
          error: `Invalid response from video generation service: ${parseError.message}. Check server logs for details.`,
          success: false,
        },
        { status: 500 }
      );
    }

    if (!result.success) {
      return NextResponse.json(
        {
          error: result.error || 'Failed to generate videos',
          success: false,
        },
        { status: 500 }
      );
    }

    return NextResponse.json({
      success: true,
      videos: result.videos || [],
      errors: result.errors || [],
      total_requested: result.total_requested || 0,
      total_succeeded: result.total_succeeded || 0,
      total_failed: result.total_failed || 0,
      message: `Successfully generated ${result.total_succeeded || 0} video${result.total_succeeded !== 1 ? 's' : ''}${result.total_failed > 0 ? ` (${result.total_failed} failed)` : ''}`,
    });
  } catch (error: any) {
    console.error('Error generating videos:', error);

    // Handle JSON parse errors
    if (error.message?.includes('JSON')) {
      return NextResponse.json(
        {
          error: 'Invalid response from video generation service',
          success: false,
        },
        { status: 500 }
      );
    }

    return NextResponse.json(
      {
        error: error.message || 'Failed to generate videos',
        success: false,
      },
      { status: 500 }
    );
  }
}
