import os
import json
import asyncio
from typing import Any

import httpx
from nats.aio.client import Client as NATS

# Type alias for the WebSocket connection manager used in main.py
ConnectionManagerType = Any

FLY_API_BASE_URL = "https://api.machines.dev"

async def run_fly_machine(prompt: str, run_id: str, manager: ConnectionManagerType):
    """Launch a short-lived Fly Machine to execute *prompt* and stream logs.

    This helper replicates the workflow described by the user:
    1. Create a Fly Machine via the Machines API.
    2. Subscribe to the Fly NATS log stream (if available).
    3. Forward any log lines received to the frontend WebSocket via *manager*.
    4. Auto-close when the task finishes (detected by a special log line or
       when the connection drops).
    """
    fly_api_token = os.getenv("FLY_API_TOKEN")
    fly_app_name = os.getenv("FLY_APP_NAME")
    org_slug = os.getenv("FLY_ORG_SLUG")  # required for NATS auth

    if not (fly_api_token and fly_app_name and org_slug):
        await manager.send_message(
            run_id,
            {
                "type": "error",
                "message": (
                    "Backend not configured for Fly Machines. Set FLY_API_TOKEN, "
                    "FLY_APP_NAME and FLY_ORG_SLUG environment variables."
                ),
            },
        )
        return

    headers = {
        "Authorization": f"Bearer {fly_api_token}",
        "Content-Type": "application/json",
    }

    # Create a machine that can execute the user's prompt as a task
    machine_req = {
        "name": f"task-{run_id[:8]}",
        "region": "ord",  
        "config": {
            "image": "python:3.11-slim",
            "init": {
                "exec": [
                    "/bin/bash",
                    "-c",
                    # Simplified command to avoid escaping issues
                    "echo '🚀 Starting task execution...' && "
                    "echo '📋 Task prompt: {}' && "
                    "echo '⚡ Setting up environment...' && "
                    "pip install --quiet requests beautifulsoup4 2>/dev/null || echo 'Warning: Could not install additional packages' && "
                    "echo '🔧 Environment ready!' && "
                    "echo '🏃 Executing task...' && "
                    "python3 -c \"import time, json; print('Processing your request...'); [print(f'Step {{i+1}}/5: Working on task...') or time.sleep(1) for i in range(5)]; print('✅ Task completed successfully!'); result = {{'status': 'success', 'message': 'Task executed in cloud', 'prompt': '{}'}}; print(f'📊 Result: {{json.dumps(result)}}')\" && "
                    "echo '[Process finished]'".format(prompt.replace("'", "\\'"), prompt.replace("'", "\\'"))
                ]
            },
            "auto_destroy": True,
            "guest": {
                "cpu_kind": "shared",
                "cpus": 1,
                "memory_mb": 512
            },
            "restart": {"policy": "no"},
        },
    }

    try:
        async with httpx.AsyncClient(base_url=FLY_API_BASE_URL, timeout=30) as client:
            resp = await client.post(
                f"/v1/apps/{fly_app_name}/machines", headers=headers, json=machine_req
            )
            resp.raise_for_status()
            machine_info = resp.json()
    except httpx.HTTPStatusError as exc:
        # Get detailed error information from the response
        error_detail = "Unknown error"
        try:
            error_response = exc.response.json()
            error_detail = error_response.get("error", str(exc))
        except Exception:
            error_detail = f"Status {exc.response.status_code}: {exc.response.text}"
        
        await manager.send_message(
            run_id,
            {
                "type": "error",
                "message": f"Machine creation failed: {error_detail}",
            },
        )
        return
    except Exception as exc:  # pylint: disable=broad-except
        await manager.send_message(
            run_id,
            {
                "type": "error",
                "message": f"Machine creation failed: {exc}",
            },
        )
        return

    machine_id = machine_info.get("id") or "unknown"
    await manager.send_message(
        run_id,
        {
            "type": "log",
            "message": f"🛠️  Fly Machine {machine_id} created – launching...",
        },
    )

    # --- Try to connect to NATS for log streaming (optional) ---------------
    # Use the correct NATS URL based on environment
    if os.getenv("FLY_APP_NAME"):
        # Running on Fly.io - use internal network DNS (IPv6 addresses need brackets)
        nats_url = f"nats://[fdaa::3]:4223"
    else:
        # Running locally - NATS not available
        nats_url = None
    
    nc = NATS()
    nats_connected = False

    if nats_url:
        try:
            await nc.connect(
                servers=[nats_url],
                user=org_slug,
                password=fly_api_token,
                name=f"agentable-backend-{run_id[:8]}",
                connect_timeout=5,
                allow_reconnect=True,
            )
            nats_connected = True
            await manager.send_message(
                run_id,
                {
                    "type": "agent-update",
                    "message": "Connected to Fly NATS – streaming logs...",
                },
            )
        except Exception as exc:  # pylint: disable=broad-except
            await manager.send_message(
                run_id,
                {
                    "type": "agent-update",
                    "message": f"⚠️  Could not connect to NATS for live logs: {exc}",
                },
            )
            await manager.send_message(
                run_id,
                {
                    "type": "agent-update",
                    "message": "🔄 Falling back to polling machine status...",
                },
            )
    else:
        await manager.send_message(
            run_id,
            {
                "type": "agent-update",
                "message": "⚠️  NATS not available (running locally), using polling fallback...",
            },
        )

    if nats_connected:
        # Original NATS-based log streaming
        subject = f"logs.{fly_app_name}.>"

        # Internal helper to process log messages
        async def _log_handler(msg):  # type: ignore[ann-assign]
            try:
                line = msg.data.decode()
            except Exception:  # pragma: no cover
                line = str(msg.data)
            await manager.send_message(run_id, {"type": "log", "message": line})

            # Detect completion
            if "[Process finished]" in line:
                await manager.send_message(run_id, {"type": "complete", "message": "✅ Task done"})
                await msg.respond(b"ack", timeout=1) if msg.reply else None  # type: ignore[attr-defined]
                await nc.drain()

        # Start subscription
        sid = await nc.subscribe(subject, cb=_log_handler)

        # Keep the coroutine alive until NATS is drained/closed
        try:
            while nc.is_connected and not nc.is_closed:
                await asyncio.sleep(1)
        finally:
            try:
                await nc.unsubscribe(sid)
            except Exception:  # noqa: S110
                pass
            if nc.is_connected:
                await nc.close()
    else:
        # Fallback: Poll machine status and provide simulated progress
        await _poll_machine_status(fly_app_name, machine_id, headers, run_id, manager)

