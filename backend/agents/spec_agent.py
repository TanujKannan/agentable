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
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.tool_names = get_tool_names()
    
    async def generate_crew_spec(self, prompt: str) -> Dict[str, Any]:
        """
        Takes a user prompt and converts it to a crew specification JSON
        """
        system_prompt = """
        You are a SpecAgent that converts user requests into CrewAI task specifications.

        You have access to the following tools: {self.tool_names}
        
        Given a user prompt, generate a JSON specification with the following structure:
        {
            "agents": [
                {
                    "name": "researcher", 
                    "config_key": "researcher",
                    "tools": ["tool_name", "tool_name"],
                    "role_description": "Research specialist for gathering information"
                },
                {
                    "name": "analyst",
                    "config_key": "reporting_analyst", 
                    "tools": ["tool_name", "tool_name"],
                    "role_description": "Analyzes and synthesizes research findings"
                }
            ],
          "tasks": [
            {
              "id": "unique_task_id",
              "agent": "AgentType",
              "description": "Clear task description with variables like {prompt}",
              "expected_output": "What the task should produce",
              "params": {
                "tool": "tool_name",
                "limit": 50,
                "method": "method_name",
                "model": "model_name"
              }
            }
          ]
        }
        
        Common agent types:
        - DataAgent: For fetching/searching data
        - AnalysisAgent: For analyzing data (sentiment, summarization, etc.)
        - ResearchAgent: For research tasks
        - WritingAgent: For content generation
        
        Common tools:
        - search: For web/data searching
        - llm: For LLM-based analysis
        - sentiment: For sentiment analysis
        - summarize: For text summarization
        
        Always include relevant parameters in the params object.
        Respond with valid JSON only.
        """
        
        try:
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
            
            # Validate the structure
            if "tasks" not in crew_spec:
                raise ValueError("Invalid crew specification: missing 'tasks' field")
            
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
            "tasks": [
                {
                    "id": "researchTask",
                    "agent": "DataAgent",
                    "description": f"Research and gather information about: {prompt}",
                    "expected_output": "A comprehensive list of relevant information",
                    "params": {
                        "tool": "website_search_tool",
                        "limit": 10
                    }
                },
                {
                    "id": "analysisTask", 
                    "agent": "AnalysisAgent",
                    "description": f"Analyze the research findings for: {prompt}",
                    "expected_output": "A detailed analysis and summary",
                    "params": {
                        "method": "summarize",
                        "model": "gpt-3.5-turbo"
                    }
                }
            ]
        }