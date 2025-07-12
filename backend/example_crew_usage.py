#!/usr/bin/env python3
"""
Example Crew Usage

Simple examples showing how to use the crew generation functions
to create and execute AI agent crews.
"""

import asyncio
import os
from crew_generator import (
    generate_crew_sync, 
    quick_research_crew_sync,
    quick_analysis_crew_sync
)

def example_1_simple_research():
    """Example 1: Generate and run a simple research crew."""
    print("🔍 Example 1: Simple Research Crew")
    print("=" * 40)
    
    # Generate a crew for research
    prompt = "Research the latest developments in renewable energy technology"
    
    try:
        print(f"Generating crew for: {prompt}")
        crew = generate_crew_sync(prompt)
        
        print(f"✅ Generated crew with {len(crew.agents)} agents and {len(crew.tasks)} tasks")
        
        # Show what was created
        print("Agents:")
        for agent in crew.agents:
            print(f"  - {agent.role}")
        
        print("Tasks:")
        for task in crew.tasks:
            print(f"  - {task.description[:60]}...")
        
        # Execute the crew (if API key is available)
        if os.getenv("OPENAI_API_KEY"):
            print("\n🚀 Executing crew...")
            result = crew.kickoff()
            print(f"✅ Crew execution completed!")
            print(f"Result preview: {str(result)[:200]}...")
        else:
            print("⚠️  Set OPENAI_API_KEY to execute the crew")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def example_2_quick_functions():
    """Example 2: Using convenience functions."""
    print("\n📊 Example 2: Quick Convenience Functions")
    print("=" * 40)
    
    # Quick research crew
    try:
        print("Creating quick research crew...")
        research_crew = quick_research_crew_sync("quantum computing applications")
        print(f"✅ Research crew: {len(research_crew.agents)} agents, {len(research_crew.tasks)} tasks")
        
        print("Creating quick analysis crew...")
        analysis_crew = quick_analysis_crew_sync("customer feedback data from Q4 2024")
        print(f"✅ Analysis crew: {len(analysis_crew.agents)} agents, {len(analysis_crew.tasks)} tasks")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def example_3_complex_workflow():
    """Example 3: Complex multi-step workflow."""
    print("\n🏗️ Example 3: Complex Workflow")
    print("=" * 40)
    
    complex_prompt = """
    Create a comprehensive business analysis for launching a new AI-powered 
    mobile app in the productivity space. I need:
    1. Market research and competitive analysis
    2. Technical feasibility assessment  
    3. Marketing strategy development
    4. Financial projections and risk analysis
    5. Implementation roadmap with timeline
    """
    
    try:
        print("Generating complex workflow crew...")
        crew = generate_crew_sync(complex_prompt.strip())
        
        print(f"✅ Generated complex crew:")
        print(f"   Agents: {len(crew.agents)}")
        print(f"   Tasks: {len(crew.tasks)}")
        
        # Show detailed breakdown
        print("\nDetailed breakdown:")
        for i, agent in enumerate(crew.agents, 1):
            print(f"  Agent {i}: {agent.role}")
            
        for i, task in enumerate(crew.tasks, 1):
            print(f"  Task {i}: {task.description[:50]}...")
            print(f"    → Assigned to: {task.agent.role}")
        
        print("\n💡 This crew demonstrates:")
        print("   - Multiple specialized agents")
        print("   - Task dependencies and sequencing")
        print("   - Tool assignment based on requirements")
        
    except Exception as e:
        print(f"❌ Error: {e}")

async def example_4_async_usage():
    """Example 4: Async usage patterns."""
    print("\n⚡ Example 4: Async Usage")
    print("=" * 40)
    
    from crew_generator import generate_crew, quick_research_crew
    
    try:
        print("Generating crew asynchronously...")
        
        # Generate crew asynchronously
        crew = await generate_crew("Analyze social media trends in 2024")
        print(f"✅ Async crew: {len(crew.agents)} agents, {len(crew.tasks)} tasks")
        
        # Quick async research
        research_crew = await quick_research_crew("blockchain technology")
        print(f"✅ Async research crew: {len(research_crew.agents)} agents")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def show_available_features():
    """Show what features are available."""
    print("🎯 Available Features")
    print("=" * 40)
    
    print("Crew Generation Functions:")
    print("  • generate_crew_sync(prompt) - Generate crew from any prompt")
    print("  • generate_crew(prompt) - Async version")
    print("  • quick_research_crew_sync(topic) - Quick research crew")
    print("  • quick_analysis_crew_sync(data) - Quick analysis crew")
    
    print("\nAgent Types:")
    print("  • Predefined: researcher, reporting_analyst")
    print("  • Custom: Created based on prompt requirements")
    
    print("\nTools Available:")
    print("  • WebSearch - Web searching capabilities")
    print("  • FileReader - Read and process files")
    print("  • DirectoryReader - Process directory contents")
    print("  • BrowserbaseLoad - Browser automation")
    
    print("\nKey Features:")
    print("  • Task dependencies and sequencing")
    print("  • Automatic tool assignment")
    print("  • Predefined + custom agent mixing")
    print("  • Comprehensive validation")

async def main():
    """Run all examples."""
    print("🤖 Agentable Crew Generation Examples")
    print("=" * 60)
    
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Note: Set OPENAI_API_KEY to enable crew execution")
        print("   Crews will still be generated for demonstration\n")
    
    show_available_features()
    
    example_1_simple_research()
    example_2_quick_functions()
    example_3_complex_workflow()
    await example_4_async_usage()
    
    print("\n" + "=" * 60)
    print("✅ All examples completed!")
    print("\n💡 Next steps:")
    print("   1. Set OPENAI_API_KEY to execute crews")
    print("   2. Try your own prompts with generate_crew_sync()")
    print("   3. Customize agents in agents/config/agents.yaml")
    print("   4. Add new tools to tools/tool_registry.py")

if __name__ == "__main__":
    asyncio.run(main()) 