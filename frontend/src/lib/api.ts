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
  if (process.env.NODE_ENV === 'production') {
    if (!process.env.NEXT_PUBLIC_BACKEND_URL) {
      throw new Error("NEXT_PUBLIC_BACKEND_URL is not set in production");
    }
    return process.env.NEXT_PUBLIC_BACKEND_URL;
  }
  return process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
};

const getWebSocketUrl = () => {
  const backendUrl = getBackendUrl();
  return backendUrl.replace(/^http/, 'ws');
};

// Start a new crew run
export const startRun = async (prompt: string): Promise<RunResponse> => {
    const backendUrl = getBackendUrl();
    if (!backendUrl) {
        throw new Error("Backend URL is not configured");
    }
    
    console.log(`Making request to: ${backendUrl}/api/run`);
    
    try {
        const response = await fetch(`${backendUrl}/api/run`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ prompt }),
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error(`Server responded with ${response.status}: ${errorText}`);
            throw new Error(`Failed to start run: ${response.status} ${response.statusText}`);
        }

        return response.json();
    } catch (error) {
        console.error('Network error:', error);
        if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
            throw new Error(`Cannot connect to backend at ${backendUrl}. Please check if the backend is running and accessible.`);
        }
        throw error;
    }
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