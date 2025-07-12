#!/usr/bin/env python3
"""
Generated Crew File - Created on 2025-07-12 16:15:48

This file was automatically generated from a JSON specification.
It contains all the agents, tasks, and crew configuration needed to run the crew.

Usage:
    python generated_crew.py
"""


from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Tool imports
from tools.tool_registry import instantiate_tool


@CrewBase
class GeneratedCrew:
    """Generated crew from JSON specification"""


    @agent
    def researcher(self) -> Agent:
        """Generated agent: researcher"""

        tools = [
            instantiate_tool("website_search_tool"),
        ]
        
        return Agent(
            role="Research AI trends in 2024 Senior Data Researcher",
            goal="Uncover cutting-edge developments in Research AI trends in 2024",
            backstory="Research AI trends in 2024 Senior Data Researcher  - Uncover cutting-edge developments in Research AI trends in 2024",
            tools=tools,
            verbose=True
        )


    @task
    def researcher_task(self) -> Task:
        """Generated task for researcher"""
        return Task(
            description="Conduct a thorough research about Research AI trends in 2024. Make sure you find any interesting and relevant information given the current year is 2024. Focus on recent developments, key trends, and significant breakthroughs. Analyze multiple reliable sources and cross-reference information for accuracy. Pay special attention to credible sources and up-to-date information.",
            expected_output="A comprehensive list with 10 bullet points of the most relevant information about Research AI trends in 2024. Each bullet point should include specific details, sources, and dates where applicable. Organize the information from most important to least important.",
            agent=self.researcher(),
        )


    @crew
    def crew(self) -> Crew:
        """Creates the generated crew"""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,    # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )


if __name__ == "__main__":
    # Initialize and run the crew
    crew_instance = GeneratedCrew()
    
    print("🚀 Starting Generated Crew...")
    print("=" * 50)
    
    # # Show crew info
    # print(f"Agents: {len(crew_instance.agents)}")
    # print(f"Tasks: {len(crew_instance.tasks)}")
    # print()
    
    # Execute the crew
    try:
        result = crew_instance.crew().kickoff()
        print("✅ Crew execution completed!")
        print("=" * 50)
        print("RESULT:")
        print(result)
    except Exception as e:
        print(f"❌ Error executing crew: {e}")
        import traceback
        traceback.print_exc()
