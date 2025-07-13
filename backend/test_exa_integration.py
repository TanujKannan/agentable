#!/usr/bin/env python3
"""
Test script to verify EXA integration with CrewAI
"""
import os
import sys
import asyncio
from agents.spec_agent import SpecAgent
from tools.tool_registry import get_tool_names, instantiate_tool

def test_tool_registration():
    """Test that EXA tools are properly registered"""
    print("Testing tool registration...")
    tool_names = get_tool_names()
    
    expected_tools = ["exa_search_tool"]
    
    for tool in expected_tools:
        if tool in tool_names:
            print(f"✅ {tool} is registered")
        else:
            print(f"❌ {tool} is NOT registered")
            return False
    
    return True

def test_tool_instantiation():
    """Test that EXA tools can be instantiated"""
    print("\nTesting tool instantiation...")
    
    try:
        exa_tool = instantiate_tool("exa_search_tool")
        print("✅ exa_search_tool instantiated successfully")
        
        return True
    except Exception as e:
        print(f"❌ Tool instantiation failed: {e}")
        return False

async def test_spec_agent_exa():
    """Test that SpecAgent can generate specs with EXA tools"""
    print("\nTesting SpecAgent with EXA prompt...")
    
    # Test prompt that should trigger EXA usage
    prompt = "Find high-quality research papers about machine learning interpretability"
    
    try:
        spec_agent = SpecAgent()
        crew_spec = await spec_agent.generate_crew_spec(prompt)
        
        # Check if EXA tools are included
        exa_used = False
        for agent in crew_spec.get('agents', []):
            tools = agent.get('tools', [])
            if 'exa_search_tool' in tools:
                exa_used = True
                print(f"✅ Agent '{agent['name']}' uses EXA tools: {tools}")
                break
        
        if not exa_used:
            print("❌ No agent uses EXA tools in the generated spec")
            print("Generated spec:", crew_spec)
            return False
        
        return True
    except Exception as e:
        print(f"❌ SpecAgent test failed: {e}")
        return False

def test_environment_variables():
    """Test that required environment variables are set"""
    print("\nTesting environment variables...")
    
    required_vars = ["EXA_API_KEY"]
    
    for var in required_vars:
        if os.getenv(var):
            print(f"✅ {var} is set")
        else:
            print(f"❌ {var} is NOT set")
            return False
    
    return True

async def main():
    """Run all tests"""
    print("🧪 Testing EXA Integration with CrewAI\n")
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("Tool Registration", test_tool_registration),
        ("Tool Instantiation", test_tool_instantiation),
        ("SpecAgent Integration", test_spec_agent_exa),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"Running {test_name}...")
        
        if asyncio.iscoroutinefunction(test_func):
            result = await test_func()
        else:
            result = test_func()
        
        results.append((test_name, result))
        print()
    
    # Summary
    print("=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! EXA integration is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)