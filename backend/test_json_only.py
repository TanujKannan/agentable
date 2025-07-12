#!/usr/bin/env python3
"""
Simple test to show only the JSON output from spec_agent without creating crews.
This avoids tool installation issues and focuses on just the JSON generation.
"""

import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from agents.spec_agent import SpecAgent
from tools.tool_registry import get_tool_names

def test_json_output():
    """Test and save the JSON output from spec_agent."""
    print("🔍 JSON OUTPUT TEST")
    print("=" * 50)
    
    # Initialize spec_agent
    spec_agent = SpecAgent()
    
    # Test query
    query = "Research AI trends in 2024"
    print(f"Query: '{query}'")
    print(f"Available tools: {get_tool_names()}")
    print("-" * 40)
    
    # Generate fallback specification (always works)
    print("📋 FALLBACK JSON SPECIFICATION:")
    print("=" * 40)
    fallback_spec = spec_agent._get_enhanced_fallback_spec(query)
    print(json.dumps(fallback_spec, indent=2))
    
    # Save fallback specification to file
    with open("fallback_spec.json", "w") as f:
        json.dump(fallback_spec, f, indent=2)
    print("💾 Saved fallback specification to fallback_spec.json")
    print()
    
    # Try LLM generation if API key is available
    if os.getenv("OPENAI_API_KEY"):
        try:
            import asyncio
            print("📋 LLM GENERATED JSON SPECIFICATION:")
            print("=" * 40)
            llm_spec = asyncio.run(spec_agent.generate_crew_spec(query))
            print(json.dumps(llm_spec, indent=2))
            
            # Save LLM specification to file
            with open("llm_generated_spec.json", "w") as f:
                json.dump(llm_spec, f, indent=2)
            print("💾 Saved LLM specification to llm_generated_spec.json")
            
        except Exception as e:
            print(f"❌ LLM generation failed: {e}")
            print("Only fallback specification is available.")
    else:
        print("⚠️  LLM generation skipped (no OPENAI_API_KEY)")
        print("Only fallback specification is available.")
    
    print("\n" + "=" * 50)
    print("✅ JSON OUTPUT TEST COMPLETED!")
    print("\n📄 Generated Files:")
    print("   - fallback_spec.json (always generated)")
    if os.getenv("OPENAI_API_KEY"):
        print("   - llm_generated_spec.json (if LLM worked)")
    print("\n🔍 These files show the JSON that would be sent to orchestrator.py")

if __name__ == "__main__":
    test_json_output() 