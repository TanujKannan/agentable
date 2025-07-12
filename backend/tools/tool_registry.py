from crewai_tools import BrowserbaseLoadTool, WebsiteSearchTool
from typing import Any


TOOL_REGISTRY = {
    "BrowserbaseLoadTool": BrowserbaseLoadTool,
    "WebsiteSearchTool": WebsiteSearchTool,
}

def instantiate_tool(tool_name: str, **kwargs) -> Any:
    if tool_name not in TOOL_REGISTRY:
        raise KeyError(f"Tool '{tool_name}' not found in registry")
    
    tool_class = TOOL_REGISTRY[tool_name]
    return tool_class(**kwargs)

def get_tool_names() -> list[str]:
    return list(TOOL_REGISTRY.keys())