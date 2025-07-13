import os
from crewai.tools import BaseTool
from pydantic import BaseModel, PrivateAttr
import requests
import json
from typing import Any

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class SlackSendMessageTool(BaseTool):
    name: str = "SendSlackMessage"
    description: str = "Send a message to a Slack channel using its alias."

    _context: Any = PrivateAttr()

    class Args(BaseModel):
        channel_ref: str
        message: str

    def __init__(self, context):
        super().__init__(
            name="SendSlackMessage",
            description="Send a message to a Slack channel using its alias.",
            args_schema=self.Args
        )
        self._bot_token = os.getenv('SLACK_BOT_TOKEN')
        self._context = context
        self._base_url = "https://slack.com/api"
        self._headers = {
            "Authorization": f"Bearer {self._bot_token}",
            "Content-Type": "application/json"
        }

    def _run(self, channel_ref: str, message: str):
        channel_id = self._context.get(channel_ref) # get from context
        if not channel_id:
            # Debug: show what's actually in context
            all_context = self._context.all()
            return f"Channel alias '{channel_ref}' not found. Available aliases: {list(all_context.keys())}"
        
        result = self._send_message(channel_id, message)
        return result
    
    def _send_message(self, channel: str, message: str) -> str:
        try:
            payload = {
                "channel": channel,
                "text": message
            }
            
            response = requests.post(
                f"{self._base_url}/chat.postMessage",
                headers=self._headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    return json.dumps({
                        "status": "success",
                        "message": f"Message sent to {channel}",
                        "ts": result.get("ts"),
                        "channel": result.get("channel")
                    })
                else:
                    return json.dumps({
                        "status": "error",
                        "message": f"Slack API error: {result.get('error')}"
                    })
            else:
                return json.dumps({
                    "status": "error",
                    "message": f"HTTP error: {response.status_code}"
                })
                
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to send message: {str(e)}"
            })
