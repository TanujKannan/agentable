import asyncio
import json
from typing import Dict, Any
from agents.spec_agent import SpecAgent
from crewai import Crew, Agent, Task

from tools.tool_registry import instantiate_tool
from tools.parameterized_tool import create_parameterized_tool

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
        for agent in crew.agents:
            await manager.send_message(run_id, {
                "type": "agent-update",
                "message": f"Agent {agent.role} is ready"
            })
        
        # Execute crew in thread pool to avoid blocking
        import concurrent.futures
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Send periodic updates during execution
            await manager.send_message(run_id, {
                "type": "log", 
                "message": "Crew is working on your task..."
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
        await manager.send_message(run_id, {
            "type": "complete",
            "message": "Crew execution completed successfully!",
            "result": str(result)
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
        agent_tools = []
        agent_tools = [instantiate_tool(tool_name) for tool_name in agent_spec.get("tools", [])]
    
        agent = Agent(
            role=agent_spec.get("name"),
            goal=agent_spec.get("role_description"),
            backstory=agent_spec.get("role_description"),
            tools=agent_tools,
            verbose=True
        )
        agents.append(agent)

    # Create tasks based on the spec
    for task_spec in crew_spec.get("tasks", []):
        agent_name = task_spec.get("agent")
        agent = next((a for a in agents if a.role == agent_name), None)

        if agent:
            # Get tool parameters for this task
            tool_params = task_spec.get("tool_params", [])
            
            # Create parameterized tools for this specific task
            task_specific_tools = []
            for param_set in tool_params:
                tool_name = param_set.get("tool")
                if tool_name:
                    # Remove the "tool" key and use the rest as parameters
                    tool_kwargs = {k: v for k, v in param_set.items() if k != "tool"}
                    
                    # Always create a parameterized version of the tool
                    parameterized_tool = create_parameterized_tool(tool_name, tool_kwargs)
                    task_specific_tools.append(parameterized_tool)
            
            # Create a task-specific agent with the parameterized tools
            task_agent = Agent(
                role=agent.role,
                goal=agent.goal,
                backstory=agent.backstory,
                tools=task_specific_tools,  # Use the parameterized tools
                verbose=True
            )

            task = Task(
                description=task_spec.get("description", ""),
                expected_output=task_spec.get("expected_output", "Task completion"),
                agent=task_agent
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