'use client';

import { useState, useRef, useEffect } from 'react';
import Image from 'next/image';
import { startRun, setupWebSocket, WebSocketEvent, HistoryRun } from '@/lib/api';
import ChatInterface from '@/components/ChatInterface';
import OutputPanel from '@/components/OutputPanel';
import LandingChatInput from '@/components/LandingChatInput';
import HistoryPanel from '@/components/HistoryPanel';
import { PipelineData } from '@/lib/types';

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
  const [pipelineData, setPipelineData] = useState<PipelineData | null>(null);
  const [agentUpdates, setAgentUpdates] = useState<WebSocketEvent[]>([]);
  const [isLandingMode, setIsLandingMode] = useState(true);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
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

    // If we're in landing mode, handle the transition
    if (isLandingMode) {
      // Start transition
      setIsTransitioning(true);
      
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
      
      // After transition, switch to two-panel view and start the run
      setTimeout(async () => {
        setIsLandingMode(false);
        setIsTransitioning(false);
        
        // Now start the actual run
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
      }, 800);
      
      return;
    }

    // If we're already in two-panel mode, handle normally
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
        setPipelineData(event.data as PipelineData);
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

  const handleSelectHistoryRun = (run: HistoryRun) => {
    // Load the historical run data
    if (run.pipeline_data) {
      setPipelineData(run.pipeline_data);
    }
    if (run.result) {
      setResult(run.result);
    }
    
    // Add the prompt as a user message
    const userMessage: ChatMessage = {
      id: `history_${run.id}`,
      content: run.prompt,
      type: 'user',
      timestamp: new Date(run.timestamp),
    };
    
    // Add completion message
    const systemMessage: ChatMessage = {
      id: `history_system_${run.id}`,
      content: run.status === 'complete' ? 'Task completed successfully ✓' : 
               run.status === 'error' ? 'Task failed ✗' : 'Task in progress...',
      type: 'system',
      timestamp: new Date(run.timestamp),
    };
    
    setMessages([userMessage, systemMessage]);
    setRunId(run.id);
    setStatus(run.status as Status);
    setShowHistory(false);
  };

  if (isLandingMode || isTransitioning) {
    return (
      <div className="h-screen relative overflow-hidden">
        {/* Gradient Background */}
        <div className={`absolute inset-0 bg-gradient-to-br from-[#1F3A93] via-[#17A589] to-[#F5B041] transition-all duration-800 ${
          isTransitioning ? 'opacity-0' : 'opacity-100'
        }`}>
          {/* Animated background elements */}
          <div className="absolute top-20 left-20 w-64 h-64 bg-white/10 rounded-full blur-3xl animate-pulse"></div>
          <div className="absolute bottom-20 right-20 w-96 h-96 bg-white/5 rounded-full blur-3xl animate-pulse" style={{animationDelay: '1s'}}></div>
          <div className="absolute top-1/2 left-1/3 w-32 h-32 bg-white/15 rounded-full blur-2xl animate-pulse" style={{animationDelay: '2s'}}></div>
        </div>

        {/* White background for transition */}
        <div className={`absolute inset-0 bg-[#F7F9FA] transition-all duration-800 ${
          isTransitioning ? 'opacity-100' : 'opacity-0'
        }`}></div>

        {/* Content */}
        <div className="relative z-10 h-full flex flex-col items-center justify-center p-8 -mt-16">
          {/* Logo and Header */}
          <div className={`mb-6 text-center transition-all duration-800 ${
            isTransitioning ? 'opacity-0 scale-95 -translate-y-8' : 'opacity-100 scale-100 translate-y-0'
          }`}>
            <div className="flex items-center justify-center">
              <Image 
                src="/agentablelogowhitetext.png" 
                alt="Agentable" 
                width={1000}
                height={300}
                className="h-40 w-auto drop-shadow-lg object-cover object-center"
                style={{
                  clipPath: 'inset(35% 0 25% 0)'
                }}
              />
            </div>
          </div>

          {/* Main Chat Interface */}
          <div className={`w-full max-w-2xl transition-all duration-800 ${
            isTransitioning 
              ? 'transform scale-110 opacity-0' 
              : 'transform scale-100 opacity-100'
          }`}>
            <div className="bg-white/95 backdrop-blur-sm rounded-2xl shadow-2xl p-8 border border-white/20">
              <div className={`mb-6 text-center transition-all duration-800 ${
                isTransitioning ? 'opacity-0' : 'opacity-100'
              }`}>
                <h2 className="text-2xl font-semibold text-[#2C3E50] mb-2">What can I help you build today?</h2>
                <p className="text-[#2C3E50]/70">Describe your task and I&apos;ll create the perfect AI crew to complete it</p>
              </div>
              
              {/* Landing Chat Input */}
              <div className="space-y-4">
                <LandingChatInput onSubmit={handleChatSubmit} isLoading={status === 'running'} />
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-[#F7F9FA] flex flex-col transition-all duration-500">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <Image 
              src="/agentablelogoblacktext.png" 
              alt="Agentable" 
              width={200}
              height={40}
              className="h-8 w-auto"
            />
            <div className="ml-3">
              <p className="text-sm text-[#2C3E50]">Automate Intelligently, Deliver Powerfully</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={() => setShowHistory(!showHistory)}
              className={`px-3 py-1 text-sm rounded-lg transition-colors ${
                showHistory 
                  ? 'bg-[#17A589] text-white' 
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              History
            </button>
            <div className="text-right">
              {runId && (
                <p className="text-xs text-gray-500">Run ID: {runId}</p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* History Panel - Conditionally shown on left */}
        {showHistory && (
          <div className="w-80 min-w-0">
            <HistoryPanel onSelectRun={handleSelectHistoryRun} />
          </div>
        )}

        {/* Chat Panel - Left side, takes proportional space */}
        <div className={`${showHistory ? 'w-80' : 'w-[35%]'} min-w-0 border-r border-gray-200`}>
          <ChatInterface
            onSubmit={handleChatSubmit}
            isLoading={status === 'running'}
            messages={messages}
          />
        </div>

        {/* Output Panel - Right side, takes remaining space */}
        <div className="flex-1 min-w-0">
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