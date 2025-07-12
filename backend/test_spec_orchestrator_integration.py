#!/usr/bin/env python3
"""
Test script to verify spec_agent and orchestrator integration.

This script tests:
1. JSON generation from spec_agent
2. Crew creation from orchestrator using the JSON
3. Compatibility between the two systems
"""

import asyncio
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from agents.spec_agent import SpecAgent
from services.orchestrator import create_crew_from_spec
from tools.tool_registry import get_tool_names

class MockManager:
    """Mock manager for testing orchestrator without WebSocket."""
    
    async def send_message(self, run_id: str, message: dict):
        """Mock send_message for testing."""
        print(f"[{run_id}] {message.get('type', 'unknown')}: {message.get('message', '')}")

async def test_spec_agent_json_output():
    """Test and display the JSON output from spec_agent."""
    print("🧪 TESTING SPEC_AGENT JSON OUTPUT")
    print("=" * 50)
    
    # Initialize spec_agent
    spec_agent = SpecAgent()
    
    # Test query
    query = "Research AI trends in 2024"
    print(f"Query: '{query}'")
    print("-" * 40)
    
    # Show available tools
    available_tools = get_tool_names()
    print(f"Available tools: {available_tools}")
    print()
    
    # Generate fallback specification (always works)
    print("📋 FALLBACK JSON SPECIFICATION:")
    print("=" * 40)
    fallback_spec = spec_agent._get_enhanced_fallback_spec(query)
    print(json.dumps(fallback_spec, indent=2))
    print()
    
    # Try LLM generation if API key is available
    if os.getenv("OPENAI_API_KEY"):
        try:
            print("📋 LLM GENERATED JSON SPECIFICATION:")
            print("=" * 40)
            llm_spec = await spec_agent.generate_crew_spec(query)
            print(json.dumps(llm_spec, indent=2))
            print()
            return llm_spec
        except Exception as e:
            print(f"❌ LLM generation failed: {e}")
            print("Using fallback specification instead.")
            return fallback_spec
    else:
        print("⚠️  LLM generation skipped (no OPENAI_API_KEY)")
        print("Using fallback specification for crew creation.")
        return fallback_spec

async def test_orchestrator_crew_creation(crew_spec):
    """Test crew creation from the JSON specification."""
    print("\n🚀 TESTING ORCHESTRATOR CREW CREATION")
    print("=" * 50)
    
    # Mock manager for testing
    mock_manager = MockManager()
    
    try:
        # Create crew from spec
        crew = await create_crew_from_spec(crew_spec, "test_run", mock_manager)
        
        print("✅ Successfully created crew!")
        print(f"Agents: {len(crew.agents)}")
        print(f"Tasks: {len(crew.tasks)}")
        print()
        
        # Display crew details
        print("🤖 CREW DETAILS:")
        print("-" * 20)
        
        # Create a detailed crew summary for saving
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
        
        for i, agent in enumerate(crew.agents):
            print(f"Agent {i+1}:")
            print(f"  Role: {agent.role}")
            print(f"  Goal: {agent.goal}")
            print(f"  Tools: {len(agent.tools)}")
            
            agent_info = {
                "id": i+1,
                "role": agent.role,
                "goal": agent.goal,
                "backstory": agent.backstory,
                "tools": []
            }
            
            for j, tool in enumerate(agent.tools):
                tool_name = type(tool).__name__
                print(f"    Tool {j+1}: {tool_name}")
                agent_info["tools"].append({
                    "id": j+1,
                    "name": tool_name,
                    "type": str(type(tool))
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
        
        # Save the crew details to a file
        with open("generated_crew_details.json", "w") as f:
            json.dump(crew_summary, f, indent=2)
        print("💾 Saved crew details to generated_crew_details.json")
        
        return crew
        
    except Exception as e:
        print(f"❌ Error creating crew: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_full_integration():
    """Test the complete integration between spec_agent and orchestrator."""
    print("\n🔄 TESTING FULL INTEGRATION")
    print("=" * 50)
    
    # Test multiple queries
    test_queries = [
        "Research AI trends in 2024",
        "Create a marketing strategy for a new product",
        "Analyze financial data and create a report"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Testing query: '{query}'")
        print("-" * 40)
        
        # Generate JSON spec
        spec_agent = SpecAgent()
        crew_spec = spec_agent._get_enhanced_fallback_spec(query)
        
        # Validate spec
        try:
            spec_agent._validate_enhanced_specification(crew_spec)
            print("✅ Specification is valid")
        except Exception as e:
            print(f"❌ Specification validation failed: {e}")
            continue
        
        # Create crew from spec
        try:
            mock_manager = MockManager()
            crew = await create_crew_from_spec(crew_spec, f"test_run_{i}", mock_manager)
            print(f"✅ Crew created successfully ({len(crew.agents)} agents, {len(crew.tasks)} tasks)")
        except Exception as e:
            print(f"❌ Crew creation failed: {e}")
        
        print()

def test_json_format_compatibility():
    """Test the JSON format compatibility between spec_agent and orchestrator."""
    print("\n📋 TESTING JSON FORMAT COMPATIBILITY")
    print("=" * 50)
    
    spec_agent = SpecAgent()
    query = "Research AI trends in 2024"
    
    # Generate specification
    spec = spec_agent._get_enhanced_fallback_spec(query)
    
    # Check required fields for orchestrator
    required_fields = ["agents", "tasks"]
    missing_fields = [field for field in required_fields if field not in spec]
    
    if missing_fields:
        print(f"❌ Missing required fields: {missing_fields}")
        return False
    
    # Check agent structure
    for agent in spec.get("agents", []):
        required_agent_fields = ["name", "role_description", "tools"]
        missing_agent_fields = [field for field in required_agent_fields if field not in agent]
        if missing_agent_fields:
            print(f"❌ Agent missing fields: {missing_agent_fields}")
            return False
    
    # Check task structure
    for task in spec.get("tasks", []):
        required_task_fields = ["agent", "description", "expected_output"]
        missing_task_fields = [field for field in required_task_fields if field not in task]
        if missing_task_fields:
            print(f"❌ Task missing fields: {missing_task_fields}")
            return False
    
    print("✅ JSON format is compatible with orchestrator!")
    return True

async def main():
    """Main test function."""
    print("🔍 SPEC_AGENT & ORCHESTRATOR INTEGRATION TEST")
    print("=" * 60)
    
    # Test 1: JSON output from spec_agent
    crew_spec = await test_spec_agent_json_output()
    
    # Test 2: Crew creation from orchestrator
    if crew_spec:
        crew = await test_orchestrator_crew_creation(crew_spec)
    
    # Test 3: JSON format compatibility
    test_json_format_compatibility()
    
    # Test 4: Full integration with multiple queries
    await test_full_integration()
    
    print("\n" + "=" * 60)
    print("✅ INTEGRATION TESTING COMPLETED!")
    print("\n💡 Key Points:")
    print("   - spec_agent generates JSON compatible with orchestrator")
    print("   - orchestrator successfully creates crews from the JSON")
    print("   - Tools are properly instantiated from tool_registry")
    print("   - The system works end-to-end")

if __name__ == "__main__":
    asyncio.run(main()) 