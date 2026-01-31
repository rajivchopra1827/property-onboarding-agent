import { NextRequest, NextResponse } from 'next/server';
import { supabase } from '@/lib/supabase';
import OpenAI from 'openai';

// Initialize OpenAI client
const getOpenAIClient = () => {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) {
    throw new Error('OPENAI_API_KEY not found in environment variables');
  }
  return new OpenAI({ apiKey });
};

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

    // Fetch all reviews for the property
    const { data: reviews, error: reviewsError } = await supabase
      .from('property_reviews')
      .select('review_text')
      .eq('property_id', propertyId)
      .not('review_text', 'is', null)
      .limit(100);

    if (reviewsError) {
      console.error('Error fetching reviews:', reviewsError);
      return NextResponse.json(
        { error: 'Failed to fetch reviews' },
        { status: 500 }
      );
    }

    if (!reviews || reviews.length === 0) {
      return NextResponse.json(
        { error: 'No reviews found for this property' },
        { status: 404 }
      );
    }

    // Extract review texts
    const reviewTexts = reviews
      .map((r) => r.review_text)
      .filter((text): text is string => Boolean(text && text.trim()));

    if (reviewTexts.length === 0) {
      return NextResponse.json(
        { error: 'No review text available for analysis' },
        { status: 404 }
      );
    }

    // Limit reviews to avoid token limits
    const reviewsToAnalyze = reviewTexts.slice(0, 50);
    const reviewsText = reviewsToAnalyze
      .map((text, i) => `Review ${i + 1}: ${text}`)
      .join('\n\n---\n\n');

    // Truncate if too long
    const maxChars = 8000;
    const truncatedReviewsText =
      reviewsText.length > maxChars
        ? reviewsText.substring(0, maxChars) + '\n\n[... truncated ...]'
        : reviewsText;

    // Generate sentiment summary using OpenAI
    const openai = getOpenAIClient();
    const prompt = `Analyze the following property reviews and create a concise summary (2-3 sentences) highlighting:
1. Key themes and patterns across the reviews
2. Common positive feedback points
3. Common concerns or negative feedback

Reviews:
${truncatedReviewsText}

Please provide a balanced summary that captures both positive and negative aspects mentioned in the reviews.`;

    const completion = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [
        {
          role: 'system',
          content:
            'You are an expert at analyzing customer reviews and extracting key insights. Provide concise, balanced summaries.',
        },
        {
          role: 'user',
          content: prompt,
        },
      ],
      temperature: 0.7,
      max_tokens: 300,
    });

    const sentimentSummary =
      completion.choices[0]?.message?.content?.trim() ||
      'Unable to generate sentiment summary.';

    // Store summary in database
    const { error: updateError } = await supabase
      .from('property_reviews_summary')
      .update({
        sentiment_summary: sentimentSummary,
        sentiment_summary_generated_at: new Date().toISOString(),
      })
      .eq('property_id', propertyId);

    if (updateError) {
      console.error('Error updating sentiment summary:', updateError);
      // Still return the summary even if database update fails
    }

    return NextResponse.json({
      sentiment_summary: sentimentSummary,
      success: true,
    });
  } catch (error: any) {
    console.error('Error generating sentiment summary:', error);
    return NextResponse.json(
      {
        error:
          error.message || 'Failed to generate sentiment summary',
        success: false,
      },
      { status: 500 }
    );
  }
}

