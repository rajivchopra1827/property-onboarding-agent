'use client';

import { useState, useCallback } from 'react';

interface UseExtractionStateOptions {
  extractionType: string;
  propertyId: string;
  apiEndpoint: string;
  onSuccess?: () => void;
  onError?: (error: string) => void;
  successMessage?: string;
}

interface UseExtractionStateReturn {
  isLoading: boolean;
  error: string | null;
  success: string | null;
  startExtraction: () => Promise<void>;
  retry: () => Promise<void>;
  clearMessages: () => void;
  stopLoading: () => void;
}

/**
 * Unified hook for managing extraction state across all extraction types.
 * Consolidates loading, error, and success state management.
 */
export function useExtractionState({
  extractionType,
  propertyId,
  apiEndpoint,
  onSuccess,
  onError,
  successMessage,
}: UseExtractionStateOptions): UseExtractionStateReturn {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const clearMessages = useCallback(() => {
    setError(null);
    setSuccess(null);
  }, []);

  const startExtraction = useCallback(async () => {
    if (!propertyId || isLoading) return;

    try {
      setIsLoading(true);
      setError(null);
      setSuccess(null);

      const response = await fetch(apiEndpoint, {
        method: 'POST',
      });

      const result = await response.json();

      if (!response.ok || !result.success) {
        throw new Error(result.error || `Failed to extract ${extractionType}`);
      }

      const message = successMessage || `${extractionType} extraction started! This may take a few minutes.`;
      setSuccess(message);
      
      // Call optional success callback
      if (onSuccess) {
        onSuccess();
      }

      // Note: isLoading will be set to false automatically when data appears
      // via Realtime subscriptions or manual checks in the component
    } catch (err: any) {
      console.error(`Error extracting ${extractionType}:`, err);
      const errorMessage = err.message || `Failed to extract ${extractionType}. Please try again.`;
      setError(errorMessage);
      setIsLoading(false);
      
      // Call optional error callback
      if (onError) {
        onError(errorMessage);
      }
    }
  }, [propertyId, isLoading, apiEndpoint, extractionType, successMessage, onSuccess, onError]);

  const retry = useCallback(async () => {
    clearMessages();
    await startExtraction();
  }, [clearMessages, startExtraction]);

  const stopLoading = useCallback(() => {
    setIsLoading(false);
  }, []);

  return {
    isLoading,
    error,
    success,
    startExtraction,
    retry,
    clearMessages,
    stopLoading,
  };
}
