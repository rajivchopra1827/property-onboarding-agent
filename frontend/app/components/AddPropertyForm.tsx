'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

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
    <div className="bg-white rounded-lg border border-neutral-200 p-6 shadow-md">
      <h2 className="text-2xl font-bold text-secondary-700 mb-4 font-display">
        Add New Property
      </h2>
      <p className="text-neutral-700 mb-6">
        Enter the website URL of the property you want to onboard. We'll extract all the information automatically.
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="url" className="block text-sm font-medium text-neutral-800 mb-2">
            Property Website URL
          </label>
          <input
            type="url"
            id="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com"
            className="w-full px-4 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-neutral-900"
            disabled={loading}
            required
          />
        </div>

        <div className="flex items-start">
          <input
            type="checkbox"
            id="force_reonboard"
            checked={forceReonboard}
            onChange={(e) => setForceReonboard(e.target.checked)}
            disabled={loading}
            className="mt-1 h-4 w-4 text-primary-500 focus:ring-primary-500 border-neutral-300 rounded"
          />
          <label htmlFor="force_reonboard" className="ml-2 text-sm text-neutral-700">
            Force re-onboard (overwrite existing data)
          </label>
        </div>

        {error && (
          <div className="bg-error-light border border-error text-error-dark px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={loading}
            className="flex-1 h-12 bg-primary-500 text-white font-semibold rounded-lg shadow-primary transition-all duration-200 hover:bg-primary-600 hover:shadow-primary-lg hover:-translate-y-0.5 active:translate-y-0 focus:outline-none focus:ring-4 focus:ring-primary-300 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0"
          >
            {loading ? 'Starting...' : 'Start Onboarding'}
          </button>
          {onClose && (
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-6 h-12 border border-neutral-300 text-neutral-700 font-semibold rounded-lg transition-all duration-200 hover:bg-neutral-50 focus:outline-none focus:ring-4 focus:ring-neutral-300 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancel
            </button>
          )}
        </div>
      </form>
    </div>
  );
}

