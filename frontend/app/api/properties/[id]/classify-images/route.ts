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

    // Parse optional request body for force_reclassify
    let forceReclassify = false;
    try {
      const body = await request.json().catch(() => ({}));
      if (body.force_reclassify && typeof body.force_reclassify === 'boolean') {
        forceReclassify = body.force_reclassify;
      }
    } catch {
      // No body provided, use default
    }

    const backendPath = path.join(process.cwd(), '..', 'backend');
    const scriptPath = path.join(backendPath, 'scripts', 'classify_images_api.py');

    // Execute Python script and capture output
    return new Promise((resolve) => {
      exec(
        `python3 "${scriptPath}" "${propertyId}" ${forceReclassify}`,
        {
          cwd: backendPath,
          env: {
            ...process.env,
            PYTHONUNBUFFERED: '1',
          },
          maxBuffer: 10 * 1024 * 1024, // 10MB buffer for large outputs
        },
        (error, stdout, stderr) => {
          // Log stderr for debugging
          if (stderr) {
            console.error('Image classification script stderr:', stderr);
          }

          if (error) {
            console.error('Image classification script error:', error);
            resolve(NextResponse.json(
              {
                success: false,
                error: error.message || 'Failed to execute classification script',
                stderr: stderr || undefined,
              },
              { status: 500 }
            ));
            return;
          }

          // Try to parse JSON output from stdout
          try {
            const output = stdout.trim();
            // Find JSON in output (might have other text before/after)
            const jsonMatch = output.match(/\{[\s\S]*\}/);
            if (jsonMatch) {
              const result = JSON.parse(jsonMatch[0]);
              
              if (result.success === false || result.error) {
                console.error('Image classification failed:', result.error);
                resolve(NextResponse.json(
                  {
                    success: false,
                    error: result.error || 'Classification failed',
                    ...result,
                  },
                  { status: 500 }
                ));
                return;
              }

              // Success - return the result
              resolve(NextResponse.json({
                success: true,
                ...result,
                message: `Successfully classified ${result.classified || 0} images (${result.failed || 0} failed)`,
              }));
            } else {
              // No JSON found in output
              console.warn('No JSON found in script output:', output);
              resolve(NextResponse.json(
                {
                  success: false,
                  error: 'Script completed but no result found',
                  output: output.substring(0, 500), // First 500 chars for debugging
                },
                { status: 500 }
              ));
            }
          } catch (parseError: any) {
            console.error('Error parsing script output:', parseError);
            console.error('Raw stdout:', stdout);
            resolve(NextResponse.json(
              {
                success: false,
                error: 'Failed to parse script output',
                parseError: parseError.message,
                output: stdout.substring(0, 500), // First 500 chars for debugging
              },
              { status: 500 }
            ));
          }
        }
      );
    });
  } catch (error: any) {
    console.error('Error starting image classification:', error);
    return NextResponse.json(
      {
        error: error.message || 'Failed to start image classification',
        success: false,
      },
      { status: 500 }
    );
  }
}


