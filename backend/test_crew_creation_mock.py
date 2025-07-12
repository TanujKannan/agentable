#!/usr/bin/env python3
"""
Test script to show crew creation without actually instantiating tools.
This shows the crew structure that would be created from the JSON.
"""

import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from agents.spec_agent import SpecAgent
from tools.tool_registry import get_tool_names
from crewai import Crew, Agent, Task

class MockTool:
    """Mock tool class to represent tools without requiring API keys."""
    def __init__(self, name):
        self.name = name
        self.description = f"Mock {name} tool"
    
    def __repr__(self):
        return f"MockTool({self.name})"

def mock_instantiate_tool(tool_name: str, **kwargs):
    """Mock tool instantiation that doesn't require API keys."""
    return MockTool(tool_name)

def create_crew_from_spec_mock(crew_spec: dict) -> Crew:
    """
    Creates a CrewAI Crew object from the generated specification using mock tools.
    This mimics the orchestrator.py logic but without requiring API keys.
    """
    agents = []
    tasks = []

    # Create agents based on spec
    for agent_spec in crew_spec.get("agents", []):
        # Use mock tools instead of real ones
        agent_tools = [mock_instantiate_tool(tool_name) for tool_name in agent_spec.get("tools", [])]
    
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

def test_crew_creation():
    """Test crew creation from JSON specification."""
    print("🔍 CREW CREATION TEST (WITH MOCK TOOLS)")
    print("=" * 50)
    
    # Initialize spec_agent
    spec_agent = SpecAgent()
    
    # Test query
    query = "Research AI trends in 2024"
    print(f"Query: '{query}'")
    print(f"Available tools: {get_tool_names()}")
    print("-" * 40)
    
    # Generate specification
    crew_spec = spec_agent._get_enhanced_fallback_spec(query)
    
    print("📋 GENERATED JSON SPECIFICATION:")
    print("=" * 40)
    print(json.dumps(crew_spec, indent=2))
    
    # Save specification to file
    with open("crew_spec.json", "w") as f:
        json.dump(crew_spec, f, indent=2)
    print("💾 Saved specification to crew_spec.json")
    print()
    
    # Create crew from specification
    print("🤖 CREATING CREW FROM SPECIFICATION:")
    print("=" * 40)
    
    crew = create_crew_from_spec_mock(crew_spec)
    
    print("✅ Successfully created crew!")
    print(f"Agents: {len(crew.agents)}")
    print(f"Tasks: {len(crew.tasks)}")
    print()
    
    # Create detailed crew summary
    crew_summary = {
        "crew_info": {
            "agents_count": len(crew.agents),
            "tasks_count": len(crew.tasks),
            "process": str(crew.process),
            "verbose": crew.verbose
        },
        "agents": [],
        "tasks": []
    }
    
    print("🤖 CREW DETAILS:")
    print("-" * 20)
    
    for i, agent in enumerate(crew.agents):
        print(f"Agent {i+1}:")
        print(f"  Role: {agent.role}")
        print(f"  Goal: {agent.goal}")
        print(f"  Backstory: {agent.backstory[:100]}...")
        print(f"  Tools: {len(agent.tools)}")
        
        agent_info = {
            "id": i+1,
            "role": agent.role,
            "goal": agent.goal,
            "backstory": agent.backstory,
            "tools": []
        }
        
        for j, tool in enumerate(agent.tools):
            tool_name = tool.name
            print(f"    Tool {j+1}: {tool_name} (Mock)")
            agent_info["tools"].append({
                "id": j+1,
                "name": tool_name,
                "type": "MockTool",
                "description": tool.description
            })
        
        crew_summary["agents"].append(agent_info)
        print()
    
    for i, task in enumerate(crew.tasks):
        print(f"Task {i+1}:")
        print(f"  Description: {task.description[:100]}...")
        print(f"  Expected Output: {task.expected_output[:100]}...")
        print(f"  Assigned Agent: {task.agent.role}")
        
        task_info = {
            "id": i+1,
            "description": task.description,
            "expected_output": task.expected_output,
            "assigned_agent": task.agent.role,
            "agent_goal": task.agent.goal
        }
        
        crew_summary["tasks"].append(task_info)
        print()
    
    # Save crew details to file
    with open("created_crew_details.json", "w") as f:
        json.dump(crew_summary, f, indent=2)
    print("💾 Saved crew details to created_crew_details.json")
    
    print("\n" + "=" * 50)
    print("✅ CREW CREATION TEST COMPLETED!")
    print("\n📄 Generated Files:")
    print("   - crew_spec.json (JSON specification)")
    print("   - created_crew_details.json (Created crew details)")
    print("\n🔍 This shows exactly how orchestrator.py would create the crew!")
    
    return crew

if __name__ == "__main__":
    test_crew_creation() 