#!/usr/bin/env python3
"""
Crew Generator Module

This module provides simple functions to generate complete CrewAI crews
from user prompts, combining specification generation and crew building.
"""

import asyncio
import yaml
from typing import Dict, Any, List
from pathlib import Path
from crewai import Crew, Agent, Task

from agents.spec_agent import SpecAgent
from tools.tool_registry import instantiate_tool

async def generate_crew(prompt: str, 
                       agents_config_path: str = "agents/config/agents.yaml",
                       tasks_config_path: str = "agents/config/tasks.yaml") -> Crew:
    """
    Generate a complete CrewAI crew from a user prompt.
    
    This function:
    1. Uses SpecAgent to convert the prompt into a specification
    2. Creates agents (predefined + custom) from the specification  
    3. Creates tasks with proper dependencies
    4. Returns a ready-to-execute Crew object
    
    Args:
        prompt: User's request/query
        agents_config_path: Path to predefined agents config
        tasks_config_path: Path to predefined tasks config
        
    Returns:
        Crew object ready for execution
        
    Example:
        crew = await generate_crew("Research AI trends and create a report")
        result = crew.kickoff()
    """
    # Step 1: Generate specification using SpecAgent
    spec_agent = SpecAgent(agents_config_path, tasks_config_path)
    crew_spec = await spec_agent.generate_crew_spec(prompt)
    
    # Step 2: Build crew from specification
    crew = await build_crew_from_specification(crew_spec, agents_config_path)
    
    return crew

def generate_crew_sync(prompt: str,
                      agents_config_path: str = "agents/config/agents.yaml", 
                      tasks_config_path: str = "agents/config/tasks.yaml") -> Crew:
    """
    Synchronous version of generate_crew.
    
    Args:
        prompt: User's request/query
        agents_config_path: Path to predefined agents config
        tasks_config_path: Path to predefined tasks config
        
    Returns:
        Crew object ready for execution
        
    Example:
        crew = generate_crew_sync("Research AI trends and create a report")
        result = crew.kickoff()
    """
    return asyncio.run(generate_crew(prompt, agents_config_path, tasks_config_path))

async def build_crew_from_specification(crew_spec: Dict[str, Any], 
                                       agents_config_path: str = "agents/config/agents.yaml") -> Crew:
    """
    Build a CrewAI crew from a specification.
    
    Args:
        crew_spec: The crew specification dictionary
        agents_config_path: Path to predefined agents config
        
    Returns:
        Crew object ready for execution
    """
    # Load predefined agents configuration
    predefined_agents = _load_predefined_agents(agents_config_path)
    
    # Create agents
    agents = []
    agent_map = {}
    
    for agent_spec in crew_spec.get("agents", []):
        agent_name = agent_spec.get("name")
        agent_source = agent_spec.get("source", "custom")
        
        # Create agent based on source type
        if agent_source == "predefined":
            agent = _create_predefined_agent(agent_spec, predefined_agents)
        else:
            agent = _create_custom_agent(agent_spec)
        
        agents.append(agent)
        agent_map[agent_name] = agent
    
    # Create tasks with dependency handling
    tasks = []
    task_map = {}
    
    # First pass: create tasks without dependencies
    for task_spec in crew_spec.get("tasks", []):
        if not task_spec.get("dependencies"):
            task = _create_task_from_spec(task_spec, agent_map, task_map)
            tasks.append(task)
            task_map[task_spec.get("name", task_spec.get("id"))] = task
    
    # Second pass: create tasks with dependencies
    remaining_tasks = [t for t in crew_spec.get("tasks", []) if t.get("dependencies")]
    max_iterations = len(remaining_tasks) + 1
    iteration = 0
    
    while remaining_tasks and iteration < max_iterations:
        iteration += 1
        created_in_iteration = []
        
        for task_spec in remaining_tasks:
            # Check if all dependencies are satisfied
            all_deps_satisfied = all(
                dep_name in task_map 
                for dep_name in task_spec.get("dependencies", [])
            )
            
            if all_deps_satisfied:
                task = _create_task_from_spec(task_spec, agent_map, task_map)
                tasks.append(task)
                task_map[task_spec.get("name", task_spec.get("id"))] = task
                created_in_iteration.append(task_spec)
        
        # Remove created tasks from remaining_tasks
        for created_task in created_in_iteration:
            remaining_tasks.remove(created_task)
    
    # Check if there are any remaining tasks (circular dependencies)
    if remaining_tasks:
        remaining_names = [t.get("name", t.get("id")) for t in remaining_tasks]
        raise ValueError(f"Circular dependencies detected for tasks: {remaining_names}")
    
    # Get crew configuration
    crew_config = crew_spec.get("crew_config", {})
    verbose = crew_config.get("verbose", True)
    
    # Create and return the crew
    crew = Crew(
        agents=agents,
        tasks=tasks,
        verbose=verbose
    )
    
    return crew

