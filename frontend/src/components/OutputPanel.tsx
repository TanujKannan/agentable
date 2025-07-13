'use client';

import { useState, useRef, useEffect } from 'react';
import { Badge } from '@/components/ui/badge';
import { Terminal, FileText, GitBranch } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import PipelineVisualization from './PipelineVisualization';
import CloudTaskExecutor from './ui/sandbox';
import { PipelineData } from '@/lib/types';
import { WebSocketEvent } from '@/lib/api';

type Status = 'idle' | 'running' | 'complete' | 'error';

interface OutputPanelProps {
  logs: string[];
  result: string | null;
  status: Status;
  runId: string | null;
  pipelineData: PipelineData | null;
  agentUpdates: WebSocketEvent[];
  prompt?: string;
}

type TabType = 'logs' | 'output' | 'pipeline';

export default function OutputPanel({ logs, result, status, runId, pipelineData, agentUpdates, prompt }: OutputPanelProps) {
  const [activeTab, setActiveTab] = useState<TabType>('pipeline');
  const logsEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll logs to bottom
  useEffect(() => {
    if (activeTab === 'logs') {
      logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, activeTab]);

  // Switch to pipeline tab when pipeline data is available
  useEffect(() => {
    if (pipelineData && status === 'running') {
      setActiveTab('pipeline');
    }
  }, [pipelineData, status]);

  // Switch to output tab when result is available
  useEffect(() => {
    if (result && status === 'complete') {
      setActiveTab('output');
    }
  }, [result, status]);

  const getStatusColor = (status: Status) => {
    switch (status) {
      case 'idle': return 'bg-gray-100 text-gray-800';
      case 'running': return 'bg-[#17A589]/10 text-[#17A589]';
      case 'complete': return 'bg-[#17A589]/20 text-[#17A589]';
      case 'error': return 'bg-red-100 text-red-800';
    }
  };

  const getStatusText = (status: Status) => {
    switch (status) {
      case 'idle': return 'Ready';
      case 'running': return 'Running';
      case 'complete': return 'Complete';
      case 'error': return 'Error';
    }
  };

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Header */}
      <div className="border-b border-gray-200 p-4">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-lg font-semibold text-[#1F3A93]">Output</h2>
          <Badge className={`${getStatusColor(status)} px-3 py-1 text-sm font-medium`}>
            {getStatusText(status)}
          </Badge>
        </div>
        {runId && (
          <p className="text-xs text-gray-500">Run ID: {runId}</p>
        )}
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <div className="flex">
          <button
            onClick={() => setActiveTab('pipeline')}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'pipeline'
                ? 'border-[#17A589] text-[#17A589]'
                : 'border-transparent text-gray-500 hover:text-[#2C3E50]'
            }`}
          >
            <GitBranch className="h-4 w-4" />
            Pipeline
            {pipelineData && (
              <Badge variant="secondary" className="ml-1 text-xs">
                {pipelineData.agents?.length || 0}
              </Badge>
            )}
          </button>
          <button
            onClick={() => setActiveTab('logs')}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'logs'
                ? 'border-[#17A589] text-[#17A589]'
                : 'border-transparent text-gray-500 hover:text-[#2C3E50]'
            }`}
          >
            <Terminal className="h-4 w-4" />
            Logs
          </button>
          <button
            onClick={() => setActiveTab('output')}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'output'
                ? 'border-[#17A589] text-[#17A589]'
                : 'border-transparent text-gray-500 hover:text-[#2C3E50]'
            }`}
          >
            <FileText className="h-4 w-4" />
            Output
            {result && (
              <Badge variant="secondary" className="ml-1 text-xs">
                1
              </Badge>
            )}
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'pipeline' && (
          <div className="h-full overflow-y-auto">
            <PipelineVisualization 
              pipelineData={pipelineData}
              agentUpdates={agentUpdates}
            />
          </div>
        )}

        {activeTab === 'logs' && (
          <div className="h-full">
            <CloudTaskExecutor
              embedded={true}
              runId={runId}
              prompt={prompt}
              height="100%"
              externalLogs={logs}
            />
          </div>
        )}

        {activeTab === 'output' && (
          <div className="h-full p-4">
            {result ? (
              <div className="h-full overflow-y-auto">
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 h-full">
                  <div className="text-sm text-green-800 prose prose-sm max-w-none
                    prose-headings:text-green-900 prose-headings:font-medium
                    prose-p:text-green-800 prose-p:leading-relaxed
                    prose-strong:text-green-900 prose-strong:font-semibold
                    prose-img:rounded-lg prose-img:shadow-sm prose-img:max-w-full prose-img:h-auto
                    prose-a:text-green-700 prose-a:underline
                    prose-ul:text-green-800 prose-ol:text-green-800
                    prose-li:text-green-800">
                    <ReactMarkdown>{result}</ReactMarkdown>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-full">
                <p className="text-gray-400 text-sm text-center">
                  Final output will appear here when the task is complete...
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}