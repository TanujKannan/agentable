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

# ---------------------------------------------------------------------------
# Import available tools here and register them so JSON can reference them by
# name.  New tools can simply be added to this registry.
# ---------------------------------------------------------------------------
# Note: crewai_tools not available, using empty registry for now
# from crewai_tools import WebsiteSearchTool

# A simple registry mapping a string identifier (as it will appear in JSON)
# to the corresponding BaseTool **class** (not instance).  When an agent
# definition references a tool we will instantiate it on-the-fly.

TOOL_REGISTRY: Dict[str, Type] = {
    # "WebSearch": WebsiteSearchTool,  # Uncomment when crewai_tools is available
}


# ---------------------------------------------------------------------------
# Example JSON specification – in practice this would come from your LLM.
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

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

    # 1. Instantiate agents ---------------------------------------------------
    agents: List[Agent] = []

    for agent_cfg in data["agents"]:
        # Extract optional list of tool names (strings). Instantiate them using
        # the TOOL_REGISTRY so the agent has live tool instances.
        tool_names = agent_cfg.pop("tools", [])
        tools = _instantiate_tools(tool_names)

        # Create the Agent with the resolved tools.
        agents.append(Agent(**agent_cfg, tools=tools))

    # 2. Create a look-up map so tasks can reference agents by role ------------
    agent_by_role = {agent.role: agent for agent in agents}

    # 3. Instantiate tasks ----------------------------------------------------
    tasks: List[Task] = []
    for task_cfg in data["tasks"]:
        tasks.append(
            Task(
                agent=agent_by_role[task_cfg["agent"]],
                description=task_cfg["description"],
                expected_output="A concise answer to the task question."
            )
        )

    # 4. Bundle everything into a Crew ---------------------------------------
    crew = Crew(agents=agents, tasks=tasks, verbose=True)  # type: ignore
    return crew


def main():
    crew = build_crew_from_json(OUTPUT_JSON)
    # `kickoff` returns the aggregated output of the tasks.
    result = crew.kickoff()
    print("\n=== Crew result ===")
    print(result)


if __name__ == "__main__":
    main() 