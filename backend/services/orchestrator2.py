import asyncio
import json
from typing import Dict, Any
from agents.spec_agent import SpecAgent
from crewai import Crew, Agent, Task, Process

from tools.tool_registry import instantiate_tool


async def runCrew(prompt: str, run_id: str, manager):
    try:
        # for websocket stuff
        max_wait = 10  # seconds
        wait_time = 0
        while run_id not in manager.active_connections and wait_time < max_wait:
            await asyncio.sleep(0.1)
            wait_time += 0.1
        
        if run_id not in manager.active_connections:
            raise Exception("WebSocket connection not established within timeout")
        
        # manager log
        await manager.send_message(run_id, {
            "type": "agent-update",
            "message": "SpecAgent started - converting prompt to crew specification"
        })

        # instantiate planner and get plan for agents
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

        # create agents from spec
        agents, tasks, task_dependencies, parallel_tasks, sequential_tasks = await read_spec(crew_spec, run_id, manager)

        if parallel_tasks:
            # execute more complicated workflow
            result = await parallel_execution(agents, tasks, task_dependencies, parallel_tasks, sequential_tasks, run_id, manager)
        else:
            # use standard crew execution
            crew = Crew(
                agents=agents,
                tasks=tasks,
                verbose=True,
                process=Process.sequential
            )
            result = crew.kickoff()
        
        return result

    except Exception as e:
        await manager.send_message(run_id, {
            "type": "error",
            "message": f"Error in crew execution: {str(e)}"
        })

async def read_spec(crew_spec: Dict[str, Any], run_id: str, manager):
    """
    Creates a CrewAI Crew object from the generated specification
    Now supports parallel execution, workflow optimization, and enhanced task configuration
    """
    agents = []
    tasks = []
    
    # Track task dependencies for parallelization
    task_dependencies = {}
    parallel_tasks = []
    sequential_tasks = []

    # Create agents based on spec
    for agent_spec in crew_spec.get("agents", []):
        agent_tools = [instantiate_tool(tool_name) for tool_name in agent_spec.get("tools", [])]
    
        # Enhanced agent configuration
        agent_config = agent_spec.get("config", {})
        agent = Agent(
            role=agent_spec.get("name"),
            goal=agent_spec.get("role_description"),
            backstory=agent_spec.get("role_description"),
            tools=agent_tools,
            verbose=True,
            allow_delegation=agent_config.get("allow_delegation", True),
            max_iter=agent_config.get("max_iterations", 3)
        )
        agents.append(agent)

        await manager.send_message(run_id, {
            "type": "agent-update",
            "message": f"Agent created: {agent.role} with {len(agent_tools)} tools"
        })

    # Create tasks and analyze dependencies
    for task_spec in crew_spec.get("tasks", []):
        agent_name = task_spec.get("agent")
        task_id = task_spec.get("id")
        
        agent = next((a for a in agents if a.role == agent_name), None)

        if agent:
            # Enhanced task creation with configuration
            # Convert params to context format expected by CrewAI

            # context_data = []
            # if task_spec.get("params"):
            #     # Add params as context information
            #     print(type(task_spec.get('params')))
            #     context_data.append(f"Task parameters: {task_spec.get('params')}")

            task_name = task_spec.get("name")

            task = Task(
                name=task_name,
                description=task_spec.get("description", ""),
                expected_output=task_spec.get("expected_output", "Task completion"),
                agent=agent,
                config={}  # Add empty config to prevent the error
            )
            
            # Set task ID for tracking
            # task.id = task_id

            tasks.append(task)
            
            # Track dependencies for parallelization
            depends_on = task_spec.get("dependsOn", [])
            task_dependencies[task_name] = depends_on
            
            # Check if task should run asynchronously
            is_async = task_spec.get("async_execution", False)
            
            if not depends_on and is_async:
                parallel_tasks.append(task_name)
            else:
                sequential_tasks.append(task_name)

            await manager.send_message(run_id, {
                "type": "agent-update",
                "message": f"Task created: {task.description[:50]}... (Priority: {task_spec.get('priority', 'medium')}, Async: {is_async})"
            })
    
    # Analyze workflow for parallelization opportunities
    workflow_info = crew_spec.get("workflow", {})
    if workflow_info:
        await manager.send_message(run_id, {
            "type": "log",
            "message": f"Workflow detected: {len(parallel_tasks)} parallel tasks, {len(sequential_tasks)} sequential tasks"
        })
    
    return agents, tasks, task_dependencies, parallel_tasks, sequential_tasks

async def parallel_execution(agents: list, tasks: list, task_dependencies, parallel_tasks, sequential_tasks, run_id: str, manager):
    """
    Executes tasks in parallel using asyncio.gather.
    Handles dependencies and sequential execution.
    """
    # Create a dictionary to hold task results
    task_results = {}
    
    # Create task mapping by ID
    task_by_id = {task.name: task for task in tasks}
    print(task_by_id)
    
    # Process parallel tasks first (no dependencies)
    if parallel_tasks:
        await manager.send_message(run_id, {
            "type": "log",
            "message": f"Executing {len(parallel_tasks)} parallel tasks"
        })
        
        # Execute parallel tasks concurrently
        parallel_task_coros = []
        for task_id in parallel_tasks:
            if task_id in task_by_id:
                task = task_by_id[task_id]
                coro = asyncio.to_thread(task.execute_sync)
                parallel_task_coros.append(coro)
        
        if parallel_task_coros:
            results = await asyncio.gather(*parallel_task_coros, return_exceptions=True)
            for i, task_id in enumerate(parallel_tasks):
                if isinstance(results[i], Exception):
                    task_results[task_id] = {"status": "failed", "error": str(results[i])}
                else:
                    task_results[task_id] = {"status": "success", "result": results[i]}
    
    # Process sequential tasks (with dependencies)
    for task_id in sequential_tasks:
        if task_id in task_by_id:
            task = task_by_id[task_id]
            
            # Check if dependencies are completed
            dependencies = task_dependencies.get(task_id, [])
            if all(dep in task_results and task_results[dep]["status"] == "success" for dep in dependencies):
                await manager.send_message(run_id, {
                    "type": "log",
                    "message": f"Executing sequential task: {task_id}"
                })
                
                try:
                    result = await asyncio.to_thread(task.execute_sync)
                    task_results[task_id] = {"status": "success", "result": result}
                except Exception as e:
                    task_results[task_id] = {"status": "failed", "error": str(e)}
            else:
                task_results[task_id] = {"status": "failed", "error": "Dependencies not met"}
    
    print(task_results)
    
    return task_results
