import os
from crewai.tools import BaseTool
from pydantic import BaseModel, PrivateAttr
import requests
import json
from openai import OpenAI
from typing import Any

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class SlackListChannelsTool(BaseTool):
    name: str = "ListSlackChannels"
    description: str = "List all available Slack channels."

    _context: Any = PrivateAttr()

    class Args(BaseModel):
        pass  # no inputs

    def __init__(self, context):
        super().__init__(
            name="ListSlackChannels",
            description="List all available Slack channels.",
            args_schema=self.Args
        )
        self._bot_token = os.getenv('SLACK_BOT_TOKEN')
        self._context = context
        self._base_url = "https://slack.com/api"
        self._headers = {
            "Authorization": f"Bearer {self._bot_token}",
            "Content-Type": "application/json"
        }

    def _run(self):
        cached = self._context.get("slack_channels")

        if cached:
            return json.dumps(cached)

        channels_result = self._get_channels()
        
        # Extract just the channels list from the result
        if isinstance(channels_result, dict) and "channels" in channels_result:
            channels = channels_result["channels"]
        else:
            channels = channels_result
            
        # Store only the channels list in context
        self._context.set("slack_channels", channels)
        print(f"🔍 ListSlackChannels: Stored {len(channels)} channels in context")
        print(f"🔍 ListSlackChannels: Channel names: {[ch['name'] for ch in channels]}")
        
        # Return the full result for the agent to see
        return json.dumps(channels_result)
    
    def _get_channels(self) -> dict:
        """Get list of available public Slack channels (structured data)."""
        try:
            response = requests.get(
                f"{self._base_url}/conversations.list",
                headers=self._headers,
                params={"types": "public_channel"}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    channels = []
                    for channel in result.get("channels", []):
                        channels.append({
                            "id": channel.get("id"),
                            "name": channel.get("name"),
                            "is_private": channel.get("is_private", False),
                            "member_count": channel.get("num_members", 0),
                            "topic": channel.get("topic", {}).get("value", ""),
                            "purpose": channel.get("purpose", {}).get("value", "")
                        })
                    return {
                        "status": "success",
                        "channels": channels,
                        "count": len(channels)
                    }
                else:
                    return {"status": "error", "message": f"Slack API error: {result.get('error')}"}
            else:
                return {"status": "error", "message": f"HTTP error: {response.status_code}"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to get channels: {str(e)}"}

