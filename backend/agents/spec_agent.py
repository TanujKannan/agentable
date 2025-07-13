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
        
        You have complete flexibility to create as many agents and tasks as needed to accomplish the user's request. 
        Think like a project manager - break down complex requests into logical steps and assign specialized agents.
        
        Given a user prompt, generate a JSON specification with the following structure:
        {{
            "agents": [
                {{
                    "name": "agent_name",
                    "tools": ["tool_name", "tool_name"],
                    "role_description": "Detailed description of what this agent specializes in",
                    "config": {{
                        "temperature": 0.7,
                        "max_iterations": 3,
                        "allow_delegation": true
                    }}
                }}
            ],
            "tasks": [
                {{
                    "name": "unique_task_name",
                    "agent": "agent_name",
                    "description": "Clear task description with variables like {{prompt}}",
                    "expected_output": "What the task should produce",
                    "params": {{
                        "tool": "tool_name",
                        "limit": 50,
                        "method": "search",
                        "model": "n/a",
                        "custom_param": "value"
                    }},
                    "dependsOn": ["task_name"],
                    "priority": "high|medium|low",
                    "timeout": 300,
                    "retry_count": 2,
                    "async_execution": true
                }}
            ],
            "workflow": {{
                "parallel_tasks": ["task_name1", "task_name2"],
                "sequential_tasks": ["task_name3", "task_name4"],
                "conditional_tasks": {{
                    "if_task": "task_name4",
                    "condition": "success|failure",
                    "then_tasks": ["task_name5"],
                    "else_tasks": ["task_name6"]
                }}
            }}
        }}
        
        Agent Specialization Guidelines:
        - Create specialized agents for different domains (research, analysis, writing, coding, etc.)
        - Consider agent expertise and tool compatibility
        - Use descriptive names that indicate the agent's role
        
        Task Design Guidelines:
        - Break complex requests into smaller, manageable tasks
        - Use dependencies to create logical workflows
        - For tasks that are long-running or have no downstream dependencies, set "async_execution": true
        - This allows the system to run them in parallel and continue without blocking
        - Tasks that must wait for async tasks should reference them in dependsOn or appear in workflow.sequential_tasks
        - Add appropriate timeouts and retry logic for reliability
        
        Workflow Optimization:
        - Identify tasks that can run in parallel (no dependencies)
        - Create sequential chains for dependent tasks
        - Add conditional logic for error handling and branching
        
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
                    "role_description": "Research specialist for gathering information",
                    "config": {
                        "temperature": 0.7,
                        "max_iterations": 3,
                        "allow_delegation": True
                    }
                },
                {
                    "name": "analyst",
                    "config_key": "analyst",
                    "tools": [],
                    "role_description": "Analyzes and synthesizes research findings",
                    "config": {
                        "temperature": 0.3,
                        "max_iterations": 2,
                        "allow_delegation": False
                    }
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
                    },
                    "priority": "high",
                    "timeout": 300,
                    "retry_count": 2
                },
                {
                    "id": "analysisTask", 
                    "agent": "analyst",
                    "description": f"Analyze the research findings for: {prompt}",
                    "expected_output": "A detailed analysis and summary",
                    "params": {
                        "method": "summarize",
                        "model": "gpt-3.5-turbo"
                    },
                    "dependsOn": ["researchTask"],
                    "priority": "medium",
                    "timeout": 180,
                    "retry_count": 1
                }
            ],
            "workflow": {
                "parallel_tasks": ["researchTask"],
                "sequential_tasks": ["analysisTask"],
                "description": "Research first, then analyze in sequence"
            }
        }
    
    def _get_complex_example_spec(self, prompt: str) -> Dict[str, Any]:
        """
        Example of a complex workflow specification showing the flexibility
        """
        return {
            "agents": [
                {
                    "name": "market_researcher",
                    "tools": ["serper_dev_tool"],
                    "role_description": "Specializes in market research and competitive analysis",
                    "config": {
                        "temperature": 0.5,
                        "max_iterations": 5,
                        "allow_delegation": True
                    }
                },
                {
                    "name": "data_analyst",
                    "tools": ["website_search_tool"],
                    "role_description": "Expert in data analysis and trend identification",
                    "config": {
                        "temperature": 0.2,
                        "max_iterations": 3,
                        "allow_delegation": False
                    }
                },
                {
                    "name": "content_writer",
                    "tools": [],
                    "role_description": "Creates compelling content and reports",
                    "config": {
                        "temperature": 0.8,
                        "max_iterations": 4,
                        "allow_delegation": True
                    }
                },
                {
                    "name": "fact_checker",
                    "tools": ["serper_dev_tool"],
                    "role_description": "Verifies information accuracy and sources",
                    "config": {
                        "temperature": 0.1,
                        "max_iterations": 2,
                        "allow_delegation": False
                    }
                }
            ],
            "tasks": [
                {
                    "id": "market_research",
                    "agent": "market_researcher",
                    "description": f"Conduct comprehensive market research on: {prompt}",
                    "expected_output": "Detailed market analysis with key insights",
                    "params": {
                        "tool": "serper_dev_tool",
                        "limit": 20,
                        "search_depth": "comprehensive"
                    },
                    "priority": "high",
                    "timeout": 600,
                    "retry_count": 2
                },
                {
                    "id": "competitor_analysis",
                    "agent": "market_researcher",
                    "description": f"Analyze competitors in the market for: {prompt}",
                    "expected_output": "Competitive landscape analysis",
                    "params": {
                        "tool": "serper_dev_tool",
                        "limit": 15,
                        "focus": "competitors"
                    },
                    "priority": "high",
                    "timeout": 450,
                    "retry_count": 2
                },
                {
                    "id": "data_processing",
                    "agent": "data_analyst",
                    "description": "Process and analyze the collected market data",
                    "expected_output": "Processed data with key metrics and trends",
                    "params": {
                        "tool": "website_search_tool",
                        "analysis_type": "trend_analysis"
                    },
                    "dependsOn": ["market_research", "competitor_analysis"],
                    "priority": "medium",
                    "timeout": 300,
                    "retry_count": 1
                },
                {
                    "id": "content_creation",
                    "agent": "content_writer",
                    "description": "Create a comprehensive market report",
                    "expected_output": "Professional market report document",
                    "params": {
                        "format": "executive_summary",
                        "length": "comprehensive"
                    },
                    "dependsOn": ["data_processing"],
                    "priority": "medium",
                    "timeout": 400,
                    "retry_count": 1
                },
                {
                    "id": "fact_verification",
                    "agent": "fact_checker",
                    "description": "Verify all facts and sources in the report",
                    "expected_output": "Verified report with source citations",
                    "params": {
                        "tool": "serper_dev_tool",
                        "verification_level": "thorough"
                    },
                    "dependsOn": ["content_creation"],
                    "priority": "low",
                    "timeout": 200,
                    "retry_count": 1
                }
            ],
            "workflow": {
                "parallel_tasks": ["market_research", "competitor_analysis"],
                "sequential_tasks": ["data_processing", "content_creation", "fact_verification"],
                "conditional_tasks": {
                    "if_task": "fact_verification",
                    "condition": "failure",
                    "then_tasks": ["content_creation"],
                    "else_tasks": []
                },
                "description": "Parallel research tasks, then sequential analysis and creation"
            }
        }
    
    def _fix_tool_names(self, crew_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Fix any incorrect tool names to match our registry"""
        tool_mapping = {
            'search': 'serper_dev_tool',
            'web_search': 'serper_dev_tool', 
            'llm': 'website_search_tool',
            'sentiment': 'website_search_tool',
            'summarize': 'website_search_tool',
        }
        
        # Fix agent tool names
        for agent in crew_spec.get('agents', []):
            if 'tools' in agent:
                agent['tools'] = [tool_mapping.get(tool, tool) for tool in agent['tools']]
                # Remove any tools not in our registry
                agent['tools'] = [tool for tool in agent['tools'] if tool in self.tool_names]
        
        return crew_spec