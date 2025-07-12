#!/usr/bin/env python3
"""
Crew File Generator - Converts JSON specifications into runnable Python crew files.

This module takes the JSON specification from spec_agent and generates a complete
Python file that can be run directly with kickoff(), similar to the original crew.py.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

def generate_crew_file(crew_spec: Dict[str, Any], output_filename: str = "generated_crew.py") -> str:
    """
    Generate a complete Python crew file from the JSON specification.
    
    Args:
        crew_spec: The JSON specification from spec_agent
        output_filename: Name of the output Python file
        
    Returns:
        The path to the generated file
    """
    
    # Generate the Python code
    python_code = _generate_crew_python_code(crew_spec)
    
    # Write to file
    output_path = Path(output_filename)
    with open(output_path, 'w') as f:
        f.write(python_code)
    
    return str(output_path)

def _generate_crew_python_code(crew_spec: Dict[str, Any]) -> str:
    """Generate the complete Python code for the crew file."""
    
    # Extract agents and tasks
    agents = crew_spec.get("agents", [])
    tasks = crew_spec.get("tasks", [])
    
    # Start building the Python code
    code_parts = []
    
    # File header
    code_parts.append(_generate_file_header())
    
    # Imports
    code_parts.append(_generate_imports())
    
    # Class definition
    code_parts.append(_generate_class_definition())
    
    # Agent methods
    for agent in agents:
        code_parts.append(_generate_agent_method(agent))
    
    # Task methods
    for task in tasks:
        code_parts.append(_generate_task_method(task))
    
    # Crew method
    code_parts.append(_generate_crew_method(agents, tasks))
    
    # Main execution
    code_parts.append(_generate_main_method())
    
    return "\n".join(code_parts)

def _generate_file_header() -> str:
    """Generate the file header with timestamp and description."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f'''#!/usr/bin/env python3
"""
Generated Crew File - Created on {timestamp}

This file was automatically generated from a JSON specification.
It contains all the agents, tasks, and crew configuration needed to run the crew.

Usage:
    python generated_crew.py
"""

'''

def _generate_imports() -> str:
    """Generate the import statements."""
    return '''from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Tool imports
from tools.tool_registry import instantiate_tool

'''

def _generate_class_definition() -> str:
    """Generate the class definition."""
    return '''@CrewBase
class GeneratedCrew:
    """Generated crew from JSON specification"""

'''

def _generate_agent_method(agent_spec: Dict[str, Any]) -> str:
    """Generate an agent method."""
    agent_name = agent_spec.get("name", "unknown_agent")
    role_description = agent_spec.get("role_description", "Agent role")
    tools = agent_spec.get("tools", [])
    
    # Clean up the role_description - remove newlines and extra spaces
    role_description = role_description.replace('\n', ' ').strip()
    
    # Split role_description into role and goal
    parts = role_description.split(" - ", 1)
    if len(parts) == 2:
        role = parts[0].strip()
        goal = parts[1].strip()
    else:
        role = role_description
        goal = role_description
    
    # Escape quotes in strings
    role = role.replace('"', '\\"')
    goal = goal.replace('"', '\\"')
    backstory = role_description.replace('"', '\\"')
    
    # Generate tool instantiation code
    if tools:
        tool_lines = []
        for tool in tools:
            tool_lines.append(f'            instantiate_tool("{tool}"),')
        tools_code = f'''
        tools = [
{chr(10).join(tool_lines)}
        ]'''
    else:
        tools_code = "        tools = []"
    
    return f'''    @agent
    def {agent_name}(self) -> Agent:
        """Generated agent: {agent_name}"""
{tools_code}
        
        return Agent(
            role="{role}",
            goal="{goal}",
            backstory="{backstory}",
            tools=tools,
            verbose=True
        )

'''

def _generate_task_method(task_spec: Dict[str, Any]) -> str:
    """Generate a task method."""
    # Create a task ID/name from the agent name
    agent_name = task_spec.get("agent", "unknown_agent")
    task_name = f"{agent_name}_task"
    
    description = task_spec.get("description", "Task description")
    expected_output = task_spec.get("expected_output", "Task completion")
    
    # Clean up strings - remove newlines and normalize whitespace
    description = ' '.join(description.split())
    expected_output = ' '.join(expected_output.split())
    
    # Escape quotes in strings
    description = description.replace('"', '\\"')
    expected_output = expected_output.replace('"', '\\"')
    
    return f'''    @task
    def {task_name}(self) -> Task:
        """Generated task for {agent_name}"""
        return Task(
            description="{description}",
            expected_output="{expected_output}",
            agent=self.{agent_name}(),
        )

'''

def _generate_crew_method(agents: list, tasks: list) -> str:
    """Generate the crew method."""
    return '''    @crew
    def crew(self) -> Crew:
        """Creates the generated crew"""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,    # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )

'''

def _generate_main_method() -> str:
    """Generate the main execution method."""
    return '''if __name__ == "__main__":
    # Initialize the crew
    crew_instance = GeneratedCrew()
    crew = crew_instance.crew()
    
    print("🚀 Starting Generated Crew...")
    print("=" * 50)
    
    # Show crew info
    print(f"Agents: {len(crew.agents)}")
    print(f"Tasks: {len(crew.tasks)}")
    print()
    
    # Execute the crew
    try:
        result = crew.kickoff()
        print("✅ Crew execution completed!")
        print("=" * 50)
        print("RESULT:")
        print(result)
    except Exception as e:
        print(f"❌ Error executing crew: {e}")
        import traceback
        traceback.print_exc()
'''

def create_crew_file_from_spec_agent(query: str, output_filename: str = "generated_crew.py") -> str:
    """
    Complete workflow: Generate JSON from spec_agent and create a runnable crew file.
    
    Args:
        query: The user query to generate crew for
        output_filename: Name of the output Python file
        
    Returns:
        The path to the generated crew file
    """
    from agents.spec_agent import SpecAgent
    
    # Generate JSON specification
    spec_agent = SpecAgent()
    crew_spec = spec_agent._get_enhanced_fallback_spec(query)
    
    # Save JSON specification for reference
    json_filename = output_filename.replace(".py", "_spec.json")
    with open(json_filename, 'w') as f:
        json.dump(crew_spec, f, indent=2)
    
    # Generate Python crew file
    crew_file_path = generate_crew_file(crew_spec, output_filename)
    
    return crew_file_path

# Test function
def test_crew_file_generation():
    """Test the crew file generation."""
    print("🔧 TESTING CREW FILE GENERATION")
    print("=" * 50)
    
    # Test query
    query = "Research AI trends in 2024"
    print(f"Query: '{query}'")
    print("-" * 40)
    
    # Generate crew file
    crew_file_path = create_crew_file_from_spec_agent(query, "test_generated_crew.py")
    
    print(f"✅ Generated crew file: {crew_file_path}")
    print(f"✅ Generated spec file: test_generated_crew_spec.json")
    print()
    
    # Show file contents preview
    print("📄 GENERATED CREW FILE PREVIEW:")
    print("=" * 40)
    with open(crew_file_path, 'r') as f:
        lines = f.readlines()
        for i, line in enumerate(lines[:30]):  # Show first 30 lines
            print(f"{i+1:2d}: {line.rstrip()}")
        if len(lines) > 30:
            print(f"... and {len(lines) - 30} more lines")
    
    print("\n" + "=" * 50)
    print("✅ CREW FILE GENERATION TEST COMPLETED!")
    print(f"\n🚀 To run the generated crew:")
    print(f"   cd backend && python {crew_file_path}")

if __name__ == "__main__":
    test_crew_file_generation() 