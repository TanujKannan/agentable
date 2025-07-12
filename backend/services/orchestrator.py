import asyncio
import json
from typing import Dict, Any
from agents.spec_agent import SpecAgent
from crewai import Crew, Agent, Task

async def runCrew(prompt: str, run_id: str, manager):
    """
    Main orchestrator function that:
    1. Uses SpecAgent to convert prompt to crew task JSON
    2. Creates CrewAI agents and tasks from the JSON
    3. Executes the crew and broadcasts events via WebSocket
    """
    try:
        # Step 1: Use SpecAgent to convert prompt to crew spec
        await manager.send_message(run_id, {
            "type": "agent-update",
            "agent": "SpecAgent",
            "status": "running"
        })
        
        spec_agent = SpecAgent()
        crew_spec = await spec_agent.generate_crew_spec(prompt)
        
        await manager.send_message(run_id, {
            "type": "log",
            "message": f"Generated crew specification with {len(crew_spec.get('tasks', []))} tasks"
        })
        
        await manager.send_message(run_id, {
            "type": "agent-update", 
            "agent": "SpecAgent",
            "status": "done"
        })
        
        # Step 2: Create and execute CrewAI crew from the spec
        crew = await create_crew_from_spec(crew_spec, run_id, manager)
        
        # Step 3: Execute the crew
        await manager.send_message(run_id, {
            "type": "log",
            "message": "Starting crew execution..."
        })
        
        result = crew.kickoff()
        
        # Step 4: Send completion event
        await manager.send_message(run_id, {
            "type": "complete",
            "outputRef": str(result),
            "result": result
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
    
    # Create agents based on the spec
    for task_spec in crew_spec.get("tasks", []):
        agent_name = task_spec.get("agent")
        
        # Create agent if not already created
        if not any(agent.role == agent_name for agent in agents):
            agent = Agent(
                role=agent_name,
                goal=task_spec.get("description", f"Execute {agent_name} tasks"),
                backstory=f"You are a specialized {agent_name} focused on {task_spec.get('description', 'task execution')}",
                verbose=True
            )
            agents.append(agent)
            
            await manager.send_message(run_id, {
                "type": "agent-update",
                "agent": agent_name,
                "status": "pending"
            })
    
    # Create tasks based on the spec
    for task_spec in crew_spec.get("tasks", []):
        agent_name = task_spec.get("agent")
        agent = next((a for a in agents if a.role == agent_name), None)
        
        if agent:
            task = Task(
                description=task_spec.get("description", ""),
                expected_output=task_spec.get("expected_output", "Task completion"),
                agent=agent
            )
            tasks.append(task)
    
    # Create and return the crew
    crew = Crew(
        agents=agents,
        tasks=tasks,
        verbose=True
    )
    
    return crew