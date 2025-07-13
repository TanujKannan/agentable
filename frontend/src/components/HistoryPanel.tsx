'use client';

import { useState, useEffect } from 'react';
import { fetchHistory, HistoryRun, clearHistory } from '@/lib/api';
import { Badge } from '@/components/ui/badge';
import { History, Trash2, Clock, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface HistoryPanelProps {
  onSelectRun?: (run: HistoryRun) => void;
  className?: string;
}

export default function HistoryPanel({ onSelectRun, className = '' }: HistoryPanelProps) {
  const [runs, setRuns] = useState<HistoryRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadHistory = async () => {
    try {
      setLoading(true);
      setError(null);
      const historyRuns = await fetchHistory(20);
      setRuns(historyRuns);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load history');
    } finally {
      setLoading(false);
    }
  };

  const handleClearHistory = async () => {
    if (!confirm('Are you sure you want to clear all history? This cannot be undone.')) {
      return;
    }
    
    try {
      await clearHistory();
      setRuns([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to clear history');
    }
  };

  useEffect(() => {
    loadHistory();
    
    // Refresh history every 30 seconds
    const interval = setInterval(loadHistory, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'complete':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      case 'running':
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'complete':
        return 'bg-green-100 text-green-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      case 'running':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '';
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  return (
    <div className={`bg-white border-r border-gray-200 flex flex-col h-full ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <History className="h-5 w-5 text-[#17A589]" />
            <h2 className="font-semibold text-[#1F3A93]">Recent Runs</h2>
          </div>
          <button
            onClick={handleClearHistory}
            className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
            title="Clear history"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center p-8">
            <Loader2 className="h-6 w-6 animate-spin text-[#17A589]" />
          </div>
        ) : error ? (
          <div className="p-4 text-center">
            <AlertCircle className="h-8 w-8 text-red-500 mx-auto mb-2" />
            <p className="text-sm text-red-600">{error}</p>
            <button
              onClick={loadHistory}
              className="mt-2 text-sm text-[#17A589] hover:underline"
            >
              Try again
            </button>
          </div>
        ) : runs.length === 0 ? (
          <div className="p-4 text-center">
            <History className="h-8 w-8 text-gray-300 mx-auto mb-2" />
            <p className="text-sm text-gray-500">No runs yet</p>
            <p className="text-xs text-gray-400 mt-1">Your recent workflows will appear here</p>
          </div>
        ) : (
          <div className="p-2 space-y-2">
            {runs.map((run) => (
              <div
                key={run.id}
                onClick={() => onSelectRun?.(run)}
                className="p-3 bg-gray-50 hover:bg-gray-100 rounded-lg cursor-pointer transition-colors border border-gray-100 hover:border-gray-200"
              >
                {/* Status and timestamp */}
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(run.status)}
                    <Badge className={`text-xs ${getStatusColor(run.status)}`}>
                      {run.status}
                    </Badge>
                  </div>
                  <div className="text-xs text-gray-500">
                    {formatDistanceToNow(new Date(run.timestamp), { addSuffix: true })}
                  </div>
                </div>

                {/* Prompt */}
                <div className="text-sm text-gray-800 mb-2 line-clamp-2">
                  {run.prompt}
                </div>

                {/* Metadata */}
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <div className="flex items-center gap-3">
                    {run.pipeline_data?.agents && (
                      <span>{run.pipeline_data.agents.length} agents</span>
                    )}
                    {run.duration_seconds && (
                      <span>{formatDuration(run.duration_seconds)}</span>
                    )}
                  </div>
                  <div className="text-gray-400 font-mono">
                    {run.id.substring(0, 8)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}