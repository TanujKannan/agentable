from crewai_tools import WebsiteSearchTool, SerperDevTool
from typing import Any
import os

TOOL_REGISTRY = {
    "website_search_tool": WebsiteSearchTool,
    "serper_dev_tool": SerperDevTool,
}

def instantiate_tool(tool_name: str, **kwargs) -> Any:
    if tool_name not in TOOL_REGISTRY:
        raise KeyError(f"Tool '{tool_name}' not found in registry. Available tools: {list(TOOL_REGISTRY.keys())}")
    
    tool_class = TOOL_REGISTRY[tool_name]
    return tool_class(**kwargs)

def get_tool_names() -> list[str]:
    return list(TOOL_REGISTRY.keys())