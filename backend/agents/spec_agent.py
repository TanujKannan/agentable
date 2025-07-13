import json
from typing import Dict, Any
import openai
import os
import weave

from tools.tool_registry import get_tool_names, instantiate_tool

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
        - Simple searches for information (use serper_dev_tool)
        - General research questions (use serper_dev_tool)
        - Finding facts, definitions, or explanations (use serper_dev_tool)
        - Basic information gathering (use serper_dev_tool)
        - When user just wants to know "what is..." or "how to..." (use serper_dev_tool)
        
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
                    "tools": ["serper_dev_tool", "website_search_tool"],
                    "role_description": "Research specialist for gathering information"
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
              "id": "unique_task_id",
              "agent": "agent_name",
              "description": "Clear task description with variables like {{prompt}}",
              "expected_output": "What the task should produce",
              "params": {{
                "tool": "serper_dev_tool",
                "limit": 50,
                "method": "search",
                "model": "n/a"
              }}
            }}
          ]
        }}
        
        Common agent types:
        - DataAgent: For fetching/searching data
        - AnalysisAgent: For analyzing data (sentiment, summarization, etc.)
        - ResearchAgent: For research tasks
        - WritingAgent: For content generation
        - ImageAgent: For image generation using DALL-E
        - WebNavigationAgent: For browsing websites and interacting with web applications
        
        Always include relevant parameters in the params object.
        Respond with valid JSON only.
        """
        
        try:
            # Use fallback if no OpenAI client
            if not self.client:
                return self._get_fallback_spec(prompt)
                
            response = self.client.chat.completions.create(
                model="o4-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Convert this prompt to a crew specification: {prompt}"}
                ],
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            crew_spec = json.loads(content)

            print('CREW SPEC', crew_spec)
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
                    "tools": ["serper_dev_tool"],
                    "role_description": "Research specialist for gathering information"
                },
                {
                    "name": "web_navigator",
                    "config_key": "web_navigator",
                    "tools": ["browserbase_tool"],
                    "role_description": "Web navigation specialist for browsing websites, interacting with web applications, and extracting content from complex pages that require JavaScript rendering"
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
                    "id": "researchTask",
                    "agent": "researcher",
                    "description": f"Research and gather information about: {prompt}",
                    "expected_output": "A comprehensive list of relevant information",
                    "params": {
                        "tool": "serper_dev_tool",
                        "limit": 10
                    }
                },
                {
                    "id": "analysisTask", 
                    "agent": "analyst",
                    "description": f"Analyze the research findings for: {prompt}",
                    "expected_output": "A detailed analysis and summary",
                    "params": {
                        "method": "summarize",
                        "model": "gpt-3.5-turbo"
                    }
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