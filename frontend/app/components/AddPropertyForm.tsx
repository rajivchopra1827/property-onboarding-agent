'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/app/components/ui/card';
import { Button } from '@/app/components/ui/button';
import { Input } from '@/app/components/ui/input';
import { Label } from '@/app/components/ui/label';
import { Checkbox } from '@/app/components/ui/checkbox';
import { Alert, AlertDescription } from '@/app/components/ui/alert';

interface AddPropertyFormProps {
  onClose?: () => void;
}

export default function AddPropertyForm({ onClose }: AddPropertyFormProps) {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [forceReonboard, setForceReonboard] = useState(false);
  const router = useRouter();

  const validateUrl = (urlString: string): boolean => {
    try {
      const urlObj = new URL(urlString);
      return urlObj.protocol.startsWith('http');
    } catch {
      return false;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!url.trim()) {
      setError('Please enter a URL');
      return;
    }

    if (!validateUrl(url.trim())) {
      setError('Please enter a valid URL starting with http:// or https://');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch('/api/properties/onboard', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          url: url.trim(),
          force_reonboard: forceReonboard
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to start onboarding');
      }

      if (data.status === 'already_exists' && data.property_id) {
        // Property already exists, redirect to it
        router.push(`/properties/${data.property_id}`);
        return;
      }

      if (data.session_id) {
        // Redirect to progress page
        router.push(`/properties/onboard/${data.session_id}`);
      } else {
        throw new Error('No session ID returned');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start onboarding');
      setLoading(false);
    }
  };

  return (
    <Card className="shadow-md overflow-hidden" style={{ borderTop: '3px solid transparent', borderImage: 'linear-gradient(135deg, #FF1B8D 0%, #7B1FA2 100%) 1' }}>
      <CardHeader>
        <CardTitle className="text-2xl font-display text-secondary-700 dark:text-secondary-300">
          Add New Property
        </CardTitle>
        <CardDescription className="text-muted-foreground">
          Enter the website URL of the property you want to onboard. We'll extract all the information automatically.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="url">Property Website URL</Label>
            <Input
              type="url"
              id="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com"
              disabled={loading}
              required
            />
          </div>

          <div className="flex items-start space-x-2">
            <Checkbox
              id="force_reonboard"
              checked={forceReonboard}
              onCheckedChange={(checked) => setForceReonboard(checked === true)}
              disabled={loading}
            />
            <Label htmlFor="force_reonboard" className="text-sm font-normal cursor-pointer">
              Force re-onboard (overwrite existing data)
            </Label>
          </div>

          {error && (
            <Alert variant="destructive" className="bg-error-light dark:bg-error/20 text-error-dark dark:text-error shadow-sm">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="flex gap-3">
            <Button
              type="submit"
              disabled={loading}
              className="flex-1 h-12 shadow-primary hover:shadow-primary-lg hover:-translate-y-0.5 active:translate-y-0 disabled:hover:translate-y-0"
            >
              {loading ? 'Starting...' : 'Start Onboarding'}
            </Button>
            {onClose && (
              <Button
                type="button"
                variant="outline"
                onClick={onClose}
                disabled={loading}
                className="px-6 h-12"
              >
                Cancel
              </Button>
            )}
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

