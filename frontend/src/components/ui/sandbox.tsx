'use client';

import { useState, useRef, useEffect, useCallback } from 'react';

interface LogEntry {
  id: string;
  message: string;
  timestamp: Date;
}

const getBackendUrl = (): string | null => {
  if (process.env.NODE_ENV === 'production') {
    return process.env.NEXT_PUBLIC_BACKEND_URL || null;
  }
  return process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
};

interface SandBoxProps {
  prompt?: string;
  shouldRun?: boolean;
  onStatusChange?: (status: 'idle' | 'running' | 'complete' | 'error') => void;
  onResult?: (result: string) => void;
  onClose?: () => void;
  runId?: string | null;
  // New props for embedded mode
  embedded?: boolean;
  height?: string;
  // External logs for embedded mode
  externalLogs?: string[];
}

export default function CloudTaskExecutor({ 
  prompt = 'Sample task for testing', 
  shouldRun = false,
  onStatusChange,
  onResult,
  onClose,
  runId,
  embedded = false,
  height = '400px',
  externalLogs = []
}: SandBoxProps) {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(runId || null);
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected');
  const wsRef = useRef<WebSocket | null>(null);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const hasRun = useRef(false);

  // Convert external logs to LogEntry format when in embedded mode
  const displayLogs = embedded && externalLogs.length > 0 
    ? externalLogs.map((log, index) => ({
        id: `external-${index}`,
        message: log,
        timestamp: new Date()
      }))
    : logs;

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs, externalLogs]);

  const addLog = useCallback((message: string) => {
    const newLog: LogEntry = {
      id: Date.now().toString() + Math.random().toString(36),
      message,
      timestamp: new Date()
    };
    setLogs(prev => [...prev, newLog]);
  }, []);

  const connectWebSocket = useCallback((taskId: string) => {
    if (wsRef.current) {
      wsRef.current.close(1000, 'Reconnecting to new task');
    }

    setConnectionStatus('connecting');
    
    const backendUrl = getBackendUrl();
    if (!backendUrl) {
      addLog('❌ Cannot connect to WebSocket: Backend URL not configured.');
      setConnectionStatus('error');
      return;
    }
    const wsUrl = backendUrl.replace(/^http/, 'ws');
    
    const ws = new WebSocket(`${wsUrl}/api/ws/${taskId}`);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnectionStatus('connected');
      addLog('🟢 Connected to log stream');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        switch (data.type) {
          case 'agent-update':
            addLog(`🤖 ${data.message}`);
            break;
          case 'log':
            addLog(`📋 ${data.message}`);
            break;
          case 'complete':
            addLog('✅ Process completed');
            if (data.result) {
              addLog(`📊 Result: ${data.result}`);
              if (onResult) {
                onResult(data.result);
              }
            }
            setIsRunning(false);
            setConnectionStatus('disconnected');
            ws.close(1000, 'Task completed normally');
            break;
          case 'error':
            addLog(`❌ Error: ${data.message}`);
            setIsRunning(false);
            setConnectionStatus('error');
            ws.close(1000, 'Task completed with error');
            break;
          default:
            addLog(data.message || event.data);
        }
      } catch {
        // Fallback for plain text messages
        const message = event.data;
        if (message === '[Process finished]') {
          addLog('✅ Process completed');
          setIsRunning(false);
          setConnectionStatus('disconnected');
          ws.close(1000, 'Process finished normally');
        } else {
          addLog(message);
        }
      }
    };

    ws.onclose = (event) => {
      setConnectionStatus('disconnected');
      if (event.code === 4001) {
        addLog('❌ Task ID not found');
      } else if (event.code !== 1000) {
        addLog('🔴 WebSocket connection closed unexpectedly');
      }
      setIsRunning(false);
    };

    ws.onerror = () => {
      setConnectionStatus('error');
      addLog('❌ WebSocket connection error');
      setIsRunning(false);
    };
  }, [addLog, onResult]);

  const runTask = useCallback(async () => {
    if (isRunning) return;

    setIsRunning(true);
    setLogs([]);
    setTaskId(null);
    addLog('🚀 Starting task...');

    try {
      const backendUrl = getBackendUrl();
      if (!backendUrl) {
        addLog('❌ Configuration error: NEXT_PUBLIC_BACKEND_URL is not set.');
        setIsRunning(false);
        return;
      }
      
      const response = await fetch(`${backendUrl}/api/run`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const newTaskId = data.taskId;
      setTaskId(newTaskId);
      addLog(`📋 Task created with ID: ${newTaskId}`);
      
      // Connect to WebSocket for real-time logs
      connectWebSocket(newTaskId);

    } catch (error) {
      addLog(`❌ Error starting task: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setIsRunning(false);
    }
  }, [prompt, isRunning, addLog, connectWebSocket]);

  // Auto-run when shouldRun changes to true
  useEffect(() => {
    if (shouldRun && !isRunning && !hasRun.current && prompt.trim()) {
      hasRun.current = true;
      runTask();
    }
  }, [shouldRun, prompt, isRunning, runTask]);

  // Reset hasRun when prompt changes
  useEffect(() => {
    hasRun.current = false;
  }, [prompt]);

  // Connect to existing task if runId provided
  useEffect(() => {
    if (runId && runId !== taskId) {
      setTaskId(runId);
      connectWebSocket(runId);
    }
  }, [runId, taskId, connectWebSocket]);

  // Notify parent of status changes
  useEffect(() => {
    if (onStatusChange) {
      if (isRunning) {
        onStatusChange('running');
      } else if (connectionStatus === 'error') {
        onStatusChange('error');
      } else if (connectionStatus === 'disconnected' && displayLogs.some(log => log.message.includes('Process completed'))) {
        onStatusChange('complete');
      } else {
        onStatusChange('idle');
      }
    }
  }, [isRunning, connectionStatus, displayLogs, onStatusChange]);

  const clearLogs = () => {
    if (embedded && externalLogs.length > 0) {
      // In embedded mode with external logs, we can't clear them
      // This would need to be handled by the parent component
      return;
    }
    setLogs([]);
  };

  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'text-green-500';
      case 'connecting': return 'text-yellow-500';
      case 'error': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connected': return 'Connected';
      case 'connecting': return 'Connecting...';
      case 'error': return 'Error';
      default: return 'Disconnected';
    }
  };

  // Embedded mode - just return the logs section
  if (embedded) {
    return (
      <div className="h-full flex flex-col bg-gray-900 text-green-400 font-mono text-sm">
        {/* Connection Status Bar */}
        <div className="bg-gray-800 px-4 py-2 border-b border-gray-700 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${
              connectionStatus === 'connected' ? 'bg-green-500' : 
              connectionStatus === 'connecting' ? 'bg-yellow-500' : 
              connectionStatus === 'error' ? 'bg-red-500' : 'bg-gray-400'
            }`}></div>
            <span className={`text-sm font-medium ${getStatusColor()}`}>
              {getStatusText()}
            </span>
          </div>
          <div className="flex items-center space-x-2">
            {taskId && (
              <span className="text-xs text-gray-400 bg-gray-700 px-2 py-1 rounded">
                ID: {taskId.slice(0, 8)}...
              </span>
            )}
            <button
              onClick={clearLogs}
              className="text-gray-400 hover:text-white transition-colors text-xs px-2 py-1 rounded hover:bg-gray-700"
            >
              Clear
            </button>
          </div>
        </div>

        {/* Logs Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-1" style={{ height }}>
          {displayLogs.length === 0 ? (
            <div className="text-gray-500 italic flex items-center justify-center h-full">
              <div className="text-center">
                <div className="text-2xl mb-2">🤖</div>
                <p>Logs will appear here when your AI crew starts working...</p>
              </div>
            </div>
          ) : (
            displayLogs.map((log) => (
              <div key={log.id} className="flex items-start space-x-3 py-1 hover:bg-gray-800/50 px-2 rounded">
                <span className="text-gray-500 text-xs whitespace-nowrap mt-0.5">
                  {log.timestamp.toLocaleTimeString()}
                </span>
                <span className="flex-1 break-words">
                  {log.message}
                </span>
              </div>
            ))
          )}
          <div ref={logsEndRef} />
        </div>
      </div>
    );
  }

  // Original modal mode
  return (
    <div className="fixed inset-0 bg-gray-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
        
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white">
              AI Crew Execution
            </h1>
            <p className="text-blue-100 text-sm">
              Real-time task execution with live logs
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${connectionStatus === 'connected' ? 'bg-green-500' : connectionStatus === 'connecting' ? 'bg-yellow-500' : connectionStatus === 'error' ? 'bg-red-500' : 'bg-gray-400'}`}></div>
              <span className={`text-sm font-medium ${getStatusColor()}`}>
                {getStatusText()}
              </span>
            </div>
            {taskId && (
              <span className="text-xs text-blue-100 bg-blue-500/20 px-2 py-1 rounded">
                ID: {taskId.slice(0, 8)}...
              </span>
            )}
            {onClose && (
              <button
                onClick={onClose}
                className="text-blue-100 hover:text-white transition-colors p-1 rounded hover:bg-blue-500/20"
                aria-label="Close"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        </div>

        {/* Current Task */}
        {prompt && prompt !== 'Sample task for testing' && (
          <div className="px-6 py-4 bg-blue-50 dark:bg-blue-900/20 border-b border-blue-200 dark:border-blue-800">
            <div className="flex items-start space-x-3">
              <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900/50 rounded-full flex items-center justify-center flex-shrink-0">
                <span className="text-blue-600 dark:text-blue-400 text-sm font-medium">🎯</span>
              </div>
              <div>
                <h3 className="font-medium text-blue-900 dark:text-blue-100 mb-1">Current Task</h3>
                <p className="text-blue-800 dark:text-blue-200 text-sm">{prompt}</p>
              </div>
            </div>
          </div>
        )}

        {/* Controls */}
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                {isRunning ? (
                  <>
                    <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                    <span className="text-sm font-medium text-blue-600">Crew is working...</span>
                  </>
                ) : (
                  <>
                    <div className="w-4 h-4 bg-green-500 rounded-full"></div>
                    <span className="text-sm font-medium text-green-600">Ready</span>
                  </>
                )}
              </div>
            </div>
            
            <button
              onClick={clearLogs}
              className="px-4 py-2 rounded-lg font-medium bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 transition-colors text-sm"
            >
              🗑️ Clear Logs
            </button>
          </div>
        </div>

        {/* Log Output */}
        <div className="flex-1 overflow-y-auto bg-gray-900 text-green-400 font-mono text-sm" style={{ height: '400px' }}>
          <div className="p-4 space-y-1">
            {displayLogs.length === 0 ? (
              <div className="text-gray-500 italic flex items-center justify-center h-full">
                <div className="text-center">
                  <div className="text-2xl mb-2">🤖</div>
                  <p>Waiting for crew to start...</p>
                </div>
              </div>
            ) : (
              displayLogs.map((log) => (
                <div key={log.id} className="flex items-start space-x-3 py-1 hover:bg-gray-800/50 px-2 rounded">
                  <span className="text-gray-500 text-xs whitespace-nowrap mt-0.5">
                    {log.timestamp.toLocaleTimeString()}
                  </span>
                  <span className="flex-1 break-words">
                    {log.message}
                  </span>
                </div>
              ))
            )}
            <div ref={logsEndRef} />
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 bg-gray-50 dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between text-xs text-gray-600 dark:text-gray-400">
            <span>
              {displayLogs.length} log {displayLogs.length === 1 ? 'entry' : 'entries'}
            </span>
            <span>
              Backend: <code className="bg-gray-200 dark:bg-gray-700 px-1 py-0.5 rounded text-xs">
                {getBackendUrl() || 'Not Configured'}
              </code>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
} 