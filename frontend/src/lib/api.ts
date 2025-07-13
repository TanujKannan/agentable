// Simple API integration for Agentable backend
// No external dependencies - uses native fetch and WebSocket

export type EventType = 'agent-update' | 'log' | 'complete' | 'error' | 'pipeline-init';

export interface RunResponse {
  runId: string;
}

export interface WebSocketEvent {
  type: EventType;
  message: string;
  result?: string;
  data?: unknown;
  agent_id?: number;
  task_id?: number;
  agent_status?: string;
  task_status?: string;
  pipeline_status?: string;
}

// Get the backend URL from environment variables
const getBackendUrl = () => {
  // In production, use the deployed backend URL
  if (process.env.NODE_ENV === 'production') {
    return process.env.NEXT_PUBLIC_BACKEND_URL || 'https://backend-holy-violet-2759.fly.dev';
  }
  // In development, use localhost
  return process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
};

const getWebSocketUrl = () => {
  // In production, use wss for secure WebSocket connection
  if (process.env.NODE_ENV === 'production') {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'https://backend-holy-violet-2759.fly.dev';
    return backendUrl.replace('https://', 'wss://');
  }
  // In development, use ws
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
  return backendUrl.replace('http://', 'ws://');
};

// Start a new crew run
export const startRun = async (prompt: string): Promise<RunResponse> => {
  const response = await fetch(`${getBackendUrl()}/api/run`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ prompt }),
  });

  if (!response.ok) {
    throw new Error(`Failed to start run: ${response.statusText}`);
  }

  return response.json();
};

// Create WebSocket connection for real-time updates
export const createWebSocket = (runId: string): WebSocket => {
  const ws = new WebSocket(`${getWebSocketUrl()}/api/ws/${runId}`);
  return ws;
};

// WebSocket event handler type
export type WebSocketEventHandler = (event: WebSocketEvent) => void;

// Helper to set up WebSocket with event handlers
export const setupWebSocket = (
  runId: string,
  onEvent: WebSocketEventHandler,
  onError?: (error: Event) => void,
  onClose?: (event: CloseEvent) => void
): WebSocket => {
  const ws = createWebSocket(runId);

  ws.onmessage = (event) => {
    try {
      const data: WebSocketEvent = JSON.parse(event.data);
      onEvent(data);
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  };

  if (onError) {
    ws.onerror = onError;
  }

  if (onClose) {
    ws.onclose = onClose;
  }

  return ws;
};