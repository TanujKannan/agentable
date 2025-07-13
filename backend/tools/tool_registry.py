from crewai_tools import WebsiteSearchTool, SerperDevTool, CodeDocsSearchTool, DallETool, BrowserbaseLoadTool, EXASearchTool
from typing import Any
import os
from .browserbase_wrapper import BrowserbaseWrapper

# Configure DallE tool with dall-e-3 model
def create_dalle_tool():
    return DallETool(
        model="dall-e-3",      # More reliable model
        size="1024x1024",      # Standard size for dall-e-3
        quality="standard",    # Use standard quality to keep costs lower
        n=1                    # Generate 1 image (dall-e-3 only supports n=1)
    )

# Configure Browserbase tool with API credentials and content filtering
def create_browserbase_tool():
    api_key = os.getenv("BROWSERBASE_API_KEY")
    project_id = os.getenv("BROWSERBASE_PROJECT_ID")
    
    if not api_key or not project_id:
        raise ValueError(
            "Browserbase credentials not configured. Please set BROWSERBASE_API_KEY and BROWSERBASE_PROJECT_ID environment variables. "
            "Get your credentials from https://browserbase.com/"
        )
    
    return BrowserbaseWrapper(
        api_key=api_key,
        project_id=project_id,
        max_tokens=150000  # Safe limit under 200K TPM
    )

TOOL_REGISTRY = {
    "website_search_tool": WebsiteSearchTool,
    "serper_dev_tool": SerperDevTool,
    "code_docs_search_tool": CodeDocsSearchTool,
    "dalle_tool": create_dalle_tool,  # Add DallE tool
    "browserbase_tool": BrowserbaseLoadTool,  # Add Browserbase navigation tool
    "exa_search_tool": EXASearchTool,  # Add EXA semantic search tool
}

def instantiate_tool(tool_name: str, **kwargs) -> Any:
    if tool_name not in TOOL_REGISTRY:
        raise KeyError(f"Tool '{tool_name}' not found in registry. Available tools: {list(TOOL_REGISTRY.keys())}")
    
    tool_class = TOOL_REGISTRY[tool_name]
    
    # Handle DallE tool specially since it's a function
    if tool_name == "dalle_tool":
        return tool_class()
    
    # Handle browserbase tool specially since it's a function
    if tool_name == "browserbase_tool":
        return create_browserbase_tool()
    
    # Handle EXA search tool - instantiate normally
    if tool_name == "exa_search_tool":
        return tool_class(**kwargs)
    
    return tool_class(**kwargs)

def get_tool_names() -> list[str]:
    return list(TOOL_REGISTRY.keys())