import asyncio
import json
import re
from typing import Dict, Any
from agents.spec_agent import SpecAgent
from crewai import Crew, Agent, Task

from tools.tool_registry import instantiate_tool

def format_result_for_markdown(result: str) -> str:
    """
    Format the result to ensure URLs are properly formatted as markdown links or images.
    This ensures that image URLs are rendered as images and other URLs as clickable links.
    """
    # Enhanced regex to find URLs in various formats
    url_pattern = r'(https?://[^\s\)\]]+)'
    
    def replace_url(match):
        url = match.group(1)
        # Clean up URL by removing trailing punctuation that might not be part of URL
        url = re.sub(r'[.,;:!?)\]]*$', '', url)
        
        # Check if it's likely an image URL
        if re.search(r'\.(jpg|jpeg|png|gif|webp|svg)(\?.*)?$', url, re.IGNORECASE):
            return f'![Generated Image]({url})'
        else:
            # For other URLs, create a clickable link
            return f'[{url}]({url})'
    
    # Replace URLs with markdown format
    formatted = re.sub(url_pattern, replace_url, result)
    
    # Also handle markdown links that might already be in the result
    # Look for existing markdown link patterns: [text](url)
    markdown_link_pattern = r'\[([^\]]+)\]\((https?://[^\s\)]+)\)'
    
    def enhance_markdown_link(match):
        text = match.group(1)
        url = match.group(2)
        
        # If it's an image URL and the text suggests it's a link, convert to image
        if re.search(r'\.(jpg|jpeg|png|gif|webp|svg)(\?.*)?$', url, re.IGNORECASE):
            if 'here' in text.lower() or 'image' in text.lower() or 'view' in text.lower():
                return f'![Generated Image]({url})'
        
        return match.group(0)  # Return original if no change needed
    
    formatted = re.sub(markdown_link_pattern, enhance_markdown_link, formatted)
    
    return formatted

async def runCrew(prompt: str, run_id: str, manager):
    """
    Main orchestrator function that:
    1. Uses SpecAgent to convert prompt to crew task JSON
    2. Creates CrewAI agents and tasks from the JSON
    3. Executes the crew and broadcasts events via WebSocket
    """
    try:
        max_wait = 10  # seconds
        wait_time = 0
        while run_id not in manager.active_connections and wait_time < max_wait:
            await asyncio.sleep(0.1)
            wait_time += 0.1
        
        if run_id not in manager.active_connections:
            raise Exception("WebSocket connection not established within timeout")

        # Step 1: Use SpecAgent to convert prompt to crew spec
        await manager.send_message(run_id, {
            "type": "agent-update",
            "message": "SpecAgent started - converting prompt to crew specification"
        })
        
        spec_agent = SpecAgent()
        crew_spec = await spec_agent.generate_crew_spec(prompt)
        
        await manager.send_message(run_id, {
            "type": "log",
            "message": f"Generated crew specification with {len(crew_spec.get('tasks', []))} tasks"
        })
        
        await manager.send_message(run_id, {
            "type": "agent-update", 
            "message": "SpecAgent completed - crew specification generated"
        })
        
        # Step 2: Create and execute CrewAI crew from the spec
        crew = await create_crew_from_spec(crew_spec, run_id, manager)
        
        # Step 3: Execute the crew with progress updates
        await manager.send_message(run_id, {
            "type": "log",
            "message": "Starting crew execution..."
        })
        
        # Send agent status updates before execution
        for i, agent in enumerate(crew.agents, 1):
            await manager.send_message(run_id, {
                "type": "agent-update",
                "message": f"🤖 Agent {i}/{len(crew.agents)}: '{agent.role}' is ready"
            })
        
        # Execute crew in thread pool to avoid blocking
        import concurrent.futures
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Send start message
            await manager.send_message(run_id, {
                "type": "agent-update", 
                "message": f"🚀 Starting crew with {len(crew.agents)} agents and {len(crew.tasks)} tasks..."
            })
            
            # Execute crew
            future = executor.submit(crew.kickoff)
            
            # Send progress updates while waiting
            import time
            start_time = time.time()
            while not future.done():
                await asyncio.sleep(2)  # Check every 2 seconds
                elapsed = int(time.time() - start_time)
                await manager.send_message(run_id, {
                    "type": "log",
                    "message": f"Still working... ({elapsed}s elapsed)"
                })
                
                if elapsed > 300:  # 5 minute timeout
                    future.cancel()
                    raise Exception("Crew execution timeout")
            
            result = future.result()
        
        # Step 4: Send completion event
        # Format the result to ensure URLs are properly formatted as markdown
        formatted_result = format_result_for_markdown(str(result))
        
        await manager.send_message(run_id, {
            "type": "complete",
            "message": "Crew execution completed successfully!",
            "result": formatted_result
        })
        
    except Exception as e:
        await manager.send_message(run_id, {
            "type": "error",
            "message": f"Error in crew execution: {str(e)}"
        })

async def create_crew_from_spec(crew_spec: Dict[str, Any], run_id: str, manager) -> Crew:
    """
    Creates a CrewAI Crew object from the generated specification
    """
    agents = []
    tasks = []

    # Create agents based on spec
    for agent_spec in crew_spec.get("agents", []):
        agent_tools = [instantiate_tool(tool_name) for tool_name in agent_spec.get("tools", [])]
    
        agent = Agent(
            role=agent_spec.get("name"),
            goal=agent_spec.get("role_description"),
            backstory=agent_spec.get("role_description"),
            tools=agent_tools,
            verbose=True
        )
        agents.append(agent)

    # Create tasks with completion callbacks
    for task_spec in crew_spec.get("tasks", []):
        agent_name = task_spec.get("agent")

        agent = next((a for a in agents if a.role == agent_name), None)

        if agent:
            # Create task completion callback
            def create_completion_callback(agent_role, task_desc, run_id, manager):
                def callback(task_output):
                    # Schedule the async message sending
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(manager.send_message(run_id, {
                        "type": "agent-update",
                        "message": f"✅ Agent '{agent_role}' completed: {task_desc[:50]}..."
                    }))
                    loop.close()
                return callback

            task = Task(
                description=task_spec.get("description", ""),
                expected_output=task_spec.get("expected_output", "Task completion"),
                agent=agent,
                callback=create_completion_callback(agent.role, task_spec.get("description", ""), run_id, manager)
            )

            tasks.append(task)

            await manager.send_message(run_id, {
                "type": "agent-update",
                "message": f"Task created: {task.description[:50]}..."
            })
    
    # Create and return the crew
    crew = Crew(
        agents=agents,
        tasks=tasks,
        verbose=True
    )
    
    return crew