import os
from crewai.tools import BaseTool
from pydantic import BaseModel, PrivateAttr
import requests
import json
from openai import OpenAI
import re
from typing import Any

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class SlackResolveChannelTool(BaseTool):
    name: str = "ResolveSlackChannel"
    description: str = "Find a Slack channel by name or topic and store its ID."

    _context: Any = PrivateAttr()

    class Args(BaseModel):
        name_or_topic: str
        alias: str 

    def __init__(self, context, llm=None):
        super().__init__(
            name="ResolveSlackChannel",
            description="Find a Slack channel by name or topic and store its ID.",
            args_schema=self.Args
        )
        self._bot_token = os.getenv('SLACK_BOT_TOKEN')
        self._context = context
        self._base_url = "https://slack.com/api"
        self._headers = {
            "Authorization": f"Bearer {self._bot_token}",
            "Content-Type": "application/json"
        }
        self._llm = llm or OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def _run(self, name_or_topic: str, alias: str):
        print(f"🔍 ResolveSlackChannel: Called with name_or_topic='{name_or_topic}', alias='{alias}'")
        print(f"🔍 ResolveSlackChannel: Parameter types - name_or_topic: {type(name_or_topic)}, alias: {type(alias)}")
        print(f"🔍 ResolveSlackChannel: Parameter values - name_or_topic: '{name_or_topic}', alias: '{alias}'")
        channels = self._context.get("slack_channels")
        if not channels:
            return "No Slack channels cached. Run ListSlackChannelsTool first."
        
        # Ensure channels is a list
        if isinstance(channels, dict) and "channels" in channels:
            channels = channels["channels"]
        elif not isinstance(channels, list):
            return f"Invalid channels data in context: {type(channels)}"
        
        print(f"🔍 ResolveSlackChannel: Looking for '{name_or_topic}' in {len(channels)} channels")
        print(f"🔍 ResolveSlackChannel: Available channels: {[ch['name'] for ch in channels]}")
    
        prompt = self._build_prompt(name_or_topic, channels)
        response = self._llm.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )

        raw_output = response.choices[0].message.content
        if raw_output:
            raw_output = raw_output.strip()
        else:
            return "No response from LLM"
        
        print(f"🔍 ResolveSlackChannel: LLM output: '{raw_output}'")
        channel_id = self._extract_channel_id(raw_output)
        print(f"🔍 ResolveSlackChannel: Extracted channel_id: '{channel_id}'")

        if not channel_id:
            return f"Could not resolve channel for '{name_or_topic}'. No matching channel found. LLM output: '{raw_output}'"

        self._context.set(alias, channel_id)
        print(f"🔍 ResolveSlackChannel: Set alias '{alias}' = '{channel_id}' in context")
        return f"LLM resolved '{name_or_topic}' to ID {channel_id} (alias: {alias})"

    def _build_prompt(self, query, channels):
        formatted_channels = "\n".join(
            f"- ID: {ch['id']}, Name: {ch['name']}, Topic: {ch.get('topic','')}, Purpose: {ch.get('purpose','')}"
            for ch in channels
        )
        return (
            f"User wants to find the Slack channel for: '{query}'\n"
            f"Choose the best match from the following channels:\n{formatted_channels}\n"
            f"Return ONLY the `ID` of the best match. No explanation."
        )
    
    def _extract_channel_id(self, output: str):
        match = re.search(r'\b(C[A-Z0-9]+)\b', output)
        return match.group(1) if match else None