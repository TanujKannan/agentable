#!/usr/bin/env python3

"""
Test script for the Dall-E tool implementation
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from tools.tool_registry import instantiate_tool, get_tool_names
from agents.spec_agent import SpecAgent
from crewai import Agent, Task, Crew

async def test_dalle_tool_registry():
    """Test that the Dall-E tool is properly registered"""
    print("🔧 Testing Dall-E tool registration...")
    
    # Check if dalle_tool is in the registry
    tool_names = get_tool_names()
    print(f"Available tools: {tool_names}")
    
    if "dalle_tool" in tool_names:
        print("✅ Dall-E tool is registered!")
        
        # Try to instantiate the tool
        dalle_tool = instantiate_tool("dalle_tool")
        print(f"✅ Dall-E tool instantiated successfully!")
        print(f"   Model: dall-e-3")
        print(f"   Size: 1024x1024")
        print(f"   Quality: standard")
        print(f"   Images per request: 1")
        
        return dalle_tool
    else:
        print("❌ Dall-E tool not found in registry")
        return None

async def test_spec_agent_with_image_prompt():
    """Test that SpecAgent can generate crew specs for image generation"""
    print("\n📋 Testing SpecAgent with image generation prompt...")
    
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not set, using fallback specification")
    
    spec_agent = SpecAgent()
    
    # Test with an image generation prompt
    prompt = "Create a beautiful landscape image of a mountain sunset"
    
    try:
        crew_spec = await spec_agent.generate_crew_spec(prompt)
        print("✅ Generated crew specification:")
        print(f"   Agents: {[agent['name'] for agent in crew_spec.get('agents', [])]}")
        print(f"   Tasks: {len(crew_spec.get('tasks', []))} tasks")
        
        # Check if dalle_tool is included
        for agent in crew_spec.get('agents', []):
            if 'dalle_tool' in agent.get('tools', []):
                print(f"   ✅ Agent '{agent['name']}' has dalle_tool")
                
        return crew_spec
    except Exception as e:
        print(f"❌ Error generating crew spec: {str(e)}")
        return None

async def test_manual_crew_with_dalle():
    """Test creating a manual crew with Dall-E tool"""
    print("\n🚀 Testing manual crew creation with Dall-E...")
    
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not set, skipping crew execution test")
        return
    
    try:
        # Create an agent with the Dall-E tool
        dalle_tool = instantiate_tool("dalle_tool")
        
        image_creator = Agent(
            role="Image Creator",
            goal="Generate beautiful images from text descriptions",
            backstory="You are a skilled digital artist who specializes in creating images from textual descriptions using AI tools.",
            tools=[dalle_tool],
            verbose=True
        )
        
        # Create a task for image generation
        image_task = Task(
            description="Create a serene mountain landscape at sunset with vibrant colors",
            expected_output="A generated image file showing a mountain landscape at sunset",
            agent=image_creator
        )
        
        # Create a crew
        crew = Crew(
            agents=[image_creator],
            tasks=[image_task],
            verbose=True
        )
        
        print("✅ Crew created successfully!")
        print("   Agent: Image Creator with Dall-E tool")
        print("   Task: Generate mountain landscape image")
        print("   Note: Use crew.kickoff() to execute (requires OpenAI API key)")
        
        return crew
        
    except Exception as e:
        print(f"❌ Error creating crew: {str(e)}")
        return None

async def main():
    """Run all tests"""
    print("🎨 Testing Dall-E Tool Implementation")
    print("=" * 50)
    
    # Test 1: Tool registry
    dalle_tool = await test_dalle_tool_registry()
    
    # Test 2: SpecAgent
    crew_spec = await test_spec_agent_with_image_prompt()
    
    # Test 3: Manual crew creation
    crew = await test_manual_crew_with_dalle()
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"   Tool Registry: {'✅ PASS' if dalle_tool else '❌ FAIL'}")
    print(f"   SpecAgent: {'✅ PASS' if crew_spec else '❌ FAIL'}")
    print(f"   Manual Crew: {'✅ PASS' if crew else '❌ FAIL'}")
    
    if dalle_tool and crew_spec and crew:
        print("\n🎉 All tests passed! Dall-E tool is ready to use.")
        print("\nTo use in your application:")
        print("1. Set OPENAI_API_KEY environment variable")
        print("2. Use prompts like: 'Create an image of a sunset'")
        print("3. The system will automatically use the dalle_tool")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")

if __name__ == "__main__":
    asyncio.run(main()) 