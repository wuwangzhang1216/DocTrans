"use client"

import React, { useState, useEffect } from 'react';
import { Download, Clock, Trash2, FileText } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001';

export interface HistoryItem {
  jobId: string;
  fileName: string;
  targetLanguage: string;
  completedAt: number; // timestamp
  outputFile: string;
}

const ONE_HOUR_MS = 3600000;

export default function TranslationHistory() {
  const [history, setHistory] = useState<HistoryItem[]>([]);

  // Load history from localStorage
  useEffect(() => {
    loadHistory();

    // Listen for storage changes (from other tabs/windows)
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'translationHistory') {
        loadHistory();
      }
    };

    // Listen for custom event (from same tab)
    const handleHistoryUpdate = () => {
      loadHistory();
    };

    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('historyUpdated', handleHistoryUpdate);

    // Poll for updates every 2 seconds as backup
    const pollInterval = setInterval(() => {
      loadHistory();
    }, 2000);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('historyUpdated', handleHistoryUpdate);
      clearInterval(pollInterval);
    };
  }, []);

  const loadHistory = () => {
    try {
      const stored = localStorage.getItem('translationHistory');
      if (stored) {
        const items: HistoryItem[] = JSON.parse(stored);
        // Filter out items older than 1 hour
        const now = Date.now();
        const validItems = items.filter(item => {
          const age = now - item.completedAt;
          return age < ONE_HOUR_MS;
        });

        // Update localStorage if we filtered out any items
        if (validItems.length !== items.length) {
          localStorage.setItem('translationHistory', JSON.stringify(validItems));
        }

        setHistory(validItems);
      }
    } catch (error) {
      console.error('Error loading history:', error);
    }
  };

  const handleDownload = (item: HistoryItem) => {
    if (item.outputFile) {
      window.open(`${API_URL}/api/download/${item.outputFile}`, '_blank');
    }
  };

  const handleDelete = (jobId: string) => {
    const updatedHistory = history.filter(item => item.jobId !== jobId);
    setHistory(updatedHistory);
    localStorage.setItem('translationHistory', JSON.stringify(updatedHistory));
  };

  const handleClearAll = () => {
    setHistory([]);
    localStorage.removeItem('translationHistory');
  };

  const formatTimeAgo = (timestamp: number) => {
    const now = Date.now();
    const diff = now - timestamp;
    const minutes = Math.floor(diff / 60000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    return `${Math.floor(minutes / 60)}h ago`;
  };

  if (history.length === 0) {
    return null;
  }

  return (
    <Card className="w-full max-w-3xl mx-auto mt-8 bg-white/5 backdrop-blur-md border border-white/10 shadow-xl">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-white">Recent Translations</CardTitle>
            <CardDescription className="text-gray-400">
              Files are available for 1 hour after completion
            </CardDescription>
          </div>
          {history.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleClearAll}
              className="text-gray-400 hover:text-white"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Clear All
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {history.map((item) => (
          <div
            key={item.jobId}
            className="border border-white/10 rounded-lg p-4 bg-white/5 hover:bg-white/10 transition-colors"
          >
            <div className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <div className="p-2 rounded-lg bg-gradient-to-br from-[#fbbf24]/20 to-[#f97316]/20">
                  <FileText className="h-5 w-5 text-[#f97316]" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm text-white truncate">
                    {item.fileName}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant="secondary" className="text-xs">
                      {item.targetLanguage}
                    </Badge>
                    <span className="text-xs text-gray-400 flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {formatTimeAgo(item.completedAt)}
                    </span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  onClick={() => handleDownload(item)}
                  className="bg-gradient-to-r from-[#fbbf24] to-[#f97316] hover:from-[#f59e0b] hover:to-[#ea580c] text-white"
                >
                  <Download className="h-4 w-4 mr-1" />
                  Download
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleDelete(item.jobId)}
                  className="text-gray-400 hover:text-white"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

// Helper function to add item to history (to be called from TranslationUpload component)
export function addToHistory(item: HistoryItem) {
  try {
    const stored = localStorage.getItem('translationHistory');
    const history: HistoryItem[] = stored ? JSON.parse(stored) : [];

    // Check if item already exists
    const existingIndex = history.findIndex(h => h.jobId === item.jobId);
    if (existingIndex >= 0) {
      // Update existing item
      history[existingIndex] = item;
    } else {
      // Add new item at the beginning
      history.unshift(item);
    }

    // Keep only items from the last hour
    const now = Date.now();
    const validHistory = history.filter(h => now - h.completedAt < ONE_HOUR_MS);

    // Limit to 50 most recent items
    const limitedHistory = validHistory.slice(0, 50);

    localStorage.setItem('translationHistory', JSON.stringify(limitedHistory));

    // Trigger custom event to notify TranslationHistory component
    window.dispatchEvent(new Event('historyUpdated'));
  } catch (error) {
    console.error('Error adding to history:', error);
  }
}