def _create_predefined_agent(agent_spec: Dict[str, Any], predefined_agents: Dict[str, Any]) -> Agent:
    """Create an agent from predefined configuration."""
    config_key = agent_spec.get("config_key")
    
    if config_key not in predefined_agents:
        raise ValueError(f"Predefined agent '{config_key}' not found")
    
    predefined_config = predefined_agents[config_key]
    
    # Get tools for the agent
    tools = _get_agent_tools(agent_spec.get("tools", []))
    
    return Agent(
        role=predefined_config.get("role", ""),
        goal=predefined_config.get("goal", ""),
        backstory=predefined_config.get("backstory", ""),
        tools=tools,
        verbose=True
    )

def _create_custom_agent(agent_spec: Dict[str, Any]) -> Agent:
    """Create a custom agent from specification."""
    # Get tools for the agent
    tools = _get_agent_tools(agent_spec.get("tools", []))
    
    return Agent(
        role=agent_spec.get("role", ""),
        goal=agent_spec.get("goal", ""),
        backstory=agent_spec.get("backstory", ""),
        tools=tools,
        verbose=True
    )

def _create_task_from_spec(task_spec: Dict[str, Any], 
                          agent_map: Dict[str, Agent],
                          task_map: Dict[str, Task]) -> Task:
    """Create a task from specification."""
    task_name = task_spec.get("name", task_spec.get("id"))
    assigned_agent_name = task_spec.get("assigned_agent", task_spec.get("agent"))
    
    if assigned_agent_name not in agent_map:
        raise ValueError(f"Agent '{assigned_agent_name}' not found for task '{task_name}'")
    
    assigned_agent = agent_map[assigned_agent_name]
    
    # Handle task dependencies
    dependencies = []
    for dep_name in task_spec.get("dependencies", []):
        if dep_name in task_map:
            dependencies.append(task_map[dep_name])
    
    # Create task parameters
    task_params = {
        "description": task_spec.get("description", ""),
        "expected_output": task_spec.get("expected_output", "Task completion"),
        "agent": assigned_agent,
    }
    
    # Add optional parameters
    if task_spec.get("output_file"):
        task_params["output_file"] = task_spec.get("output_file")
    
    if dependencies:
        task_params["context"] = dependencies
    
    return Task(**task_params)

def _get_agent_tools(tool_names: List[str]) -> List:
    """Get instantiated tools for an agent."""
    tools = []
    for tool_name in tool_names:
        try:
            tool = instantiate_tool(tool_name)
            tools.append(tool)
        except Exception as e:
            print(f"Warning: Could not instantiate tool '{tool_name}': {e}")
    
    return tools

def _load_predefined_agents(agents_config_path: str) -> Dict[str, Any]:
    """Load predefined agents from YAML configuration."""
    try:
        config_path = Path(agents_config_path)
        if config_path.exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        return {}
    except Exception as e:
        print(f"Warning: Could not load agents config: {e}")
        return {}

# Convenience functions for quick testing
async def quick_research_crew(topic: str) -> Crew:
    """
    Quick function to create a research crew for a specific topic.
    
    Args:
        topic: The research topic
        
    Returns:
        Crew configured for research
    """
    prompt = f"Research {topic} and create a comprehensive report with analysis and insights"
    return await generate_crew(prompt)

async def quick_analysis_crew(data_description: str) -> Crew:
    """
    Quick function to create an analysis crew.
    
    Args:
        data_description: Description of what needs to be analyzed
        
    Returns:
        Crew configured for analysis
    """
    prompt = f"Analyze {data_description} and provide detailed insights and recommendations"
    return await generate_crew(prompt)

def quick_research_crew_sync(topic: str) -> Crew:
    """Synchronous version of quick_research_crew."""
    return asyncio.run(quick_research_crew(topic))

def quick_analysis_crew_sync(data_description: str) -> Crew:
    """Synchronous version of quick_analysis_crew."""
    return asyncio.run(quick_analysis_crew(data_description)) 