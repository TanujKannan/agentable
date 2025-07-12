// Simple API integration for Agentable backend
// No external dependencies - uses native fetch and WebSocket

export type EventType = 'agent-update' | 'log' | 'complete' | 'error';

export interface RunResponse {
  runId: string;
}

export interface WebSocketEvent {
  type: EventType;
  message: string;
  result?: string;
  data?: unknown;
}

// Start a new crew run
export const startRun = async (prompt: string): Promise<RunResponse> => {
  const response = await fetch('http://localhost:8000/api/run', {
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
  const ws = new WebSocket(`ws://localhost:8000/api/ws/${runId}`);
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