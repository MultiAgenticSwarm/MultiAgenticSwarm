"""
Example usage of the MultiAgenticSwarm package.

This example demonstrates all major features:
- Agent creation with different LLM providers
- Tool creation with hierarchical sharing
- Task definition and collaboration
- Event-driven automation
- System orchestration
"""

import asyncio
from multiagenticswarm import Agent, Tool, Task, Collaboration, Trigger, Automation, System


# Mock functions for demonstration
def fetch_from_api(query: str) -> dict:
    """Mock API fetch function."""
    return {"data": f"API result for: {query}", "status": "success"}


def transform_data(data: dict) -> dict:
    """Mock data transformation function."""
    return {"transformed": data, "processing_time": "0.5s"}


def send_email(recipient: str, subject: str, body: str) -> str:
    """Mock email sending function."""
    return f"Email sent to {recipient}: {subject}"


def generate_report(data: dict) -> str:
    """Mock report generation function."""
    return f"Report generated with {len(str(data))} characters of data"


def main():
    """Main example demonstrating the complete system."""
    
    # 1️⃣ Create agents with different LLM providers
    print("🤖 Creating agents...")
    
    data_analyst = Agent(
        name="DataAnalyst",
        description="Analyzes data patterns and trends",
        system_prompt="You are an expert data analyst. Analyze data thoroughly and provide insights.",
        llm_provider="openai",
        llm_model="gpt-4"
    )
    
    action_executor = Agent(
        name="ActionExecutor", 
        description="Executes actions based on analysis",
        system_prompt="You execute business actions efficiently based on data analysis.",
        llm_provider="anthropic",
        llm_model="claude-3.5-sonnet"
    )
    
    report_generator = Agent(
        name="ReportGenerator",
        description="Generates comprehensive reports",
        system_prompt="You create detailed, professional reports from data and analysis.",
        llm_provider="openai",
        llm_model="gpt-3.5-turbo"  # Cost-effective for report generation
    )
    
    # 2️⃣ Create tools with hierarchical sharing
    print("🔧 Creating tools...")
    
    # Local tool - only for DataAnalyst
    api_fetcher = Tool(
        name="APIFetcher",
        func=fetch_from_api,
        description="Fetches data from external APIs",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Query to search for"}
            },
            "required": ["query"]
        }
    )
    api_fetcher.set_local(data_analyst)
    
    # Shared tool - for DataAnalyst and ActionExecutor  
    data_transformer = Tool(
        name="DataTransformer",
        func=transform_data,
        description="Transforms and processes data",
        parameters={
            "type": "object", 
            "properties": {
                "data": {"type": "object", "description": "Data to transform"}
            },
            "required": ["data"]
        }
    )
    data_transformer.set_shared(data_analyst, action_executor)
    
    # Global tool - available to all agents
    email_sender = Tool(
        name="EmailSender",
        func=send_email,
        description="Sends emails to recipients",
        parameters={
            "type": "object",
            "properties": {
                "recipient": {"type": "string"},
                "subject": {"type": "string"},
                "body": {"type": "string"}
            },
            "required": ["recipient", "subject", "body"]
        }
    )
    email_sender.set_global()
    
    # Another shared tool
    report_tool = Tool(
        name="ReportGenerator",
        func=generate_report,
        description="Generates reports from data",
        parameters={
            "type": "object",
            "properties": {
                "data": {"type": "object", "description": "Data to include in report"}
            },
            "required": ["data"]
        }
    )
    report_tool.set_shared(data_analyst, report_generator)
    
    # 3️⃣ Create tasks and collaborations
    print("📋 Creating tasks...")
    
    data_analysis_task = Task(
        name="DataAnalysisWorkflow",
        description="Complete data analysis and reporting workflow",
        steps=[
            {
                "agent": "DataAnalyst",
                "tool": "APIFetcher", 
                "input": "fetch latest sales data",
                "context": {"source": "sales_api"}
            },
            {
                "agent": "DataAnalyst",
                "tool": "DataTransformer",
                "input": "analyze sales trends",
                "context": {"analysis_type": "trend"}
            },
            {
                "agent": "ReportGenerator",
                "tool": "ReportGenerator", 
                "input": "create executive summary",
                "context": {"format": "executive"}
            },
            {
                "agent": "ActionExecutor",
                "tool": "EmailSender",
                "input": "send report to stakeholders",
                "context": {"recipients": ["ceo@company.com", "cfo@company.com"]}
            }
        ]
    )
    
    # Create a collaboration pattern
    analysis_collaboration = Collaboration(
        name="AnalysisTeam",
        agents=[data_analyst, action_executor, report_generator],
        pattern="sequential",
        shared_context={"project": "Q4_analysis", "priority": "high"},
        handoff_rules={
            "DataAnalyst": "ReportGenerator",
            "ReportGenerator": "ActionExecutor"
        }
    )
    
    # 4️⃣ Create triggers and automations
    print("⚡ Creating triggers and automations...")
    
    # Event-based trigger
    data_update_trigger = Trigger(
        name="DataUpdateTrigger",
        trigger_type="event",
        condition_string="event.type == 'data_update' and event.source == 'sales'",
        description="Triggers when sales data is updated"
    )
    
    # Time-based trigger  
    daily_report_trigger = Trigger(
        name="DailyReportTrigger", 
        trigger_type="schedule",
        schedule="0 9 * * *",  # 9 AM daily
        description="Triggers daily report generation"
    )
    
    # Create automations
    auto_analysis = Automation(
        trigger=data_update_trigger,
        sequence=data_analysis_task,
        name="AutoDataAnalysis",
        description="Automatically analyze data when updated"
    )
    
    daily_reporting = Automation(
        trigger=daily_report_trigger,
        sequence=data_analysis_task, 
        name="DailyReporting",
        description="Generate daily reports automatically"
    )
    
    # 5️⃣ Build and configure the system
    print("🏗️ Building system...")
    
    system = System()
    
    # Register all components
    system.register_agents(data_analyst, action_executor, report_generator)
    system.register_tools(api_fetcher, data_transformer, email_sender, report_tool)
    system.register_tasks(data_analysis_task)
    system.register_collaborations(analysis_collaboration)
    system.register_triggers(data_update_trigger, daily_report_trigger)
    system.register_automations(auto_analysis, daily_reporting)
    
    # 6️⃣ Demonstrate system capabilities
    print("\n" + "="*50)
    print("🚀 MULTIAGENTICSWARM DEMONSTRATION")
    print("="*50)
    
    # Show system status
    status = system.get_system_status()
    print(f"\n📊 System Status:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # Test individual agent execution
    print(f"\n🧪 Testing individual agent...")
    try:
        result = asyncio.run(system.execute_agent(
            "DataAnalyst",
            "What are the key trends in our sales data?",
            {"context": "Q4 analysis"}
        ))
        print(f"Agent result: {result['output'][:100]}...")
    except Exception as e:
        print(f"Agent execution: {e}")
    
    # Test task execution
    print(f"\n🧪 Testing task execution...")
    try:
        result = asyncio.run(system.execute_task(
            "DataAnalysisWorkflow",
            {"priority": "high", "requester": "demo"}
        ))
        print(f"Task status: {result['status']}")
        print(f"Steps completed: {len(result['results'])}")
    except Exception as e:
        print(f"Task execution: {e}")
    
    # Test event processing
    print(f"\n🧪 Testing event-driven automation...")
    system.emit_event({
        "type": "data_update",
        "source": "sales", 
        "timestamp": "2024-12-22T10:00:00Z",
        "changes": ["revenue", "units_sold"]
    })
    
    # Process events
    asyncio.run(system.process_events())
    
    # Show automation statistics
    for auto_name, automation in system.automations.items():
        stats = automation.get_statistics()
        print(f"\n📈 {auto_name} Statistics:")
        print(f"  Executions: {stats['execution_count']}")
        print(f"  Success Rate: {stats['success_rate']:.1%}")
    
    # 7️⃣ Save configuration for reuse
    print(f"\n💾 Saving configuration...")
    system.save_config("example_config.yaml")
    print("Configuration saved to example_config.yaml")
    
    # 8️⃣ Demonstrate configuration loading
    print(f"\n📂 Testing configuration loading...")
    new_system = System.from_config("example_config.yaml")
    new_status = new_system.get_system_status()
    print(f"Loaded system with {new_status['agents']} agents, {new_status['tools']} tools")
    
    print(f"\n✅ MultiAgenticSwarm demonstration completed!")
    print("="*50)


def configuration_example():
    """Example of configuration-driven setup."""
    
    # Create example YAML configuration
    yaml_config = """
agents:
  - name: "QuickAnalyst"
    description: "Fast data analysis agent"
    system_prompt: "You provide quick data insights"
    llm_provider: "openai"
    llm_model: "gpt-3.5-turbo"
    
  - name: "DeepThinker"
    description: "Comprehensive analysis agent"
    system_prompt: "You provide detailed, thorough analysis"
    llm_provider: "anthropic"
    llm_model: "claude-3.5-sonnet"

tools:
  - name: "QuickFetch"
    description: "Fast data fetching"
    scope: "local"
    agents: ["QuickAnalyst"]
    
  - name: "DeepAnalysis"
    description: "Comprehensive analysis tool"
    scope: "shared"
    agents: ["QuickAnalyst", "DeepThinker"]
    
  - name: "Notifier"
    description: "Global notification tool"
    scope: "global"

tasks:
  - name: "QuickInsight"
    description: "Generate quick insights"
    steps:
      - agent: "QuickAnalyst"
        tool: "QuickFetch"
        input: "get recent data"
      - agent: "QuickAnalyst" 
        tool: "DeepAnalysis"
        input: "analyze quickly"
      - agent: "QuickAnalyst"
        tool: "Notifier"
        input: "send quick update"

triggers:
  - name: "UrgentAlert"
    trigger_type: "event"
    condition_string: "event.priority == 'urgent'"

automations:
  - trigger: "UrgentAlert"
    task: "QuickInsight"
    name: "UrgentResponse"
    description: "Respond to urgent events quickly"
"""
    
    # Save configuration
    with open("quick_config.yaml", "w") as f:
        f.write(yaml_config)
    
    # Load and use
    system = System.from_config("quick_config.yaml")
    
    print(f"\n🔧 Configuration-driven system created:")
    print(f"  Agents: {len(system.agents)}")
    print(f"  Tools: {len(system.tools)}")  
    print(f"  Tasks: {len(system.tasks)}")
    print(f"  Automations: {len(system.automations)}")
    
    # Test urgent event
    system.emit_event({
        "type": "alert",
        "priority": "urgent",
        "message": "System performance degraded"
    })
    
    return system


if __name__ == "__main__":
    # Run main demonstration
    main()
    
    print(f"\n" + "="*50)
    print("🔧 CONFIGURATION EXAMPLE")
    print("="*50)
    
    # Run configuration example
    configuration_example()
    
    print(f"\n🎉 All examples completed successfully!")
