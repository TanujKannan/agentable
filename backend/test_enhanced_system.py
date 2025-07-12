#!/usr/bin/env python3
"""
Test script for the enhanced SpecAgent system.

This script verifies that:
1. SpecAgent can load predefined agents and tasks
2. Tool registry is working
3. Enhanced prompt generation works
4. JSON specification generation works
"""

import asyncio
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from agents.spec_agent import SpecAgent
from tools.tool_registry import get_tool_names, get_tool_info

async def test_enhanced_spec_agent():
    """Test the enhanced SpecAgent functionality."""
    print("🧪 Testing Enhanced SpecAgent System")
    print("=" * 50)
    
    # Check if OpenAI API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not set. Set it to test LLM functionality.")
        print("   export OPENAI_API_KEY='your-key-here'")
        print()
    
    # Initialize the enhanced SpecAgent
    print("1. Initializing enhanced SpecAgent...")
    spec_agent = SpecAgent()
    
    # Test predefined agents loading
    print("2. Testing predefined agents loading...")
    available_agents = spec_agent.get_available_agents()
    print(f"   Available predefined agents: {available_agents}")
    
    # Test tools registry
    print("3. Testing tools registry...")
    available_tools = spec_agent.get_available_tools()
    print(f"   Available tools: {available_tools}")
    
    # Get tool information
    tool_info = get_tool_info()
    print("   Tool details:")
    for tool_name, info in tool_info.items():
        print(f"     - {tool_name}: {info['description']}")
    
    # Test enhanced prompt generation
    print("4. Testing enhanced prompt generation...")
    test_query = "Research AI trends in 2024 and create a comprehensive report"
    enhanced_prompt = spec_agent._generate_enhanced_prompt(test_query)
    print(f"   Generated enhanced prompt (first 200 chars):")
    print(f"   {enhanced_prompt[:200]}...")
    
    # Test specification generation (only if API key is available)
    if os.getenv("OPENAI_API_KEY"):
        print("5. Testing specification generation with LLM...")
        try:
            crew_spec = await spec_agent.generate_crew_spec(test_query)
            print("   ✅ Successfully generated crew specification!")
            
            # Print the full JSON specification
            print("\n" + "=" * 60)
            print("📋 GENERATED JSON SPECIFICATION:")
            print("=" * 60)
            print(json.dumps(crew_spec, indent=2))
            print("=" * 60)
            
            print(f"   Agents: {len(crew_spec.get('agents', []))}")
            print(f"   Tasks: {len(crew_spec.get('tasks', []))}")
            
            # Display the specification structure
            print("   Specification structure:")
            for agent in crew_spec.get('agents', []):
                print(f"     Agent: {agent.get('name')} ({agent.get('source', 'unknown')})")
                print(f"       Tools: {agent.get('tools', [])}")
            
            for task in crew_spec.get('tasks', []):
                print(f"     Task: {task.get('name', task.get('id'))}")
                print(f"       Agent: {task.get('assigned_agent')}")
                print(f"       Dependencies: {task.get('dependencies', [])}")
                
                # Show task detail to verify elaborate format
                description = task.get('description', '')
                expected_output = task.get('expected_output', '')
                print(f"       Description preview: {description[:100]}...")
                print(f"       Expected output preview: {expected_output[:100]}...")
                
                # Check if it follows the elaborate format
                has_multiple_sentences = len(description.split('.')) > 2
                has_detailed_output = len(expected_output.split('.')) > 1
                is_elaborate = has_multiple_sentences and has_detailed_output
                print(f"       ✅ Elaborate format: {is_elaborate}")
            
            # Save specification for inspection
            with open("test_crew_spec.json", "w") as f:
                json.dump(crew_spec, f, indent=2)
            print("   💾 Saved specification to test_crew_spec.json")
            
        except Exception as e:
            print(f"   ❌ Error generating specification: {e}")
    else:
        print("5. Skipping LLM test (no API key)")
    
    # Test fallback specification
    print("6. Testing fallback specification...")
    fallback_spec = spec_agent._get_enhanced_fallback_spec(test_query)
    print("   ✅ Successfully generated fallback specification!")
    
    # Print the fallback JSON specification
    print("\n" + "=" * 60)
    print("📋 FALLBACK JSON SPECIFICATION:")
    print("=" * 60)
    print(json.dumps(fallback_spec, indent=2))
    print("=" * 60)
    
    print(f"   Fallback agents: {len(fallback_spec.get('agents', []))}")
    print(f"   Fallback tasks: {len(fallback_spec.get('tasks', []))}")
    
    # Check fallback task format
    for task in fallback_spec.get('tasks', []):
        description = task.get('description', '')
        expected_output = task.get('expected_output', '')
        print(f"   Fallback task description: {description[:100]}...")
        print(f"   Fallback expected output: {expected_output[:100]}...")
        
        # Verify elaborate format in fallback
        has_multiple_sentences = len(description.split('.')) > 2
        has_detailed_output = len(expected_output.split('.')) > 1
        is_elaborate = has_multiple_sentences and has_detailed_output
        print(f"   ✅ Fallback follows elaborate format: {is_elaborate}")
    
    # Test validation
    print("7. Testing specification validation...")
    try:
        spec_agent._validate_enhanced_specification(fallback_spec)
        print("   ✅ Fallback specification is valid!")
    except Exception as e:
        print(f"   ❌ Validation error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Enhanced SpecAgent testing completed!")
    print("\n💡 Tips:")
    print("   - Set OPENAI_API_KEY to test full LLM functionality")
    print("   - Check test_crew_spec.json for generated specification")
    print("   - The system supports both predefined and custom agents")
    print("   - Task dependencies are automatically handled")

