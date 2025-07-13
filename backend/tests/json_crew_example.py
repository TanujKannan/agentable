#!/usr/bin/env python
"""
json_crew_example.py

Demonstration of how to construct and execute a CrewAI crew starting from a JSON
string – for instance, the structured output of an LLM prompt.

Run it with:

    python -m agentable_backend.json_crew_example

or from the project root:

    poetry run python -m agentable_backend.json_crew_example

Prerequisites:
1. `crewai` installed (already listed in pyproject.toml)
2. An `OPENAI_API_KEY` (or other model provider) exported in your environment so
   CrewAI can access an LLM when agents perform their tasks.
"""

import json
from typing import List, Dict, Type

from crewai import Agent, Crew, Task


TOOL_REGISTRY: Dict[str, Type] = {
    # "WebSearch": WebsiteSearchTool,  # Uncomment when crewai_tools is available
}

OUTPUT_JSON = """
{
  "agents": [
    {
      "role": "Researcher",
      "goal": "Research x",
      "backstory": "An experienced domain expert focused on gathering factual information.",
      "tools": ["WebSearch"]
    }
  ],
  "tasks": [  
    {
      "description": "Search website for sf events today",
      "agent": "Researcher"
    }
  ]
}
"""


def _instantiate_tools(tool_names: List[str]):
    """Instantiate tools listed in *tool_names* using TOOL_REGISTRY."""
    tools = []
    for name in tool_names:
        tool_cls = TOOL_REGISTRY.get(name)
        if tool_cls is None:
            raise ValueError(
                f"Tool '{name}' is not registered. Add it to TOOL_REGISTRY to use it."
            )
        tools.append(tool_cls())
    return tools


def build_crew_from_json(json_spec: str) -> Crew:
    """Create Agent, Task, and Crew instances from a JSON definition."""

    data = json.loads(json_spec)

    agents: List[Agent] = []

    for agent_cfg in data["agents"]:
        tool_names = agent_cfg.pop("tools", [])
        tools = _instantiate_tools(tool_names)

        # Create the Agent with the resolved tools.
        agents.append(Agent(**agent_cfg, tools=tools))

    agent_by_role = {agent.role: agent for agent in agents}

    tasks: List[Task] = []
    for task_cfg in data["tasks"]:
        tasks.append(
            Task(
                agent=agent_by_role[task_cfg["agent"]],
                description=task_cfg["description"],
                expected_output="A concise answer to the task question."
            )
        )

    crew = Crew(agents=agents, tasks=tasks, verbose=True)  # type: ignore
    return crew


def main():
    crew = build_crew_from_json(OUTPUT_JSON)
    result = crew.kickoff()
    print("\n=== Crew result ===")
    print(result)


if __name__ == "__main__":
    main() 