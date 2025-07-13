from crewai_tools import WebsiteSearchTool, SerperDevTool, CodeDocsSearchTool, DallETool, ZapierActionTools, BrowserbaseLoadTool
from tools.google_slides_tool import GoogleSlidesTool
from tools.slack_resolve_channel_tool import SlackResolveChannelTool
from tools.slack_list_channels_tool import SlackListChannelsTool
from tools.slack_send_message_tool import SlackSendMessageTool
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
    "website_search_tool": WebsiteSearchTool,
    "serper_dev_tool": SerperDevTool,
    "code_docs_search_tool": CodeDocsSearchTool,
    "dalle_tool": create_dalle_tool,  # Add DallE tool
    "slack_list_channels_tool": SlackListChannelsTool,
    "slack_resolve_channel_tool": SlackResolveChannelTool,
    "slack_send_message_tool": SlackSendMessageTool,
    "browserbase_tool": BrowserbaseLoadTool
}

KWARGS_REGISTRY = {
    "serper_dev_tool": {
        "query": "Search query based on the task",
        "limit": "Number of results (default: 10)"
    },

    "slack_send_message_tool": {
        "channel_ref": "Alias of the Slack channel to send the message to",
        "message": "The text message to send"
    },
    "slack_resolve_channel_tool": {
        "name_or_topic": "Human-friendly channel name or topic to match",
        "alias": "Alias to use for referencing the channel later"
    },
    "slack_list_channels_tool": {
        # no inputs needed
    },
    "browserbase_tool": {
        "url": "URL to navigate to",
        "action": "Action to perform (load, click, scroll, etc.)"
    },
}

def instantiate_tool(tool_name: str, context=None, **kwargs) -> Any:
    if tool_name not in TOOL_REGISTRY:
        raise KeyError(f"Tool '{tool_name}' not found in registry. Available tools: {list(TOOL_REGISTRY.keys())}")
    
    tool_class = TOOL_REGISTRY[tool_name]
    
    # Handle DallE tool specially since it's a function
    if tool_name == "dalle_tool":
        return tool_class()
    
    # Handle browserbase tool - instantiate normally
    if tool_name == "browserbase_tool":
        return tool_class(**kwargs)
    
    # Pass context to tools that need it
    if context and tool_name in ["slack_list_channels_tool", "slack_resolve_channel_tool", "slack_send_message_tool"]:
        return tool_class(context=context, **kwargs)
    
    return tool_class(**kwargs)

def get_tool_names() -> list[str]:
    return list(TOOL_REGISTRY.keys())

def get_tool_kwargs() -> dict[str, Any]:
    return KWARGS_REGISTRY