def test_tool_registry():
    """Test the enhanced tool registry functionality."""
    print("\n🔧 Testing Enhanced Tool Registry")
    print("=" * 50)
    
    from tools.tool_registry import (
        instantiate_tool, 
        validate_tool_exists, 
        get_tool_class,
        get_tools_registry
    )
    
    # Test tool existence validation
    print("1. Testing tool existence validation...")
    print(f"   WebSearch exists: {validate_tool_exists('WebSearch')}")
    print(f"   NonExistentTool exists: {validate_tool_exists('NonExistentTool')}")
    
    # Test tool class retrieval
    print("2. Testing tool class retrieval...")
    try:
        web_search_class = get_tool_class("WebSearch")
        print(f"   WebSearch class: {web_search_class.__name__}")
    except Exception as e:
        print(f"   Error getting WebSearch class: {e}")
    
    # Test tool instantiation
    print("3. Testing tool instantiation...")
    try:
        web_search_tool = instantiate_tool("WebSearch")
        print(f"   ✅ Successfully instantiated WebSearch tool: {type(web_search_tool)}")
    except Exception as e:
        print(f"   ❌ Error instantiating WebSearch: {e}")
    
    # Test registry access
    print("4. Testing registry access...")
    registry = get_tools_registry()
    print(f"   Registry contains {len(registry)} tools")
    
    print("✅ Tool registry testing completed!")

async def test_crew_generation():
    """Test the crew generation functionality."""
    print("\n🚀 Testing Crew Generation")
    print("=" * 50)
    
    from crew_generator import generate_crew, generate_crew_sync, quick_research_crew_sync
    
    # Test synchronous crew generation
    print("1. Testing synchronous crew generation...")
    try:
        crew = generate_crew_sync("Research machine learning trends in 2024")
        print(f"   ✅ Successfully generated crew!")
        print(f"   Agents: {len(crew.agents)}")
        print(f"   Tasks: {len(crew.tasks)}")
        
        # Show agent details
        for i, agent in enumerate(crew.agents):
            print(f"     Agent {i+1}: {agent.role}")
            print(f"       Tools: {len(agent.tools)}")
        
        # Show task details
        for i, task in enumerate(crew.tasks):
            print(f"     Task {i+1}: {task.description[:50]}...")
            print(f"       Agent: {task.agent.role}")
        
    except Exception as e:
        print(f"   ❌ Error generating crew: {e}")
    
    # Test quick convenience function
    print("2. Testing quick research crew...")
    try:
        research_crew = quick_research_crew_sync("artificial intelligence ethics")
        print(f"   ✅ Successfully generated research crew!")
        print(f"   Agents: {len(research_crew.agents)}")
        print(f"   Tasks: {len(research_crew.tasks)}")
    except Exception as e:
        print(f"   ❌ Error generating research crew: {e}")
    
    print("✅ Crew generation testing completed!")

async def main():
    """Main test function."""
    await test_enhanced_spec_agent()
    test_tool_registry()
    await test_crew_generation()

def simple_json_test():
    """Simple test that just prints the JSON being generated."""
    print("🔍 SIMPLE JSON GENERATION TEST")
    print("=" * 50)
    
    from agents.spec_agent import SpecAgent
    from tools.tool_registry import get_tool_names
    import json
    
    spec_agent = SpecAgent()
    
    # Test query
    query = "Research AI trends in 2024"
    print(f"Query: '{query}'")
    print(f"Available tools: {get_tool_names()}")
    print("-" * 40)
    
    # Generate fallback specification (always works)
    fallback_spec = spec_agent._get_enhanced_fallback_spec(query)
    print("FALLBACK JSON (Compatible with orchestrator.py):")
    print(json.dumps(fallback_spec, indent=2))
    
    # Try LLM generation if API key is available
    if os.getenv("OPENAI_API_KEY"):
        try:
            import asyncio
            llm_spec = asyncio.run(spec_agent.generate_crew_spec(query))
            print("\nLLM GENERATED JSON:")
            print(json.dumps(llm_spec, indent=2))
        except Exception as e:
            print(f"\nLLM generation failed: {e}")
    else:
        print("\nLLM generation skipped (no OPENAI_API_KEY)")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "simple":
        simple_json_test()
    else:
        asyncio.run(main()) 