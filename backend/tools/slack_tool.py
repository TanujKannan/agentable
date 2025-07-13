"""
Slack Tool for CrewAI
Handles sending messages to Slack channels
"""

import os
from typing import Dict, Any, List, Optional, ClassVar
from crewai.tools import BaseTool
from pydantic import Field
import requests
import json

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class SlackTool(BaseTool):
    """
    A tool for sending messages to Slack channels.
    
    Capabilities:
    - Send text messages to channels
    - Send formatted messages with attachments
    - Send messages to specific users via DM
    - Get channel information
    
    Required parameters:
    - action: The operation to perform (send_message, get_channels, etc.)
    - channel: Channel ID or name (for sending messages)
    - message: Text content to send
    """
    
    # Required BaseTool fields
    name: str = Field(default="slack_tool", description="Tool name")
    description: str = Field(default="Tool for sending messages to Slack channels. Automatically resolves channel names (#general) and usernames (@john) to IDs. Use with action parameter: send_message, send_dm, get_channels, get_users, find_channel, find_user", description="Tool description")
    
    def __init__(self, **data):
        super().__init__(**data)
        self._validate_config()
    
    def _validate_config(self):
        """Validate Slack configuration"""
        self._bot_token = os.getenv('SLACK_BOT_TOKEN')
        if not self._bot_token:
            raise ValueError(
                "Slack bot token not found in environment variables. "
                "Please set SLACK_BOT_TOKEN in your .env file"
            )
        
        # Validate token format
        if not self._bot_token.startswith('xoxb-'):
            raise ValueError(
                "Invalid Slack bot token format. Token should start with 'xoxb-'"
            )
        
        self._base_url = "https://slack.com/api"
        self._headers = {
            "Authorization": f"Bearer {self._bot_token}",
            "Content-Type": "application/json"
        }
    
    def _run(self, action: str, **kwargs) -> str:
        """
        Dispatches the requested Slack action. This method is called by CrewAI with all task parameters.
        Required parameter: action (str)
        Other parameters depend on the action.
        
        The tool automatically derives IDs from names:
        - Channel names like "#general" or "general" → channel ID
        - Usernames like "@john" or "john" → user ID
        """
        try:
            if action == "send_message":
                channel = kwargs.get("channel")
                message = kwargs.get("message")
                if not channel or not message:
                    return json.dumps({
                        "status": "error", 
                        "message": "Missing required parameters: channel, message"
                    })
                
                # Auto-derive channel ID if needed
                channel_id = self._resolve_channel_id(channel)
                if not channel_id:
                    return json.dumps({
                        "status": "error",
                        "message": f"Could not find channel: {channel}"
                    })
                
                return self._send_message(channel=channel_id, message=message)
                
            elif action == "send_dm":
                user = kwargs.get("user")  # Can be username, @username, or user ID
                message = kwargs.get("message")
                if not user or not message:
                    return json.dumps({
                        "status": "error", 
                        "message": "Missing required parameters: user, message"
                    })
                
                # Auto-derive user ID if needed
                user_id = self._resolve_user_id(user)
                if not user_id:
                    return json.dumps({
                        "status": "error",
                        "message": f"Could not find user: {user}"
                    })
                
                return self._send_dm(user_id=user_id, message=message)
                
            elif action == "get_channels":
                return self._get_channels()
                
            elif action == "get_users":
                return self._get_users()
                
            elif action == "find_channel":
                channel_name = kwargs.get("channel_name")
                if not channel_name:
                    return json.dumps({
                        "status": "error",
                        "message": "Missing required parameter: channel_name"
                    })
                return self._find_channel(channel_name)
                
            elif action == "find_user":
                username = kwargs.get("username")
                if not username:
                    return json.dumps({
                        "status": "error",
                        "message": "Missing required parameter: username"
                    })
                return self._find_user(username)
                
            elif action == "send_formatted_message":
                channel = kwargs.get("channel")
                message = kwargs.get("message")
                attachments = kwargs.get("attachments", [])
                if not channel or not message:
                    return json.dumps({
                        "status": "error",
                        "message": "Missing required parameters: channel, message"
                    })
                
                # Auto-derive channel ID if needed
                channel_id = self._resolve_channel_id(channel)
                if not channel_id:
                    return json.dumps({
                        "status": "error",
                        "message": f"Could not find channel: {channel}"
                    })
                
                return self._send_formatted_message(
                    channel=channel_id, 
                    message=message, 
                    attachments=attachments
                )
                
            else:
                return json.dumps({"status": "error", "message": f"Unknown action: {action}"})
                
        except Exception as e:
            return json.dumps({"status": "error", "message": f"Exception in SlackTool: {str(e)}"})
    
    def _send_message(self, channel: str, message: str) -> str:
        """Send a simple text message to a Slack channel"""
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
    
    def _send_dm(self, user_id: str, message: str) -> str:
        """Send a direct message to a user"""
        try:
            # First, open a DM with the user
            dm_payload = {
                "users": user_id
            }
            
            dm_response = requests.post(
                f"{self._base_url}/conversations.open",
                headers=self._headers,
                json=dm_payload
            )
            
            if dm_response.status_code != 200:
                return json.dumps({
                    "status": "error",
                    "message": f"Failed to open DM: {dm_response.status_code}"
                })
            
            dm_result = dm_response.json()
            if not dm_result.get("ok"):
                return json.dumps({
                    "status": "error",
                    "message": f"Failed to open DM: {dm_result.get('error')}"
                })
            
            # Send message to the DM channel
            channel_id = dm_result["channel"]["id"]
            return self._send_message(channel=channel_id, message=message)
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to send DM: {str(e)}"
            })
    
    def _send_formatted_message(self, channel: str, message: str, attachments: Optional[List[Dict[str, Any]]] = None) -> str:
        """Send a formatted message with attachments"""
        try:
            payload: Dict[str, Any] = {
                "channel": channel,
                "text": message
            }
            
            if attachments:
                payload["attachments"] = attachments
            
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
                        "message": f"Formatted message sent to {channel}",
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
                "message": f"Failed to send formatted message: {str(e)}"
            })
    
    def _get_channels(self) -> str:
        """Get list of available channels"""
        try:
            # Only get public channels since we only have channels:read scope
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
                            "member_count": channel.get("num_members", 0)
                        })
                    
                    return json.dumps({
                        "status": "success",
                        "channels": channels,
                        "count": len(channels)
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
                "message": f"Failed to get channels: {str(e)}"
            })
    
    def _get_users(self) -> str:
        """Get list of users in the workspace"""
        try:
            response = requests.get(
                f"{self._base_url}/users.list",
                headers=self._headers
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    users = []
                    for user in result.get("members", []):
                        if not user.get("deleted") and not user.get("is_bot"):
                            users.append({
                                "id": user.get("id"),
                                "name": user.get("name"),
                                "real_name": user.get("real_name"),
                                "display_name": user.get("profile", {}).get("display_name")
                            })
                    
                    return json.dumps({
                        "status": "success",
                        "users": users,
                        "count": len(users)
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
                "message": f"Failed to get users: {str(e)}"
            }) 
    
    def _resolve_channel_id(self, channel_input: str) -> Optional[str]:
        """
        Resolve channel ID from various input formats:
        - "#general" → channel ID
        - "general" → channel ID  
        - "C1234567890" → channel ID (already an ID)
        """
        # If it's already a channel ID (starts with C)
        if channel_input.startswith('C'):
            return channel_input
        
        # Remove # if present
        channel_name = channel_input.lstrip('#')
        
        # Get all channels and find the matching one
        channels_result = self._get_channels()
        try:
            channels_data = json.loads(channels_result)
            if channels_data.get("status") == "success":
                for channel in channels_data.get("channels", []):
                    if channel.get("name") == channel_name:
                        return channel.get("id")
        except:
            pass
        
        return None
    
    def _resolve_user_id(self, user_input: str) -> Optional[str]:
        """
        Resolve user ID from various input formats:
        - "@john" → user ID
        - "john" → user ID
        - "U1234567890" → user ID (already an ID)
        """
        # If it's already a user ID (starts with U)
        if user_input.startswith('U'):
            return user_input
        
        # Remove @ if present
        username = user_input.lstrip('@')
        
        # Get all users and find the matching one
        users_result = self._get_users()
        try:
            users_data = json.loads(users_result)
            if users_data.get("status") == "success":
                for user in users_data.get("users", []):
                    if (user.get("name") == username or 
                        user.get("real_name", "").lower() == username.lower() or
                        user.get("display_name", "").lower() == username.lower()):
                        return user.get("id")
        except:
            pass
        
        return None
    
    def _find_channel(self, channel_name: str) -> str:
        """Find a specific channel by name"""
        channel_id = self._resolve_channel_id(channel_name)
        if channel_id:
            return json.dumps({
                "status": "success",
                "channel_id": channel_id,
                "channel_name": channel_name.lstrip('#')
            })
        else:
            return json.dumps({
                "status": "error",
                "message": f"Channel not found: {channel_name}"
            })
    
    def _find_user(self, username: str) -> str:
        """Find a specific user by username"""
        user_id = self._resolve_user_id(username)
        if user_id:
            return json.dumps({
                "status": "success",
                "user_id": user_id,
                "username": username.lstrip('@')
            })
        else:
            return json.dumps({
                "status": "error",
                "message": f"User not found: {username}"
            }) 