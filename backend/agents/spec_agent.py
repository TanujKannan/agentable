import json
from typing import Dict, Any
import openai
import os

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
    
    async def generate_crew_spec(self, prompt: str) -> Dict[str, Any]:
        """
        Takes a user prompt and converts it to a crew specification JSON
        """
        available_tools = self.tool_names
        system_prompt = f"""
        You are a SpecAgent that converts user requests into CrewAI task specifications.

        You only have access to the following tools: {available_tools}
        
        IMPORTANT: You must use the EXACT tool names from the list above. Do not use generic names like 'search' or 'llm'.
        
        Tool Usage Guidelines:
        - Use "serper_dev_tool" for web search and research
        - Use "website_search_tool" for website content search
        - Use "code_docs_search_tool" for code documentation search
        - Use "dalle_tool" for image generation tasks
        
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
        
        Always include relevant parameters in the params object.
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
        }
        
        # Fix agent tool names
        for agent in crew_spec.get('agents', []):
            if 'tools' in agent:
                agent['tools'] = [tool_mapping.get(tool, tool) for tool in agent['tools']]
                # Remove any tools not in our registry
                agent['tools'] = [tool for tool in agent['tools'] if tool in self.tool_names]
        
        return crew_spec