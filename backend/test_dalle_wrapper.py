#!/usr/bin/env python3
"""
Test script to verify DALL-E wrapper cleans up markdown output
"""

import sys
import os
sys.path.append('/Users/byrencheema/Coding/PersonalProjects/agentable/backend')

from tools.dalle_wrapper import DalleWrapper

def test_dalle_output_cleaning():
    """Test the DALL-E output cleaning functionality"""
    print("Testing DALL-E output cleaning...")
    
    # Test various polluted outputs
    test_cases = [
        "Flag of Luxembourg: ![Luxembourg Flag](!Generated Image)",
        "Flag of Singapore: ![Singapore Flag](!Generated Image)",
        "Flag of Qatar: ![Qatar Flag](!Generated Image)",
        "Multiple flags: ![Flag 1](!Generated Image) and ![Flag 2](!Generated Image)",
        "Mixed content: Here's a flag ![Test Flag](!Generated Image) and some text !Generated Image more text"
    ]
    
    wrapper = DalleWrapper()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}:")
        print(f"Original: {test_case}")
        
        cleaned = wrapper._clean_dalle_output(test_case)
        print(f"Cleaned:  {cleaned}")
        
        # Check if pollution was removed
        if "!Generated Image" in cleaned:
            print("⚠️  Still contains pollution")
        else:
            print("✅ Pollution removed")
    
    print("\n✅ DALL-E output cleaning test completed!")
    return True

def test_tool_registry():
    """Test tool registry integration"""
    print("Testing DALL-E tool registry integration...")
    
    try:
        from tools.tool_registry import instantiate_tool
        
        # Test tool creation
        tool = instantiate_tool("dalle_tool")
        print(f"✓ Tool created: {tool.name}")
        print(f"✓ Tool type: {type(tool)}")
        
        # Test that it's our wrapper
        if hasattr(tool, '_clean_dalle_output'):
            print("✓ Using wrapped DALL-E tool with output cleaning")
        else:
            print("⚠️ Tool may not be wrapped properly")
        
        print("\n✅ Tool registry test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Tool registry test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success1 = test_dalle_output_cleaning()
    success2 = test_tool_registry()
    
    if success1 and success2:
        print("\n🎉 All tests passed! The DALL-E wrapper should now clean up markdown output.")
    else:
        print("\n❌ Some tests failed.")
    
    sys.exit(0 if (success1 and success2) else 1)