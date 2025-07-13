from dotenv import load_dotenv
load_dotenv()

import asyncio
import json
import uuid
from typing import Dict, Any
import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.orchestrator import runCrew
from services.fly_machine_launcher import run_fly_machine

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "https://agentable-frontend.fly.dev",  # Production frontend
        "https://*.fly.dev",  # Allow any fly.dev subdomain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, run_id: str):
        await websocket.accept()
        self.active_connections[run_id] = websocket

    def disconnect(self, run_id: str):
        if run_id in self.active_connections:
            del self.active_connections[run_id]

    async def send_message(self, run_id: str, message: dict):
        if run_id in self.active_connections:
            websocket = self.active_connections[run_id]
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                print(f"Error sending message to {run_id}: {e}")
                self.disconnect(run_id)

manager = ConnectionManager()

class RunRequest(BaseModel):
    prompt: str

@app.post("/api/run")
async def run_task(request: RunRequest, background_tasks: BackgroundTasks):
    """Start a crew execution task and return the task ID."""
    run_id = str(uuid.uuid4())
    
    background_tasks.add_task(runCrew, request.prompt, run_id, manager)
    
    return {"taskId": run_id}

@app.websocket("/api/ws/{task_id}")
async def stream_logs(websocket: WebSocket, task_id: str):
    """WebSocket endpoint to stream real-time updates for a given task_id."""
    await manager.connect(websocket, task_id)
    
    try:
        # Keep the connection alive and wait for messages
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(task_id)

@app.get("/")
async def root():
    return {"message": "Agentable Backend API "}