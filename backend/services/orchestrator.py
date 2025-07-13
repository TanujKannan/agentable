import asyncio
import json
from typing import Dict, Any
from agents.spec_agent import SpecAgent
from crewai import Crew, Agent, Task, Process

from tools.tool_registry import instantiate_tool

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
        
        # Step 2: Analyze workflow for parallelization opportunities
        workflow_info = crew_spec.get("workflow", {})
        has_parallel_tasks = any(task.get("dependsOn", []) == [] for task in crew_spec.get("tasks", []))
        
        if has_parallel_tasks or workflow_info:
            await manager.send_message(run_id, {
                "type": "log",
                "message": "Detected parallel workflow - using advanced execution engine"
            })
            
            # Use parallel workflow execution
            results = await execute_parallel_workflow(crew_spec, run_id, manager)
            result = results
        else:
            await manager.send_message(run_id, {
                "type": "log",
                "message": "Using standard sequential execution"
            })
            
            # Use standard crew execution
            crew = await create_crew_from_spec(crew_spec, run_id, manager)
            
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
            context_data = []
            if task_spec.get("params"):
                # Add params as context information
                context_data.append(f"Task parameters: {task_spec.get('params')}")
            
            task = Task(
                description=task_spec.get("description", ""),
                expected_output=task_spec.get("expected_output", "Task completion"),
                agent=agent,
                context=context_data,
                config={}  # Add empty config to prevent the error
            )

            tasks.append(task)
            
            # Track dependencies for parallelization
            depends_on = task_spec.get("dependsOn", [])
            task_dependencies[task_id] = depends_on
            
            if not depends_on:
                parallel_tasks.append(task_id)
            else:
                sequential_tasks.append(task_id)

            await manager.send_message(run_id, {
                "type": "agent-update",
                "message": f"Task created: {task.description[:50]}... (Priority: {task_spec.get('priority', 'medium')})"
            })
    
    # Analyze workflow for parallelization opportunities
    workflow_info = crew_spec.get("workflow", {})
    if workflow_info:
        await manager.send_message(run_id, {
            "type": "log",
            "message": f"Workflow detected: {len(parallel_tasks)} parallel tasks, {len(sequential_tasks)} sequential tasks"
        })
    
    # Create and return the crew with enhanced configuration
    crew = Crew(
        agents=agents,
        tasks=tasks,
        verbose=True,
        process=Process.sequential  # Can be changed to Process.hierarchical for more complex workflows
    )
    
    return crew

async def execute_parallel_workflow(crew_spec: Dict[str, Any], run_id: str, manager):
    """
    Advanced workflow execution that supports parallel task execution
    """
    # Create agents and tasks
    agents = []
    tasks_by_id = {}
    
    # Create agents
    for agent_spec in crew_spec.get("agents", []):
        agent_tools = [instantiate_tool(tool_name) for tool_name in agent_spec.get("tools", [])]
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
    
    print('after agent spec', agents)
    
    # Create tasks and build dependency graph
    for task_spec in crew_spec.get("tasks", []):
        print('here 1')
        agent_name = task_spec.get("agent")

        print('here 2')

        task_id = task_spec.get("id")

        print('here 3')
        
        agent = next((a for a in agents if a.role == agent_name), None)
        if agent:
            # Convert params to context format expected by CrewAI
            context_data = []

            print('here 4')

            if task_spec.get("params"):
                # Add params as context information
                print('here 5')
                context_data.append(f"Task parameters: {task_spec.get('params')}")

            
            print('here 6')

            print(task_spec.get("description"))
            print(task_spec.get("expected_output"))
            
            task = Task(
                description=task_spec.get("description", ""),
                expected_output=task_spec.get("expected_output", "Task completion"),
                agent=agent,
                context=context_data,
                config={}
            )

            print('here 7')
        
            tasks_by_id[task_id] = {
                "task": task,
                "spec": task_spec,
                "dependencies": task_spec.get("dependsOn", []),
                "completed": False,
                "result": None
            }

            print('here 8')
    
    print('after task spec')
    
    # Execute tasks in parallel where possible
    completed_tasks = set()
    running_tasks = set()

    print('before while loop')
    
    while len(completed_tasks) < len(tasks_by_id):
        # Find tasks that can run (all dependencies completed)
        ready_tasks = []
        for task_id, task_info in tasks_by_id.items():
            if (task_id not in completed_tasks and 
                task_id not in running_tasks and
                all(dep in completed_tasks for dep in task_info["dependencies"])):
                ready_tasks.append(task_id)
        
        if not ready_tasks and not running_tasks:
            # Deadlock or circular dependency
            await manager.send_message(run_id, {
                "type": "error",
                "message": "Circular dependency detected in task workflow"
            })
            break
        
        # Execute ready tasks in parallel
        if ready_tasks:
            await manager.send_message(run_id, {
                "type": "log",
                "message": f"Starting {len(ready_tasks)} tasks in parallel: {', '.join(ready_tasks)}"
            })
            
            # Execute tasks concurrently
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(ready_tasks)) as executor:
                futures = {}
                for task_id in ready_tasks:
                    task_info = tasks_by_id[task_id]
                    future = executor.submit(task_info["task"].execute_sync)
                    futures[future] = task_id
                    running_tasks.add(task_id)
                
                # Wait for completion
                for future in concurrent.futures.as_completed(futures):
                    task_id = futures[future]
                    try:
                        result = future.result()
                        tasks_by_id[task_id]["result"] = result
                        tasks_by_id[task_id]["completed"] = True
                        completed_tasks.add(task_id)
                        running_tasks.remove(task_id)
                        
                        await manager.send_message(run_id, {
                            "type": "agent-update",
                            "message": f"Task {task_id} completed successfully"
                        })
                    except Exception as e:
                        await manager.send_message(run_id, {
                            "type": "error",
                            "message": f"Task {task_id} failed: {str(e)}"
                        })
                        running_tasks.remove(task_id)
        
        # Wait a bit before checking for more ready tasks
        await asyncio.sleep(1)
    
    # Aggregate results
    results = []
    for task_id, task_info in tasks_by_id.items():
        if task_info["completed"]:
            results.append({
                "task_id": task_id,
                "result": task_info["result"]
            })
    
    return results