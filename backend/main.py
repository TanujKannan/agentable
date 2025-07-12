from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import uuid
import subprocess
from pathlib import Path
from typing import Dict, Any

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory registry of running tasks → {task_id: {"process": Popen, "queue": asyncio.Queue}}
TASKS: Dict[str, Dict[str, Any]] = {}

INFRA_SCRIPT = Path(__file__).parent / "tests" / "json_crew_example.py"

if not INFRA_SCRIPT.exists():
    # Fallback for "python backend/tests/infra_test.py" when running from repo root
    alt = Path(__file__).parent / "tests" / "json_crew_example.py"
    if alt.exists():
        INFRA_SCRIPT = alt


async def _read_stream(proc: subprocess.Popen, queue: asyncio.Queue):
    """Background task: read lines from process stdout and put into queue."""
    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, proc.stdout)

    while not reader.at_eof():
        try:
            line = await reader.readline()
            if line:
                await queue.put(line.decode().rstrip())
        except Exception:
            break

    await queue.put(None)  # Sentinel to indicate completion


@app.post("/run-task")
async def run_task(background_tasks: BackgroundTasks):
    """Launch infra_test.py as a subprocess and start reading its stdout."""
    task_id = str(uuid.uuid4())

    proc = subprocess.Popen(
        ["python", str(INFRA_SCRIPT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=False,
        bufsize=1,
    )

    queue: asyncio.Queue = asyncio.Queue()
    TASKS[task_id] = {"process": proc, "queue": queue}

    # Start asynchronous reader in background
    background_tasks.add_task(_read_stream, proc, queue)

    return {"task_id": task_id}


@app.websocket("/ws/logs/{task_id}")
async def stream_logs(websocket: WebSocket, task_id: str):
    """WebSocket endpoint to stream log lines for a given task_id."""
    await websocket.accept()
    
    if task_id not in TASKS:
        await websocket.close(code=4001)
        return
    queue: asyncio.Queue = TASKS[task_id]["queue"]

    try:
        while True:
            line = await queue.get()
            if line is None:  # Process finished
                await websocket.send_text("[Process finished]")
                break
            await websocket.send_text(line)
    except WebSocketDisconnect:
        pass
    finally:
        # Cleanup if no other clients are expected.
        proc: subprocess.Popen = TASKS[task_id]["process"]
        if proc.poll() is None:
            proc.terminate()
        TASKS.pop(task_id, None)


@app.get("/")
async def root():
    return {"message": "Backend POC is running"}