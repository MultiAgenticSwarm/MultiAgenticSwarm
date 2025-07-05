#!/usr/bin/env python3
"""
Simple MultiAgenticSwarm Example
This demonstrates the basic usage patterns of MultiAgenticSwarm.
"""

import multiagenticswarm as mas


def main():
    """Simple demonstration of MultiAgenticSwarm."""
    print("🚀 Simple MultiAgenticSwarm Example")
    print("=" * 40)
    
    # Create two agents with different LLMs
    researcher = mas.Agent(
        name="Researcher",
        system_prompt="You are a research assistant who gathers and analyzes information.",
        llm_provider="openai",
        llm_model="gpt-4"
    )
    
    writer = mas.Agent(
        name="Writer", 
        system_prompt="You are a content writer who creates engaging articles.",
        llm_provider="anthropic",
        llm_model="claude-3.5-sonnet"
    )
    
    # Define tool functions
    def research_topic(topic: str) -> str:
        """Research a topic and return key information."""
        return f"Research findings for '{topic}': Key insights, statistics, and trends discovered."
    
    def write_article(research_data: str) -> str:
        """Write an article based on research data."""
        return f"Article created based on: {research_data}"
    
    def review_content(content: str) -> str:
        """Review content for quality."""
        return f"Content reviewed and approved: {content[:50]}..."
    
    # Create tools with different sharing levels
    research_tool = mas.Tool(
        name="ResearchTool",
        func=research_topic,
        description="Conducts research on specified topics"
    )
    research_tool.set_local(researcher)  # Only researcher can use this
    
    writing_tool = mas.Tool(
        name="WritingTool", 
        func=write_article,
        description="Writes articles based on research"
    )
    writing_tool.set_shared(researcher, writer)  # Both can use this
    
    review_tool = mas.Tool(
        name="ReviewTool",
        func=review_content,
        description="Reviews content for quality and accuracy"
    )
    review_tool.set_global()  # Available to all agents
    
    # Create a collaborative task
    article_task = mas.Task(
        name="CreateArticle",
        description="Research and write an article on a topic",
        steps=[
            {"agent": "Researcher", "tool": "ResearchTool", "input": "artificial intelligence trends"},
            {"agent": "Writer", "tool": "WritingTool", "input": "research findings"},
            {"agent": "Writer", "tool": "ReviewTool", "input": "final article"}
        ]
    )
    
    # Set up the system
    system = mas.System(enable_logging=True)
    system.register_agents(researcher, writer)
    system.register_tools(research_tool, writing_tool, review_tool)
    system.register_tasks(article_task)
    
    # Execute the task
    print("\n📝 Executing article creation task...")
    try:
        result = system.execute_task("CreateArticle")
        print(f"✅ Task completed successfully!")
        print(f"📄 Result: {result}")
    except Exception as e:
        print(f"❌ Task failed: {e}")
    
    print("\n🎉 Example completed!")
    return system


if __name__ == "__main__":
    main()
