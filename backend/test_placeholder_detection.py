#!/usr/bin/env python3
"""
Test script to verify placeholder detection works with # prefixes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.parameterized_tool import ParameterizedTool

def test_placeholder_detection():
    """Test that placeholder detection works with # prefixes"""
    
    # Create a dummy tool for testing
    from crewai.tools import BaseTool
    
    class DummyTool(BaseTool):
        name: str = "dummy_tool"
        description: str = "A dummy tool"
        
        def _run(self, *args, **kwargs):
            return "dummy result"
    
    # Create ParameterizedTool instance
    param_tool = ParameterizedTool(DummyTool(), {})
    
    # Test cases
    test_cases = [
        ("#selected_channel", False),  # Should be detected as placeholder
        ("selected_channel", False),   # Should be detected as placeholder  
        ("#general", True),           # Should be detected as real value
        ("general", True),            # Should be detected as real value
        ("C095GES3SF8", True),        # Should be detected as real value
        ("Your message here", False), # Should be detected as placeholder
        ("Let's schedule a meeting", True), # Should be detected as real value
    ]
    
    print("🧪 Testing placeholder detection:")
    for value, expected in test_cases:
        result = param_tool._is_real_value(value)
        status = "✅" if result == expected else "❌"
        print(f"   {status} '{value}' -> {result} (expected {expected})")

if __name__ == "__main__":
    test_placeholder_detection() 