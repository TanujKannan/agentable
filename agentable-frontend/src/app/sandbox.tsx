'use client';

import { useState, useRef, useEffect } from 'react';

interface LogEntry {
  id: string;
  message: string;
  timestamp: Date;
}

export default function LogStreamingDemo() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected');
  const wsRef = useRef<WebSocket | null>(null);
  const logsEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const addLog = (message: string) => {
    const newLog: LogEntry = {
      id: Date.now().toString() + Math.random().toString(36),
      message,
      timestamp: new Date()
    };
    setLogs(prev => [...prev, newLog]);
  };

  const connectWebSocket = (taskId: string) => {
    if (wsRef.current) {
      wsRef.current.close();
    }

    setConnectionStatus('connecting');
    const ws = new WebSocket(`ws://localhost:8000/ws/logs/${taskId}`);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnectionStatus('connected');
      addLog('🟢 Connected to log stream');
    };

    ws.onmessage = (event) => {
      const message = event.data;
      if (message === '[Process finished]') {
        addLog('✅ Process completed');
        setIsRunning(false);
        setConnectionStatus('disconnected');
        ws.close();
      } else {
        addLog(message);
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
  };

  const runTask = async () => {
    if (isRunning) return;

    setIsRunning(true);
    setLogs([]);
    setTaskId(null);
    addLog('🚀 Starting task...');

    try {
      const response = await fetch('http://localhost:8000/run-task', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const newTaskId = data.task_id;
      setTaskId(newTaskId);
      addLog(`📋 Task created with ID: ${newTaskId}`);
      
      // Connect to WebSocket for real-time logs
      connectWebSocket(newTaskId);

    } catch (error) {
      addLog(`❌ Error starting task: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setIsRunning(false);
    }
  };

  const clearLogs = () => {
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

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-4">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-hidden">
          
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-4">
            <h1 className="text-2xl font-bold text-white">
              Real-time Log Streaming Demo
            </h1>
            <p className="text-blue-100 mt-1">
              Execute tasks and stream logs in real-time from your backend
            </p>
          </div>

          {/* Controls */}
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <button
                  onClick={runTask}
                  disabled={isRunning}
                  className={`px-6 py-2 rounded-lg font-medium transition-all duration-200 ${
                    isRunning 
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed' 
                      : 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg hover:shadow-xl'
                  }`}
                >
                  {isRunning ? (
                    <span className="flex items-center">
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Running...
                    </span>
                  ) : (
                    '🚀 Run Task'
                  )}
                </button>
                
                <button
                  onClick={clearLogs}
                  className="px-4 py-2 rounded-lg font-medium bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 transition-colors"
                >
                  🗑️ Clear Logs
                </button>
              </div>

              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <div className={`w-2 h-2 rounded-full ${connectionStatus === 'connected' ? 'bg-green-500' : connectionStatus === 'connecting' ? 'bg-yellow-500' : connectionStatus === 'error' ? 'bg-red-500' : 'bg-gray-400'}`}></div>
                  <span className={`text-sm font-medium ${getStatusColor()}`}>
                    {getStatusText()}
                  </span>
                </div>
                {taskId && (
                  <span className="text-sm text-gray-500 dark:text-gray-400">
                    Task ID: {taskId.slice(0, 8)}...
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Log Output */}
          <div className="h-96 overflow-y-auto bg-gray-900 text-green-400 font-mono text-sm">
            <div className="p-4 space-y-1">
              {logs.length === 0 ? (
                <div className="text-gray-500 italic">
                  No logs yet. Click "Run Task" to start streaming logs...
                </div>
              ) : (
                logs.map((log) => (
                  <div key={log.id} className="flex items-start space-x-3 py-1">
                    <span className="text-gray-500 text-xs whitespace-nowrap">
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
          <div className="px-6 py-4 bg-gray-50 dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
              <span>
                Backend: <code className="bg-gray-200 dark:bg-gray-700 px-2 py-1 rounded">http://localhost:8000</code>
              </span>
              <span>
                {logs.length} log entries
              </span>
            </div>
          </div>
        </div>

        {/* Instructions */}
        <div className="mt-6 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-2">
            How it works:
          </h3>
          <ol className="list-decimal list-inside space-y-1 text-blue-800 dark:text-blue-200 text-sm">
            <li>Click "Run Task" to start a new task on the backend</li>
            <li>The backend creates a subprocess and returns a task ID</li>
            <li>Frontend connects to WebSocket at <code>/ws/logs/{'{task_id}'}</code></li>
            <li>Logs stream in real-time as the subprocess runs</li>
            <li>Connection closes when the process completes</li>
          </ol>
        </div>
      </div>
    </div>
  );
} 