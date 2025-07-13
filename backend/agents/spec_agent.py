import json
from typing import Dict, Any
import openai
import os
import weave

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
    
    @weave.op()
    async def generate_crew_spec(self, prompt: str) -> Dict[str, Any]:
        """
        Takes a user prompt and converts it to a crew specification JSON
        """
        # Add weave attributes for better tracing - disabled
        # with weave.attributes({
        #     'prompt_length': len(prompt),
        #     'available_tools': self.tool_names,
        #     'has_openai_client': self.client is not None
        # }):
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

        You only have access to the following tools: {available_tools}
        
        IMPORTANT: You must use the EXACT tool names from the list above. Do not use generic names like 'search' or 'llm'.
        
        Tool Usage Guidelines:
        - Use "serper_dev_tool" for web search and research (general searches, finding information)
        - Use "website_search_tool" for website content search
        - Use "code_docs_search_tool" for code documentation search
        - Use "dalle_tool" for image generation tasks
        - Use "browserbase_tool" for web navigation and interaction (when user wants to browse a specific website, navigate through pages, or interact with complex web applications)
        - Use "exa_search_tool" for semantic search across the internet (when you need high-quality, contextually relevant results that understand the meaning behind the query)
        
        - You can use serper_dev_tool to find the URL of the website to browse, then use browserbase_tool to browse the website.

        CRITICAL: When to use Browserbase vs Regular Search:
        
        USE BROWSERBASE TOOLS when:
        - User specifically mentions wanting to "browse", "navigate", or "visit" a website
        - User wants to interact with a web application or fill out forms
        - User needs to access content that requires JavaScript or complex rendering
        - User wants to perform actions like clicking, scrolling, or taking screenshots
        - User mentions specific websites they want to navigate through
        - Task involves booking, purchasing, or multi-step web interactions
        - User wants to extract content from dynamically loaded pages
        
        DO NOT USE BROWSERBASE TOOLS for:
        - Simple searches for information (use serper_dev_tool or exa_search_tool)
        - General research questions (use serper_dev_tool or exa_search_tool)
        - Finding facts, definitions, or explanations (use serper_dev_tool or exa_search_tool)
        - Basic information gathering (use serper_dev_tool or exa_search_tool)
        - When user just wants to know "what is..." or "how to..." (use serper_dev_tool or exa_search_tool)
        
        WHEN TO USE EXA SEARCH TOOL:
        - Use "exa_search_tool" when you need semantic, contextually-aware search results
        - Best for research that requires understanding the meaning and context behind queries
        - Ideal for finding high-quality, relevant content that matches the intent of the search
        - Use when you need more sophisticated search capabilities than basic keyword matching
        - Perfect for academic research, technical documentation, or when search quality is crucial
        - Use when "serper_dev_tool" might return too many irrelevant results
        
        PREFERENCE ORDER FOR SEARCH TOOLS:
        1. Use "exa_search_tool" for high-quality, semantic search when search quality is important
        2. Use "serper_dev_tool" for general web search and when you need comprehensive results
        3. Use "website_search_tool" for searching within specific website content
        - Simple searches for information (use serper_dev_tool)
        - General research questions (use serper_dev_tool)
        - Finding facts, definitions, or explanations (use serper_dev_tool)
        - Basic information gathering (use serper_dev_tool)
        - When user just wants to know "what is..." or "how to..." (use serper_dev_tool)
        - Large e-commerce sites that may return massive HTML content (prefer serper_dev_tool for product information)
        
        IMPORTANT: When using browserbase_tool, be specific about the target URL and avoid generic browsing tasks that might result in large HTML pages. Focus on targeted content extraction rather than general website browsing.
        
        CRITICAL TOOL USAGE: For image generation tasks using dalle_tool:
        - The parameter name MUST be 'image_description' (NOT 'description')
        - Pass the description as a DIRECT STRING value, NOT a dictionary
        - Correct format: dalle_tool(image_description="A beautiful sunset over mountains")
        - WRONG format: Do NOT pass dictionary objects to the tool
        
        Example of correct usage: dalle_tool(image_description="A monkey hanging from a tree branch")
        
        Given a user prompt, generate a JSON specification with the following structure:
        {{
            "agents": [
                {{
                    "name": "researcher", 
                    "config_key": "researcher",
                    "tools": ["exa_search_tool", "serper_dev_tool", "website_search_tool"],
                    "role_description": "Research specialist for gathering high-quality, contextually relevant information using semantic search"
                }},
                {{
                    "name": "semantic_researcher",
                    "config_key": "semantic_researcher",
                    "tools": ["exa_search_tool"],
                    "role_description": "Semantic search specialist for finding high-quality, contextually relevant content across the internet using advanced search capabilities"
                }},
                {{
                    "name": "web_navigator",
                    "config_key": "web_navigator",
                    "tools": ["browserbase_tool"],
                    "role_description": "Web navigation specialist for browsing websites, interacting with web applications, and extracting content from complex pages that require JavaScript rendering"
                }},
                {{
                    "name": "image_creator",
                    "config_key": "image_creator",
                    "tools": ["dalle_tool"],
                    "role_description": "Creates images from textual descriptions using DALL-E. CRITICAL: Call dalle_tool with direct string parameter: dalle_tool(image_description='description text'). Do NOT pass dictionaries or objects."
                }},
                {{
                    "name": "analyst",
                    "config_key": "reporting_analyst", 
                    "tools": [],
                    "role_description": "Analyzes and synthesizes research findings"
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
        
        CRITICAL: Generate ACTUAL parameter values based on the user's request. NEVER use placeholders like "Your message here", "selected_channel", "#selected_channel", "[insert findings here]", or any generic terms. Use real, specific values that make sense for the specific task. 
        
        For Slack messages: Write the actual message content the agent should send, like "Here are the research findings on basketball: [research results from previous task]" - this tells the agent to include the research results from the previous task. 
        
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
                print('NO OPENAI CLIENT')
                return self._get_fallback_spec(prompt)
                
            print("Making OpenAI API call...")
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Convert this prompt to a crew specification: {prompt}"}
                ],
            )
            
            content = response.choices[0].message.content
            print(f"Raw API response: {content}")
            
            if content.startswith('```json'):
                content = content[7:] 
            if content.startswith('```'):
                content = content[3:]  
            if content.endswith('```'):
                content = content[:-3]  
            content = content.strip()
            
            print(f"Cleaned content: {content}")
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
            print(f"JSON DECODE ERROR: {e}")
            print(f"Raw content: {content}")
            # Fallback to a default specification if LLM fails
            return self._get_fallback_spec(prompt)
        except Exception as e:
            print(f"GENERAL EXCEPTION: {e}")
            # Fallback to a default specification if LLM fails
            return self._get_fallback_spec(prompt)
    
    # @weave.op()  # Disabled due to serialization issues
    def _get_fallback_spec(self, prompt: str) -> Dict[str, Any]:
        """
        Fallback specification when LLM fails
        """
        # with weave.attributes({'fallback_reason': 'LLM_unavailable_or_failed'}):
        return {
            "agents": [
                {
                    "name": "researcher",
                    "config_key": "researcher", 
                    "tools": ["exa_search_tool", "serper_dev_tool"],
                    "role_description": "Research specialist for gathering high-quality, contextually relevant information"
                },
                {
                    "name": "web_navigator",
                    "config_key": "web_navigator",
                    "tools": ["browserbase_tool"],
                    "role_description": "Web navigation specialist for browsing specific websites, interacting with web applications, and extracting targeted content from pages that require JavaScript rendering. Focuses on targeted content extraction rather than general website browsing to avoid context length issues."
                },
                {
                    "name": "image_creator",
                    "config_key": "image_creator",
                    "tools": ["dalle_tool"],
                    "role_description": "Creates images from textual descriptions using DALL-E. CRITICAL: Call dalle_tool with direct string parameter: dalle_tool(image_description='description text'). Do NOT pass dictionaries or objects."
                },
                {
                    "name": "analyst",
                    "config_key": "analyst",
                    "tools": [],
                    "role_description": "Analyzes and synthesizes research findings"
                }
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
                },
                {
                    "name": "analysisTask", 
                    "agent": "analyst",
                    "description": f"Analyze the research findings for: {prompt}",
                    "expected_output": "A detailed analysis and summary",
                    "tool_params": []
                }
            ]
        }
    
    # @weave.op()  # Disabled due to serialization issues
    def _fix_tool_names(self, crew_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Fix any incorrect tool names to match our registry"""
        # with weave.attributes({
        #     'agent_count': len(crew_spec.get('agents', [])),
        #     'task_count': len(crew_spec.get('tasks', []))
        # }):
        tool_mapping = {
            'search': 'exa_search_tool',  # Default to EXA for better search quality
            'web_search': 'exa_search_tool', 
            'semantic_search': 'exa_search_tool',
            'exa': 'exa_search_tool',
            'research': 'exa_search_tool',
            'find': 'exa_search_tool',
            'lookup': 'exa_search_tool',
            'serper': 'serper_dev_tool',
            'google_search': 'serper_dev_tool',
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
            'browser': 'browserbase_tool',
            'browse': 'browserbase_tool',
            'navigate': 'browserbase_tool',
            'browserbase': 'browserbase_tool',
            'web_navigation': 'browserbase_tool',
            'web_browse': 'browserbase_tool',
            'click': 'browserbase_tool',
            'interact': 'browserbase_tool',
            'form_fill': 'browserbase_tool',
            'screenshot': 'browserbase_tool',
        }
        
        # Fix agent tool names
        for agent in crew_spec.get('agents', []):
            if 'tools' in agent:
                agent['tools'] = [tool_mapping.get(tool, tool) for tool in agent['tools']]
                # Remove any tools not in our registry
                agent['tools'] = [tool for tool in agent['tools'] if tool in self.tool_names]
        
        return crew_spec