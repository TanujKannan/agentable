import json
from typing import Dict, Any
import openai
import os

from tools.tool_registry import get_tool_names, get_tool_kwargs, instantiate_tool

class SpecAgent:
    """
    SpecAgent converts user prompts into CrewAI task specifications
    """
    
    def __init__(self):
        # Initialize OpenAI client (or use any LLM provider)
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = openai.OpenAI(api_key=api_key)
        else:
            self.client = None
        self.tool_names = get_tool_names()
        self.tool_kwargs = get_tool_kwargs()
    
    async def generate_crew_spec(self, prompt: str) -> Dict[str, Any]:
        """
        Takes a user prompt and converts it to a crew specification JSON
        """
        available_tools = self.tool_names
        kwargs = self.tool_kwargs

        # Build tool parameter documentation
        tool_params_doc = ""
        for tool_name, tool_kwargs in kwargs.items():
            tool_params_doc += f"\n{tool_name}:\n"
            for param_name, param_value in tool_kwargs.items():
                if isinstance(param_value, list):
                    tool_params_doc += f"  - {param_name}: {', '.join(param_value)}\n"
                else:
                    tool_params_doc += f"  - {param_name}: {param_value}\n"

        system_prompt = f"""
        You are a SpecAgent that converts user requests into CrewAI task specifications.

        AVAILABLE TOOLS: {available_tools}

        TOOL PARAMETERS:
        {tool_params_doc}

        IMPORTANT RULES:
        1. Use ONLY the exact tool names from the available tools list above
        2. For each tool you use, include the appropriate parameters from the tool parameters section
        3. Do not use generic names like 'search' or 'llm' - use the specific tool names

        You have complete flexibility to create as many agents and tasks as needed to accomplish the user's request. 
        Think like a project manager - break down complex requests into logical steps and assign specialized agents.
        
        Generate a JSON specification with this structure:
        {{
            "agents": [
                {{
                    "name": "agent_name",
                    "tools": ["tool_name"],
                    "role_description": "Detailed description of what this agent specializes in"
                }}
            ],
            "tasks": [
                {{
                    "name": "unique_task_name",
                    "agent": "agent_name",
                    "description": "Clear task description",
                    "expected_output": "What the task should produce",
                    "tool_params": [
                        {{
                            "tool": "tool_name",
                            "param1": "value1",
                            "param2": "value2"
                        }}
                    ]
                }}
            ]
        }}
        
        HOW CREWAI TOOLS WORK:
        - CrewAI calls the tool's _run method with ALL parameters as keyword arguments
        - The first parameter is typically the action/operation (like "send_message" for slack_tool)
        - Additional parameters are passed as kwargs to the _run method
        - Example: slack_tool._run(action="send_message", channel="#general", message="Hello")
        
        CRITICAL: Generate ACTUAL parameter values based on the user's request. NEVER use placeholders like "Your message here", "selected_channel", "#selected_channel", or any generic terms. Use real, specific values that make sense for the specific task. 
        
        Agent Specialization Guidelines:
        - Create specialized agents for different domains (research, analysis, writing, coding, presentation creation, etc.)
        - Consider agent expertise and tool compatibility
        - Use descriptive names that indicate the agent's role

        IMPORTANT TOOL USAGE ORDER:
        - You MUST always call "slack_list_channels_tool" before "slack_resolve_channel_tool" in a workflow, unless you are certain the channel list is already cached in context.
        - Example correct sequence:
            1. Use slack_list_channels_tool to cache channels.
            2. Use slack_resolve_channel_tool to resolve a channel name to an ID and store it with an alias.
            3. Use slack_send_message_tool to send a message using the resolved alias.
        
        TOOL PARAMETER EXAMPLES:
        - slack_list_channels_tool: {{"tool": "slack_list_channels_tool"}}
        - slack_resolve_channel_tool: {{"tool": "slack_resolve_channel_tool", "name_or_topic": "general", "alias": "main_channel"}}
        - slack_send_message_tool: {{"tool": "slack_send_message_tool", "channel_ref": "main_channel", "message": "Your message here"}}
        - serper_dev_tool: {{"tool": "serper_dev_tool", "query": "search query", "limit": 10}}
        
        CRITICAL: The "alias" parameter in slack_resolve_channel_tool creates a reference that MUST be used in the "channel_ref" parameter of slack_send_message_tool. Do NOT use the original channel name or ID in slack_send_message_tool - use the alias!
        
        CRITICAL ALIAS REQUIREMENT: When using slack_resolve_channel_tool, you MUST provide a meaningful alias that describes the channel's purpose. Examples:
        - For a general channel: alias="general_channel"
        - For an announcements channel: alias="announcements"
        - For a team channel: alias="team_channel"
        - For a project channel: alias="project_channel"
        
        NEVER use empty aliases or generic names like "channel" or "selected_channel". The alias must be descriptive and unique.
        
        When using tools, always include the required parameters in tool_params based on the tool parameters documentation above.
        Respond with valid JSON only.
        """
        
        try:
            # Use fallback if no OpenAI client
            if not self.client:
                return self._get_fallback_spec(prompt)
                
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Convert this prompt to a crew specification: {prompt}"}
                ],
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            if content is None:
                return self._get_fallback_spec(prompt)
            crew_spec = json.loads(content)

            print('CREW SPEC', content)
            print('========================================')
            
            # Validate the structure
            if "tasks" not in crew_spec:
                raise ValueError("Invalid crew specification: missing 'tasks' field")
            
            # Fix any incorrect tool names
            crew_spec = self._fix_tool_names(crew_spec)
            
            return crew_spec
            
        except json.JSONDecodeError as e:
            # Fallback to a default specification if LLM fails
            return self._get_fallback_spec(prompt)
        except Exception as e:
            # Fallback to a default specification if LLM fails
            return self._get_fallback_spec(prompt)
    
    def _get_fallback_spec(self, prompt: str) -> Dict[str, Any]:
        """
        Fallback specification when LLM fails
        """
        return {
            "agents": [
                {
                    "name": "researcher",
                    "config_key": "researcher", 
                    "tools": ["serper_dev_tool"],
                    "role_description": "Research specialist for gathering information"
                },
            ],
            "tasks": [
                {
                    "name": "researchTask",
                    "agent": "researcher",
                    "description": f"Research and gather information about: {prompt}",
                    "expected_output": "A comprehensive list of relevant information",
                    "tool_params": [
                        {
                            "tool": "serper_dev_tool",
                            "query": f"information about {prompt}",
                            "limit": 10
                        }
                    ]
                }
            ]
        }
    
    def _fix_tool_names(self, crew_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Fix any incorrect tool names to match our registry"""
        tool_mapping = {
            'search': 'serper_dev_tool',
            'web_search': 'serper_dev_tool', 
            'llm': 'website_search_tool',
            'sentiment': 'website_search_tool',
            'summarize': 'website_search_tool',
            'image': 'dalle_tool',
            'image_generation': 'dalle_tool',
            'dalle': 'dalle_tool',
            'dall-e': 'dalle_tool',
            'generate_image': 'dalle_tool',
            'create_image': 'dalle_tool',
            'slides': 'google_slides_tool',
            'presentation': 'google_slides_tool',
            'google_slides': 'google_slides_tool',
            'powerpoint': 'google_slides_tool',
            # Remove incorrect Slack mappings - let the individual tools be used as-is
        }
        
        # Fix agent tool names
        for agent in crew_spec.get('agents', []):
            if 'tools' in agent:
                agent['tools'] = [tool_mapping.get(tool, tool) for tool in agent['tools']]
                # Remove any tools not in our registry
                agent['tools'] = [tool for tool in agent['tools'] if tool in self.tool_names]
        
        return crew_spec