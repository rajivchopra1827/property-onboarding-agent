import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';

interface NormalizeRequest {
  amenities: Array<{
    name: string;
    category: 'building' | 'apartment';
  }>;
}

interface NormalizedAmenity {
  raw_name: string;
  normalized_name: string;
  confidence: number | null;
}

export async function POST(request: NextRequest) {
  try {
    const body: NormalizeRequest = await request.json();

    if (!body.amenities || !Array.isArray(body.amenities)) {
      return NextResponse.json(
        { error: 'Invalid request: amenities array required' },
        { status: 400 }
      );
    }

    const backendPath = path.join(process.cwd(), '..', 'backend');
    const scriptPath = path.join(backendPath, 'scripts', 'normalize_amenities_api.py');

    // Prepare input JSON
    const inputJson = JSON.stringify({ amenities: body.amenities });

    try {
      // Execute Python script with input from stdin using spawn
      const result = await new Promise<NormalizeResponse>((resolve, reject) => {
        const pythonProcess = spawn('python3', [scriptPath], {
          cwd: backendPath,
          env: {
            ...process.env,
            PYTHONUNBUFFERED: '1',
          },
        });

        let stdout = '';
        let stderr = '';

        pythonProcess.stdout.on('data', (data) => {
          stdout += data.toString();
        });

        pythonProcess.stderr.on('data', (data) => {
          stderr += data.toString();
        });

        pythonProcess.on('close', (code) => {
          if (code !== 0) {
            // Try to parse error from stdout
            try {
              const errorResult = JSON.parse(stdout);
              reject(new Error(errorResult.error || 'Normalization failed'));
            } catch {
              reject(new Error(stderr || `Process exited with code ${code}`));
            }
          } else {
            try {
              const result = JSON.parse(stdout);
              resolve(result);
            } catch (e) {
              reject(new Error(`Failed to parse output: ${stdout}`));
            }
          }
        });

        pythonProcess.on('error', (error) => {
          reject(error);
        });

        // Write input JSON to stdin
        pythonProcess.stdin.write(inputJson);
        pythonProcess.stdin.end();
      });

      if (result.error) {
        return NextResponse.json(
          { error: result.error, success: false },
          { status: 500 }
        );
      }

      return NextResponse.json({
        normalized: result.normalized || [],
        success: true
      });
    } catch (error: any) {
      console.error('Error executing normalization:', error);
      return NextResponse.json(
        { error: error.message || 'Failed to normalize amenities', success: false },
        { status: 500 }
      );
    }
  } catch (error: any) {
    console.error('Error in normalize API:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error.message, success: false },
      { status: 500 }
    );
  }
}
