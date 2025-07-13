#!/usr/bin/env python3
"""
Test script to verify browserbase wrapper works with CrewAI
"""

import sys
import os
sys.path.append('/Users/byrencheema/Coding/PersonalProjects/agentable/backend')

from crewai import Agent, Task, Crew
from tools.tool_registry import instantiate_tool

def test_crew_integration():
    """Test the browserbase wrapper with CrewAI crew execution"""
    print("Testing browserbase wrapper with CrewAI...")
    
    try:
        # Create browserbase tool
        browserbase_tool = instantiate_tool("browserbase_tool")
        print(f"✓ Created tool: {browserbase_tool.name}")
        
        # Create agent with browserbase tool
        agent = Agent(
            role="web_navigator",
            goal="Navigate websites and extract content",
            backstory="You are a web navigation specialist",
            tools=[browserbase_tool],
            verbose=True
        )
        print("✓ Created agent with browserbase tool")
        
        # Create task
        task = Task(
            description="Load content from https://example.com",
            expected_output="Website content",
            agent=agent
        )
        print("✓ Created task")
        
        # Create crew
        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=True
        )
        print("✓ Created crew")
        
        # Execute crew
        print("🚀 Executing crew...")
        result = crew.kickoff()
        print(f"✅ Crew execution completed successfully!")
        print(f"Result length: {len(str(result))} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ Crew integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_crew_integration()
    sys.exit(0 if success else 1)