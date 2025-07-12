from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import asyncio
from typing import Dict
import json

from services.orchestrator import runCrew

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RunRequest(BaseModel):
    prompt: str

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
            try:
                await self.active_connections[run_id].send_text(json.dumps(message))
            except:
                self.disconnect(run_id)

manager = ConnectionManager()

@app.post("/api/run")
async def run_endpoint(request: RunRequest):
    run_id = str(uuid.uuid4())
    
    # Start crew execution in background
    asyncio.create_task(runCrew(request.prompt, run_id, manager))
    
    return {"runId": run_id}

@app.websocket("/api/ws/{run_id}")
async def websocket_endpoint(websocket: WebSocket, run_id: str):
    await manager.connect(websocket, run_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(run_id)

@app.get("/")
async def root():
    return {"message": "Agentable Backend API"}