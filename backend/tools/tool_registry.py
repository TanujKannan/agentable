from crewai_tools import BrowserbaseLoadTool, WebsiteSearchTool
from typing import Dict, Type, Any


TOOL_REGISTRY = {
    "BrowserbaseLoadTool": BrowserbaseLoadTool,
    "WebsiteSearchTool": WebsiteSearchTool,
}


def instantiate_tool(tool_name: str, **kwargs) -> Any:
    """
    Instantiate a tool from the registry by name.
    
    Args:
        tool_name: Name of the tool in the registry
        **kwargs: Arguments to pass to the tool's __init__ method
    
    Returns:
        Instantiated tool instance
    
    Raises:
        KeyError: If tool_name is not in registry
    """
    if tool_name not in TOOL_REGISTRY:
        raise KeyError(f"Tool '{tool_name}' not found in registry")
    
    tool_class = TOOL_REGISTRY[tool_name]
    return tool_class(**kwargs)


def get_tool_names() -> list[str]:
    """Get list of available tool names"""
    return list(TOOL_REGISTRY.keys())