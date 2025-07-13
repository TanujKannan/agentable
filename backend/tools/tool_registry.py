from crewai_tools import WebsiteSearchTool, SerperDevTool, CodeDocsSearchTool, DallETool, ZapierActionTools
from tools.google_slides_tool import GoogleSlidesTool
from tools.slack_tool import SlackTool
from typing import Any
import os

# Configure DallE tool with dall-e-3 model
def create_dalle_tool():
    return DallETool(
        model="dall-e-3",      # More reliable model
        size="1024x1024",      # Standard size for dall-e-3
        quality="standard",    # Use standard quality to keep costs lower
        n=1                    # Generate 1 image (dall-e-3 only supports n=1)
    )

TOOL_REGISTRY = {
    # "website_search_tool": WebsiteSearchTool,
    "serper_dev_tool": SerperDevTool,
    # "code_docs_search_tool": CodeDocsSearchTool,
    # "dalle_tool": create_dalle_tool,  # Add DallE tool
    # "google_slides_tool": GoogleSlidesTool,
    "slack_tool": SlackTool,
}

KWARGS_REGISTRY = {
    "serper_dev_tool": {
        "query": "Search query based on the task",
        "limit": "Number of results (default: 10)"
    },
    "slack_tool": {
        "action": [
            "send_message",
            "send_dm", 
            "get_channels",
            "get_users",
            "find_channel",
            "find_user",
            "send_formatted_message"
        ],
        "channel": "Appropriate channel based on the task",
        "message": "Appropriate message based on the task"
    }
}

def instantiate_tool(tool_name: str, **kwargs) -> Any:
    if tool_name not in TOOL_REGISTRY:
        raise KeyError(f"Tool '{tool_name}' not found in registry. Available tools: {list(TOOL_REGISTRY.keys())}")
    
    tool_class = TOOL_REGISTRY[tool_name]
    
    # Handle DallE tool specially since it's a function
    if tool_name == "dalle_tool":
        return tool_class()
    
    return tool_class(**kwargs)

def get_tool_names() -> list[str]:
    return list(TOOL_REGISTRY.keys())

def get_tool_kwargs() -> dict[str, Any]:
    return KWARGS_REGISTRY