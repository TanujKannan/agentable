'use client';

import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { startRun, setupWebSocket, WebSocketEvent } from '@/lib/api';

type Status = 'idle' | 'running' | 'complete' | 'error';

export default function Home() {
  const [prompt, setPrompt] = useState('');
  const [runId, setRunId] = useState<string | null>(null);
  const [status, setStatus] = useState<Status>('idle');
  const [logs, setLogs] = useState<string[]>([]);
  const [result, setResult] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const logsEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll logs to bottom
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || status === 'running') return;

    try {
      setStatus('running');
      setLogs([]);
      setResult(null);
      
      // Start the crew run
      const { runId: newRunId } = await startRun(prompt);
      setRunId(newRunId);
      
      // Set up WebSocket connection
      wsRef.current = setupWebSocket(
        newRunId,
        handleWebSocketEvent,
        handleWebSocketError,
        handleWebSocketClose
      );
      
    } catch (error) {
      console.error('Failed to start run:', error);
      setStatus('error');
      setLogs(prev => [...prev, `Error: ${error instanceof Error ? error.message : 'Unknown error'}`]);
    }
  };

  const handleWebSocketEvent = (event: WebSocketEvent) => {
    switch (event.type) {
      case 'log':
        if (event.message) {
          setLogs(prev => [...prev, event.message]);
        }
        break;
      case 'agent-update':
        if (event.message) {
          setLogs(prev => [...prev, `Agent Update: ${event.message}`]);
        }
        break;
      case 'complete':
        setStatus('complete');
        if (event.result) {
          setResult(event.result);
        }
        if (event.message) {
          setLogs(prev => [...prev, `Complete: ${event.message}`]);
        }
        break;
      case 'error':
        setStatus('error');
        if (event.message) {
          setLogs(prev => [...prev, `Error: ${event.message}`]);
        }
        break;
    }
  };

  const handleWebSocketError = (error: Event) => {
    console.error('WebSocket error:', error);
    setStatus('error');
    setLogs(prev => [...prev, 'Connection error occurred']);
  };

  const handleWebSocketClose = (event: CloseEvent) => {
    console.log('WebSocket closed:', event.code, event.reason);
    if (status === 'running') {
      setStatus('error');
      setLogs(prev => [...prev, 'Connection closed unexpectedly']);
    }
  };

  const getStatusColor = (status: Status) => {
    switch (status) {
      case 'idle': return 'bg-gray-100 text-gray-800';
      case 'running': return 'bg-blue-100 text-blue-800';
      case 'complete': return 'bg-green-100 text-green-800';
      case 'error': return 'bg-red-100 text-red-800';
    }
  };

  const resetSession = () => {
    setPrompt('');
    setRunId(null);
    setStatus('idle');
    setLogs([]);
    setResult(null);
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      <div className="max-w-6xl mx-auto p-6">
        {/* Header */}
        <div className="text-center mb-8 pt-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 bg-clip-text text-transparent mb-2">
            Agentable
          </h1>
          <p className="text-gray-600 text-lg">
            Your AI crew manager
          </p>
          
          {/* Status Badge */}
          <div className="mt-4">
            <Badge className={`${getStatusColor(status)} px-3 py-1 text-sm font-medium`}>
              {status === 'idle' && 'Ready'}
              {status === 'running' && 'AI Crew Working...'}
              {status === 'complete' && 'Task Complete'}
              {status === 'error' && 'Error Occurred'}
            </Badge>
            {runId && (
              <p className="text-xs text-gray-500 mt-1">Run ID: {runId}</p>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Prompt Input Section */}
          <div>
            <Card className="border-0 shadow-lg bg-white/80 backdrop-blur-sm">
              <div className="bg-gradient-to-r from-blue-500 to-purple-500 text-white p-6">
                <CardTitle className="text-lg font-medium flex items-center justify-between">
                  Create Task
                  {status !== 'idle' && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={resetSession}
                      className="text-white border-white hover:bg-white hover:text-purple-600"
                    >
                      New Task
                    </Button>
                  )}
                </CardTitle>
              </div>
              <CardContent className="p-6">
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="prompt" className="text-sm font-medium text-gray-700">
                      Describe what you need
                    </Label>
                    <Textarea
                      id="prompt"
                      value={prompt}
                      onChange={(e) => setPrompt(e.target.value)}
                      placeholder="What would you like your AI crew to help you with?"
                      className="min-h-[120px] resize-none border-gray-300 focus:border-purple-500 focus:ring-purple-500 bg-white/50"
                      disabled={status === 'running'}
                    />
                  </div>
                  
                  <Button
                    type="submit"
                    disabled={!prompt.trim() || status === 'running'}
                    className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white shadow-lg hover:shadow-xl transition-all duration-200"
                    size="lg"
                  >
                    {status === 'running' ? (
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        Creating crew...
                      </div>
                    ) : (
                      'Create AI Crew'
                    )}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </div>

          {/* Real-time Output Section */}
          <div>
            <Card className="border-0 shadow-lg bg-white/80 backdrop-blur-sm h-full">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg font-medium text-gray-800">
                  Live Output
                </CardTitle>
              </CardHeader>
              <CardContent className="p-6 pt-0">
                {/* Logs Display */}
                <div className="space-y-4">
                  <div className="bg-gray-900 rounded-lg p-4 h-64 overflow-y-auto">
                    {logs.length === 0 ? (
                      <p className="text-gray-400 text-sm">Logs will appear here when your crew starts working...</p>
                    ) : (
                      <div className="space-y-1">
                        {logs.map((log, index) => (
                          <div key={index} className="text-green-400 text-sm font-mono">
                            {log}
                          </div>
                        ))}
                        <div ref={logsEndRef} />
                      </div>
                    )}
                  </div>

                  {/* Results Section */}
                  {result && (
                    <>
                      <Separator />
                      <div>
                        <h3 className="text-sm font-medium text-gray-700 mb-2">Final Result:</h3>
                        <div className="bg-green-50 border border-green-200 rounded-lg p-4 max-h-64 overflow-y-auto">
                          <pre className="text-sm text-green-800 whitespace-pre-wrap">{result}</pre>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