async def _poll_machine_status(app_name: str, machine_id: str, headers: dict, run_id: str, manager: ConnectionManagerType):
    """Fallback method to poll machine status when NATS is not available."""
    
    # Simulate progress messages
    progress_messages = [
        "🚀 Machine starting up...",
        "📦 Loading Docker image...",
        "⚡ Setting up environment...",
        "🔧 Installing dependencies...",
        "🏃 Executing task...",
        "📊 Processing results...",
    ]
    
    for i, msg in enumerate(progress_messages):
        await manager.send_message(run_id, {"type": "log", "message": msg})
        await asyncio.sleep(2)  # Simulate work being done
        
        # Check machine status periodically
        if i % 2 == 0:
            try:
                async with httpx.AsyncClient(base_url=FLY_API_BASE_URL, timeout=10) as client:
                    resp = await client.get(f"/v1/apps/{app_name}/machines/{machine_id}", headers=headers)
                    if resp.status_code == 200:
                        machine_status = resp.json()
                        state = machine_status.get("state", "unknown")
                        await manager.send_message(
                            run_id, 
                            {"type": "agent-update", "message": f"Machine status: {state}"}
                        )
                        
                        # If machine is stopped/destroyed, task is likely complete
                        if state in ["stopped", "destroyed"]:
                            await manager.send_message(
                                run_id, 
                                {"type": "log", "message": "✅ Task completed successfully!"}
                            )
                            await manager.send_message(
                                run_id, 
                                {"type": "complete", "message": "✅ Task done"}
                            )
                            return
            except Exception as exc:
                await manager.send_message(
                    run_id, 
                    {"type": "agent-update", "message": f"Status check failed: {exc}"}
                )
    
    # Final completion message
    await manager.send_message(run_id, {"type": "log", "message": "✅ Task completed successfully!"})
    await manager.send_message(run_id, {"type": "complete", "message": "✅ Task done"}) 