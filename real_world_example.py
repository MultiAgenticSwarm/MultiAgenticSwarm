#!/usr/bin/env python3
"""
Real-World MultiAgenticSwarm Example: Content Creation Pipeline
This demonstrates how to use MultiAgenticSwarm for a realistic content creation workflow.
"""

import multiagenticswarm as mas
import json
import os
from datetime import datetime
from typing import Dict, List, Any


def main():
    """Real-world content creation pipeline using MultiAgenticSwarm."""
    print("🚀 Real-World Example: Content Creation Pipeline")
    print("=" * 60)
    
    # Set up comprehensive logging
    mas.setup_logging(verbose=True, log_directory="./content_pipeline_logs")
    logger = mas.get_logger("content_pipeline")
    
    # 1. Create specialized agents for content creation
    print("\n👥 Creating specialized content creation agents...")
    
    researcher = mas.Agent(
        name="ContentResearcher",
        system_prompt="""You are an expert content researcher who:
        - Conducts thorough research on topics
        - Finds credible sources and statistics  
        - Identifies trending keywords and topics
        - Analyzes competitor content strategies
        - Provides comprehensive research briefs""",
        llm_provider="openai",
        llm_model="gpt-4",
        temperature=0.3
    )
    
    writer = mas.Agent(
        name="ContentWriter", 
        system_prompt="""You are a professional content writer who:
        - Creates engaging, high-quality content
        - Adapts tone and style for different audiences
        - Incorporates SEO best practices
        - Writes compelling headlines and introductions
        - Ensures content flow and readability""",
        llm_provider="anthropic",
        llm_model="claude-3.5-sonnet",
        temperature=0.7
    )
    
    editor = mas.Agent(
        name="ContentEditor",
        system_prompt="""You are a meticulous content editor who:
        - Reviews content for clarity and coherence
        - Checks grammar, spelling, and style
        - Ensures brand voice consistency
        - Verifies factual accuracy
        - Optimizes content for engagement""",
        llm_provider="openai",
        llm_model="gpt-3.5-turbo",
        temperature=0.2
    )
    
    seo_specialist = mas.Agent(
        name="SEOSpecialist",
        system_prompt="""You are an SEO specialist who:
        - Optimizes content for search engines
        - Identifies relevant keywords and phrases
        - Ensures proper meta descriptions and titles
        - Analyzes content for SEO best practices
        - Provides recommendations for better ranking""",
        llm_provider="openai",
        llm_model="gpt-4",
        temperature=0.4
    )
    
    # 2. Define realistic tool functions
    print("\n🔧 Setting up content creation tools...")
    
    def research_topic(topic: str, target_audience: str = "general") -> Dict[str, Any]:
        """Research a topic thoroughly"""
        # Simulate research results
        research_data = {
            "topic": topic,
            "target_audience": target_audience,
            "key_points": [
                f"Key insight about {topic}",
                f"Market trend related to {topic}",
                f"User behavior regarding {topic}"
            ],
            "statistics": {
                "market_size": "Growing by 15% annually",
                "user_engagement": "High interest in {topic}",
                "competition_level": "Moderate"
            },
            "sources": [
                "Industry Report 2024",
                "Research Study by XYZ",
                "Market Analysis by ABC"
            ],
            "trending_keywords": [
                f"{topic} trends",
                f"best {topic}",
                f"{topic} guide"
            ]
        }
        logger.info(f"Research completed for topic: {topic}")
        return research_data
    
    def generate_content_outline(research_data: Dict[str, Any], content_type: str = "blog") -> Dict[str, Any]:
        """Generate a structured content outline"""
        outline = {
            "title": f"Complete Guide to {research_data['topic']}",
            "meta_description": f"Learn everything about {research_data['topic']} with our comprehensive guide",
            "structure": {
                "introduction": "Hook readers with compelling opening",
                "main_sections": [
                    f"Understanding {research_data['topic']}",
                    f"Benefits of {research_data['topic']}",
                    f"Best Practices for {research_data['topic']}",
                    f"Common Mistakes to Avoid",
                    "Conclusion and Next Steps"
                ],
                "call_to_action": "Encourage engagement or conversion"
            },
            "target_length": "2000-2500 words",
            "tone": "informative yet engaging",
            "keywords": research_data.get("trending_keywords", [])
        }
        logger.info(f"Content outline generated for: {research_data['topic']}")
        return outline
    
    def write_content(outline: Dict[str, Any]) -> Dict[str, Any]:
        """Write full content based on outline"""
        content = {
            "title": outline["title"],
            "meta_description": outline["meta_description"],
            "content": f"""
# {outline["title"]}

## Introduction
{outline["structure"]["introduction"]}

## {outline["structure"]["main_sections"][0]}
Comprehensive content about the topic based on research...

## {outline["structure"]["main_sections"][1]} 
Detailed explanation of benefits and advantages...

## {outline["structure"]["main_sections"][2]}
Practical tips and best practices for implementation...

## {outline["structure"]["main_sections"][3]}
Common pitfalls and how to avoid them...

## Conclusion
{outline["structure"]["call_to_action"]}
            """,
            "word_count": 2250,
            "keywords_used": outline.get("keywords", []),
            "creation_date": datetime.now().isoformat()
        }
        logger.info(f"Content written: {outline['title']}")
        return content
    
    def edit_content(content: Dict[str, Any]) -> Dict[str, Any]:
        """Edit and improve content"""
        edited_content = content.copy()
        edited_content["editing_notes"] = [
            "Improved readability and flow",
            "Enhanced introduction for better engagement",
            "Added transitions between sections",
            "Corrected grammar and spelling",
            "Strengthened conclusion"
        ]
        edited_content["status"] = "edited"
        edited_content["editor_approval"] = True
        logger.info(f"Content edited: {content['title']}")
        return edited_content
    
    def optimize_for_seo(content: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize content for SEO"""
        seo_optimized = content.copy()
        seo_optimized["seo_optimization"] = {
            "title_optimized": True,
            "meta_description_optimized": True,
            "keywords_density": "2.5%",
            "headings_optimized": True,
            "internal_links": 3,
            "external_links": 5,
            "alt_text_added": True,
            "schema_markup": "article"
        }
        seo_optimized["seo_score"] = 92
        seo_optimized["status"] = "seo_optimized"
        logger.info(f"SEO optimization completed: {content['title']}")
        return seo_optimized
    
    def publish_content(content: Dict[str, Any], platform: str = "website") -> Dict[str, Any]:
        """Publish content to specified platform"""
        publication_result = {
            "content_id": f"content_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "platform": platform,
            "status": "published",
            "publication_date": datetime.now().isoformat(),
            "url": f"https://example.com/content/{content['title'].lower().replace(' ', '-')}",
            "estimated_reach": 5000,
            "content": content
        }
        logger.info(f"Content published on {platform}: {content['title']}")
        return publication_result
    
    # 3. Create tools with appropriate sharing levels
    print("\n🛠️ Configuring tool sharing hierarchy...")
    
    # Research tools - local to researcher
    research_tool = mas.Tool(
        name="TopicResearcher",
        func=research_topic,
        description="Conducts comprehensive research on topics"
    )
    research_tool.set_local(researcher)
    
    # Content creation tools - shared between specific agents
    outline_tool = mas.Tool(
        name="ContentOutliner",
        func=generate_content_outline,
        description="Creates structured content outlines"
    )
    outline_tool.set_shared(researcher, writer)
    
    writing_tool = mas.Tool(
        name="ContentWriter",
        func=write_content,
        description="Writes full content based on outlines"
    )
    writing_tool.set_shared(writer, editor)
    
    editing_tool = mas.Tool(
        name="ContentEditor",
        func=edit_content,
        description="Edits and improves content quality"
    )
    editing_tool.set_shared(writer, editor, seo_specialist)
    
    seo_tool = mas.Tool(
        name="SEOOptimizer",
        func=optimize_for_seo,
        description="Optimizes content for search engines"
    )
    seo_tool.set_shared(editor, seo_specialist)
    
    # Publishing tool - global access
    publishing_tool = mas.Tool(
        name="ContentPublisher",
        func=publish_content,
        description="Publishes content to various platforms"
    )
    publishing_tool.set_global()
    
    # 4. Create comprehensive content creation workflow
    print("\n📋 Setting up content creation workflow...")
    
    content_creation_task = mas.Task(
        name="CreateContent",
        description="Complete content creation pipeline from research to publication",
        steps=[
            {"agent": "ContentResearcher", "tool": "TopicResearcher", "input": "AI in Healthcare"},
            {"agent": "ContentResearcher", "tool": "ContentOutliner", "input": "research_results"},
            {"agent": "ContentWriter", "tool": "ContentWriter", "input": "content_outline"},
            {"agent": "ContentEditor", "tool": "ContentEditor", "input": "written_content"},
            {"agent": "SEOSpecialist", "tool": "SEOOptimizer", "input": "edited_content"},
            {"agent": "SEOSpecialist", "tool": "ContentPublisher", "input": "optimized_content"}
        ]
    )
    
    # 5. Set up automation for content scheduling
    print("\n⚡ Configuring content automation...")
    
    content_trigger = mas.Trigger(
        name="ScheduledContentCreation",
        condition=lambda event: event.get("type") == "scheduled_content" and event.get("topic")
    )
    
    auto_content_creation = mas.Automation(
        name="AutoContentPipeline",
        trigger=content_trigger,
        task=content_creation_task
    )
    
    # 6. Build and configure the system
    print("\n🏗️ Building content creation system...")
    
    system = mas.System(enable_logging=True, verbose=True)
    
    # Register all components
    system.register_agents(researcher, writer, editor, seo_specialist)
    system.register_tools(research_tool, outline_tool, writing_tool, editing_tool, seo_tool, publishing_tool)
    system.register_tasks(content_creation_task)
    system.register_automations(auto_content_creation)
    
    # 7. Execute the content creation pipeline
    print("\n🎯 Executing content creation pipeline...")
    
    try:
        # Execute the complete workflow
        result = system.execute_task("CreateContent")
        print(f"✅ Content creation pipeline completed successfully!")
        
        # Save results to file
        with open("content_creation_result.json", "w") as f:
            json.dump(result, f, indent=2)
        print(f"📄 Results saved to content_creation_result.json")
        
    except Exception as e:
        print(f"❌ Content creation failed: {e}")
        logger.error(f"Content creation pipeline failed: {e}")
    
    # 8. Demonstrate automation trigger
    print("\n🤖 Triggering automated content creation...")
    
    try:
        # Trigger automated content creation
        system.trigger_event({
            "type": "scheduled_content",
            "topic": "Future of AI in Business",
            "target_audience": "business professionals",
            "deadline": "2024-01-20"
        })
        print("✅ Automated content creation triggered successfully!")
        
    except Exception as e:
        print(f"❌ Automation trigger failed: {e}")
    
    # 9. System analytics and reporting
    print("\n📊 Content Creation System Analytics:")
    print(f"   • Total Agents: {len(system.agents)}")
    print(f"   • Total Tools: {len(system.tools)}")
    print(f"   • Active Workflows: {len(system.tasks)}")
    print(f"   • Automations: {len(system.automations)}")
    
    # Show tool sharing hierarchy
    print("\n🔧 Tool Sharing Hierarchy:")
    for tool_name, tool in system.tools.items():
        scope = "Local" if hasattr(tool, 'local_agent') and tool.local_agent else \
                "Shared" if hasattr(tool, 'shared_agents') and tool.shared_agents else \
                "Global"
        print(f"   • {tool_name}: {scope}")
    
    print("\n🎉 Real-world content creation pipeline demonstration completed!")
    print("🔍 Check the logs directory for detailed execution traces.")
    
    return system


if __name__ == "__main__":
    # Run the real-world example
    content_system = main()
    
    print("\n💡 This example demonstrates:")
    print("   • Multi-agent collaboration in real workflows")
    print("   • Hierarchical tool sharing (Local → Shared → Global)")
    print("   • Event-driven automation for scheduled tasks")
    print("   • Comprehensive logging and monitoring")
    print("   • Practical business use case implementation")
    print("\n🚀 Your MultiAgenticSwarm is ready for production use!")
