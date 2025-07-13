'use client';

import { useState, useRef, useEffect } from 'react';
import { startRun, setupWebSocket, WebSocketEvent } from '@/lib/api';
import ChatInterface from '@/components/ChatInterface';
import OutputPanel from '@/components/OutputPanel';

type Status = 'idle' | 'running' | 'complete' | 'error';

interface ChatMessage {
  id: string;
  content: string;
  type: 'user' | 'system' | 'loading';
  timestamp: Date;
}

export default function Home() {
  const [runId, setRunId] = useState<string | null>(null);
  const [status, setStatus] = useState<Status>('idle');
  const [logs, setLogs] = useState<string[]>([]);
  const [result, setResult] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [pipelineData, setPipelineData] = useState<any>(null);
  const [agentUpdates, setAgentUpdates] = useState<any[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const handleChatSubmit = async (message: string) => {
    if (status === 'running') return;

    // Add user message to chat
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      content: message,
      type: 'user',
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMessage]);

    // Add loading message
    const loadingMessage: ChatMessage = {
      id: Date.now().toString() + '_loading',
      content: '',
      type: 'loading',
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, loadingMessage]);

    try {
      setStatus('running');
      setLogs([]);
      setResult(null);
      setPipelineData(null);
      setAgentUpdates([]);
      
      // Start the crew run
      const { runId: newRunId } = await startRun(message);
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
      // Remove loading message and add error message to chat
      setMessages(prev => {
        const filtered = prev.filter(msg => msg.type !== 'loading');
        const errorMessage: ChatMessage = {
          id: Date.now().toString() + '_error',
          content: 'Failed to start task ✗',
          type: 'system',
          timestamp: new Date(),
        };
        return [...filtered, errorMessage];
      });
      setLogs(prev => [...prev, `Error: ${error instanceof Error ? error.message : 'Unknown error'}`]);
    }
  };

  const handleWebSocketEvent = (event: WebSocketEvent) => {
    switch (event.type) {
      case 'log':
        setLogs(prev => [...prev, event.message]);
        break;
      case 'pipeline-init':
        setPipelineData(event.data);
        break;
      case 'agent-update':
        setLogs(prev => [...prev, `Agent Update: ${event.message}`]);
        setAgentUpdates(prev => [...prev, event]);
        break;
      case 'complete':
        setStatus('complete');
        if (event.result) {
          setResult(event.result);
          console.log('Result received:', event.result);
          // Remove loading message and add simple completion message to chat
          setMessages(prev => {
            const filtered = prev.filter(msg => msg.type !== 'loading');
            const completionMessage: ChatMessage = {
              id: Date.now().toString() + '_complete',
              content: 'Task completed successfully ✓',
              type: 'system',
              timestamp: new Date(),
            };
            return [...filtered, completionMessage];
          });
        }
        setLogs(prev => [...prev, `Complete: ${event.message}`]);
        break;
      case 'error':
        setStatus('error');
        // Remove loading message and add error message to chat
        setMessages(prev => {
          const filtered = prev.filter(msg => msg.type !== 'loading');
          const errorMessage: ChatMessage = {
            id: Date.now().toString() + '_error',
            content: 'Task failed ✗',
            type: 'system',
            timestamp: new Date(),
          };
          return [...filtered, errorMessage];
        });
        setLogs(prev => [...prev, `Error: ${event.message}`]);
        break;
    }
  };

  const handleWebSocketError = (error: Event) => {
    console.error('WebSocket error:', error);
    setStatus('error');
    // Remove loading message and add error message to chat
    setMessages(prev => {
      const filtered = prev.filter(msg => msg.type !== 'loading');
      const errorMessage: ChatMessage = {
        id: Date.now().toString() + '_error',
        content: 'Connection error ✗',
        type: 'system',
        timestamp: new Date(),
      };
      return [...filtered, errorMessage];
    });
    setLogs(prev => [...prev, 'Connection error occurred']);
  };

  const handleWebSocketClose = (event: CloseEvent) => {
    console.log('WebSocket closed:', event.code, event.reason);
    if (status === 'running') {
      setStatus('error');
      // Remove loading message and add error message to chat
      setMessages(prev => {
        const filtered = prev.filter(msg => msg.type !== 'loading');
        const errorMessage: ChatMessage = {
          id: Date.now().toString() + '_error',
          content: 'Connection lost ✗',
          type: 'system',
          timestamp: new Date(),
        };
        return [...filtered, errorMessage];
      });
      setLogs(prev => [...prev, 'Connection closed unexpectedly']);
    }
  };

  return (
    <div className="h-screen bg-[#F7F9FA] flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img 
              src="/agentablelogo.png" 
              alt="Agentable" 
              className="h-8 w-auto"
            />
            <div>
              <h1 className="text-2xl font-bold text-[#1F3A93]">Agentable</h1>
              <p className="text-sm text-[#2C3E50]">Automate Intelligently, Deliver Powerfully</p>
            </div>
          </div>
          <div className="text-right">
            {runId && (
              <p className="text-xs text-gray-500">Run ID: {runId}</p>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Chat Panel - Left side, takes 35% of screen */}
        <div className="w-[35%] min-w-0 border-r border-gray-200">
          <ChatInterface
            onSubmit={handleChatSubmit}
            isLoading={status === 'running'}
            messages={messages}
          />
        </div>

        {/* Output Panel - Right side, takes 65% of screen */}
        <div className="w-[65%] min-w-0">
          <OutputPanel
            logs={logs}
            result={result}
            status={status}
            runId={runId}
            pipelineData={pipelineData}
            agentUpdates={agentUpdates}
          />
        </div>
      </div>
    </div>
  );
}