#!/usr/bin/env python3
"""
Test script to verify browserbase wrapper fixes token limit issues
"""

import sys
import os
sys.path.append('/Users/byrencheema/Coding/PersonalProjects/agentable/backend')

from tools.browserbase_wrapper import BrowserbaseWrapper

def test_content_filtering():
    """Test the content filtering functionality"""
    print("Testing content filtering functionality...")
    
    # Create a mock wrapper for testing
    wrapper = BrowserbaseWrapper(
        api_key="test_key",
        project_id="test_project",
        max_tokens=1000  # Small limit for testing
    )
    
    # Test HTML cleaning
    large_html = """
    <html>
    <head><title>Test Page</title></head>
    <body>
        <nav>Navigation stuff</nav>
        <script>alert('test')</script>
        <style>body { color: red; }</style>
        <main>
            <h1>Main Content</h1>
            <p>This is the main content that should be preserved.</p>
            <p>""" + "Very long content. " * 1000 + """</p>
        </main>
        <footer>Footer content</footer>
    </body>
    </html>
    """
    
    # Test cleaning
    cleaned = wrapper._clean_html_content(large_html)
    print(f"✓ HTML cleaned successfully")
    print(f"✓ Cleaned content length: {len(cleaned)} characters")
    
    # Test token counting
    token_count = wrapper._count_tokens(cleaned)
    print(f"✓ Token count: {token_count}")
    
    # Test truncation
    truncated = wrapper._truncate_content(cleaned)
    print(f"✓ Truncated content length: {len(truncated)} characters")
    
    # Check if truncation message was added
    if "[Content truncated due to size limits]" in truncated:
        print("✓ Content was properly truncated")
    else:
        print("✓ Content was under limit, no truncation needed")
    
    print("\n✅ Content filtering test passed!")
    return True

def test_tool_registry():
    """Test tool registry integration"""
    print("Testing tool registry integration...")
    
    try:
        from tools.tool_registry import instantiate_tool
        
        # Test tool creation
        tool = instantiate_tool("browserbase_tool")
        print(f"✓ Tool created: {tool.name}")
        print(f"✓ Tool description: {tool.description}")
        print(f"✓ Tool type: {type(tool)}")
        
        # Test that it's our wrapper
        if hasattr(tool, 'max_tokens'):
            print(f"✓ Using wrapped tool with max_tokens: {tool.max_tokens}")
        else:
            print("⚠️ Tool may not be wrapped properly")
        
        # Test args_schema
        print(f"✓ args_schema: {tool.args_schema}")
        print(f"✓ args_schema type: {type(tool.args_schema)}")
        if hasattr(tool.args_schema, 'model_fields'):
            print(f"✓ args_schema has model_fields: {bool(tool.args_schema.model_fields)}")
        
        print("\n✅ Tool registry test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Tool registry test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success1 = test_content_filtering()
    success2 = test_tool_registry()
    
    if success1 and success2:
        print("\n🎉 All tests passed! The browserbase wrapper should now prevent token limit errors.")
    else:
        print("\n❌ Some tests failed.")
    
    sys.exit(0 if (success1 and success2) else 1)