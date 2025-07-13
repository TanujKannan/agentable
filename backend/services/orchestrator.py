import asyncio
import json
import re
from typing import Dict, Any
from agents.spec_agent import SpecAgent
from crewai import Crew, Agent, Task

from tools.tool_registry import instantiate_tool
from tools.context_store import RunContext

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
            "message": "🧠 SpecAgent started - analyzing your request and creating crew specification..."
        })
        
        spec_agent = SpecAgent()
        crew_spec = await spec_agent.generate_crew_spec(prompt)
        
        await manager.send_message(run_id, {
            "type": "log",
            "message": f"📋 Generated crew specification with {len(crew_spec.get('agents', []))} agents and {len(crew_spec.get('tasks', []))} tasks"
        })
        
        # Log which tools are available for each agent with visual indicators
        for agent_spec in crew_spec.get('agents', []):
            agent_name = agent_spec.get('name')
            tools = agent_spec.get('tools', [])
            if tools:
                # Add visual indicators for different tool types
                tool_indicators = []
                for tool in tools:
                    if tool == 'browserbase_tool':
                        tool_indicators.append('🌐 browserbase_tool')
                    elif tool == 'serper_dev_tool':
                        tool_indicators.append('🔍 serper_dev_tool')
                    elif tool == 'dalle_tool':
                        tool_indicators.append('🎨 dalle_tool')
                    elif tool == 'website_search_tool':
                        tool_indicators.append('🔗 website_search_tool')
                    elif tool == 'code_docs_search_tool':
                        tool_indicators.append('📚 code_docs_search_tool')
                    else:
                        tool_indicators.append(f'🔧 {tool}')
                
                tool_list = ', '.join(tool_indicators)
                await manager.send_message(run_id, {
                    "type": "log",
                    "message": f"🤖 Agent '{agent_name}' equipped with: {tool_list}"
                })
            else:
                await manager.send_message(run_id, {
                    "type": "log",
                    "message": f"🤖 Agent '{agent_name}' has no tools (analysis/reasoning only)"
                })
        
        await manager.send_message(run_id, {
            "type": "agent-update", 
            "message": "✅ SpecAgent completed - crew specification ready!"
        })
        
        # Step 2: Create and execute CrewAI crew from the spec
        crew = await create_crew_from_spec(crew_spec, run_id, manager)
        
        # Step 3: Send pipeline initialization data (only agents with tasks)
        agents_with_tasks = []
        pipeline_tasks = []
        
        for task_idx, task in enumerate(crew.tasks):
            agent_idx = next((i for i, agent in enumerate(crew.agents) if agent == task.agent), 0)
            agent = crew.agents[agent_idx]
            
            # Only add agent if not already added
            if not any(a["role"] == agent.role for a in agents_with_tasks):
                agents_with_tasks.append({
                    "id": len(agents_with_tasks), 
                    "role": agent.role, 
                    "status": "pending"
                })
            
            # Find the agent ID in our filtered list
            filtered_agent_id = next((i for i, a in enumerate(agents_with_tasks) if a["role"] == agent.role), 0)
            
            pipeline_tasks.append({
                "id": task_idx, 
                "description": task.description[:50] + "...", 
                "agent_id": filtered_agent_id, 
                "status": "pending"
            })
        
        pipeline_data = {
            "agents": agents_with_tasks,
            "tasks": pipeline_tasks
        }
        await manager.send_message(run_id, {
            "type": "pipeline-init",
            "data": pipeline_data
        })
        
        # Step 4: Execute the crew with progress updates
        await manager.send_message(run_id, {
            "type": "log",
            "message": "🚀 Initializing crew execution pipeline..."
        })
        
        # Send agent initialization updates (only for agents with tasks)
        for i, agent_data in enumerate(agents_with_tasks):
            await manager.send_message(run_id, {
                "type": "agent-update",
                "message": f"⚡ Agent {i+1}/{len(agents_with_tasks)} initialized: '{agent_data['role']}' ready for action",
                "agent_id": i,
                "agent_status": "ready"
            })
            await asyncio.sleep(0.2)  # Small delay for visual effect
        
        # Execute crew in thread pool to avoid blocking
        import concurrent.futures
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Send start message
            await manager.send_message(run_id, {
                "type": "agent-update", 
                "message": f"🚀 Starting crew with {len(agents_with_tasks)} agents and {len(crew.tasks)} tasks...",
                "pipeline_status": "running"
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
    
    # Create a shared context for tools that need it
    run_context = RunContext()

    # Create agents based on spec
    for agent_spec in crew_spec.get("agents", []):
        agent_tools = []
        agent_tools = [instantiate_tool(tool_name, context=run_context) for tool_name in agent_spec.get("tools", [])]
        
        # Log which tools the agent is using
        tool_names = agent_spec.get("tools", [])
        await manager.send_message(run_id, {
            "type": "log",
            "message": f"🛠️ Agent '{agent_spec.get('name')}' configured with tools: {', '.join(tool_names)}"
        })
    
        agent = Agent(
            role=agent_spec.get("name"),
            goal=agent_spec.get("role_description"),
            backstory=agent_spec.get("role_description"),
            tools=agent_tools,
            verbose=True
        )
        agents.append(agent)

    # Create tasks with completion callbacks
    tasks_with_tasks = []
    for task_idx, task_spec in enumerate(crew_spec.get("tasks", [])):
        agent_name = task_spec.get("agent")
        agent = next((a for a in agents if a.role == agent_name), None)

        if agent:
            # Get tool parameters for this task
            tool_params = task_spec.get("tool_params", [])
            
            # Create tools with context - parameters will be passed at runtime by CrewAI
            task_specific_tools = []
            for param_set in tool_params:
                tool_name = param_set.get("tool")
                if tool_name:
                    # Instantiate the tool with context
                    tool_instance = instantiate_tool(tool_name, context=run_context)
                    task_specific_tools.append(tool_instance)
            
            # Create a task-specific agent with the tools
            # Include tool parameters in the agent's context
            tool_params_info = ""
            for param_set in tool_params:
                tool_name = param_set.get("tool")
                if tool_name:
                    tool_params_info += f"\n{tool_name} parameters: {json.dumps({k: v for k, v in param_set.items() if k != 'tool'})}"
            
            task_agent = Agent(
                role=agent.role,
                goal=agent.goal,
                backstory=agent.backstory + f"\n\nAvailable tool parameters for this task:{tool_params_info}",
                tools=task_specific_tools,  # Use the tools
                verbose=True
            )
            
            # Debug: Log the agent's backstory with tool parameters
            await manager.send_message(run_id, {
                "type": "log",
                "message": f"Agent backstory for task '{task_spec.get('name')}': {task_agent.backstory}"
            })

            # Track agents with tasks for proper ID mapping
            if not any(a["role"] == agent.role for a in agents_with_tasks):
                agents_with_tasks.append({"role": agent.role, "agent_obj": agent})
            
            # Get the filtered agent ID
            filtered_agent_id = next((i for i, a in enumerate(agents_with_tasks) if a["role"] == agent.role), 0)
            
            # Create task completion callback
            def create_completion_callback(agent_role, task_desc, task_id, agent_id, run_id, manager):
                def callback(task_output):
                    # Schedule the async message sending
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(manager.send_message(run_id, {
                        "type": "agent-update",
                        "message": f"✅ Agent '{agent_role}' completed: {task_desc[:50]}...",
                        "agent_id": agent_id,
                        "task_id": task_id,
                        "agent_status": "completed",
                        "task_status": "completed"
                    }))
                    loop.close()
                return callback

            task = Task(
                description=task_spec.get("description", ""),
                expected_output=task_spec.get("expected_output", "Task completion"),
                agent=task_agent,
                callback=create_completion_callback(agent.role, task_spec.get("description", ""), task_idx, filtered_agent_id, run_id, manager)
            )

            tasks.append(task)

            await manager.send_message(run_id, {
                "type": "agent-update",
                "message": f"📝 Task created: {task.description[:50]}... (Agent: {agent.role})",
                "task_id": task_idx,
                "agent_id": filtered_agent_id
            })
    
    # Create and return the crew
    crew = Crew(
        agents=agents,
        tasks=tasks,
        verbose=True
    )
    
    return crew