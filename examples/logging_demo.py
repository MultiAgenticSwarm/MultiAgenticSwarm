#!/usr/bin/env python3
"""
Comprehensive demonstration of the MultiAgenticSwarm logging capabilities.

This script shows how to:
1. Setup comprehensive logging
2. Use the system with logging enabled
3. View and analyze logs
4. Export logs for analysis

Usage:
    python logging_demo.py
"""

import os
import sys
import time
from pathlib import Path

# Add the parent directory to sys.path so we can import multiagenticswarm
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    # Import the multiagenticswarm package
    import multiagenticswarm as mas
    from multiagenticswarm.logging import (
        setup_logging, view_logs, search_logs, get_summary,
        get_logs_for_agent, get_llm_logs, export_logs,
        log_info, log_debug, log_warning, log_error
    )
    print("✅ Successfully imported multiagenticswarm with logging")
except ImportError as e:
    print(f"❌ Failed to import multiagenticswarm: {e}")
    sys.exit(1)


def demo_basic_logging():
    """Demonstrate basic logging setup and usage."""
    print("\n" + "="*60)
    print("🔧 DEMO: Basic Logging Setup")
    print("="*60)
    
    # Setup comprehensive logging
    log_config = setup_logging(
        verbose=True,  # Enable debug logging
        log_directory="./demo_logs",  # Custom log directory
        enable_json_logs=True  # Enable structured JSON logs
    )
    
    print(f"📁 Logs will be stored in: {log_config['log_directory']}")
    print(f"🆔 Session ID: {log_config['session_id']}")
    
    # Test basic logging functions
    log_info("This is a basic info message", user="demo_user", action="demo")
    log_debug("This is a debug message with data", data={"key": "value", "number": 42})
    log_warning("This is a warning message", severity="medium")
    log_error("This is an error message", error_code=500, description="Demo error")
    
    print("✅ Basic logging demonstrated")


def demo_system_with_logging():
    """Demonstrate using the multiagenticswarm with comprehensive logging."""
    print("\n" + "="*60)
    print("🤖 DEMO: System Usage with Logging")
    print("="*60)
    
    try:
        # Create a simple system for demonstration
        system = mas.System(enable_logging=True, verbose=True)
        
        # Create a demo agent
        agent = mas.Agent(
            name="DemoAgent",
            role="Demonstrates logging functionality",
            system_prompt="You are a demo agent that helps showcase logging capabilities."
        )
        
        # Create a demo tool
        def demo_calculation(x: int, y: int) -> int:
            """A simple calculation tool for demonstration."""
            result = x * y + (x - y)
            return result
        
        tool = mas.Tool(
            name="demo_calculation",
            description="Performs a demo calculation",
            function=demo_calculation
        )
        
        # Add agent and tool to system
        system.add_agent(agent)
        system.add_tool(tool)
        
        # Create a simple task
        task = mas.Task(
            name="demo_task",
            description="A demonstration task",
            agents=[agent],
            tools=[tool]
        )
        
        system.add_task(task)
        
        print("✅ System created with logging enabled")
        
        # The system should automatically log all interactions
        print("🔄 System components are now being logged automatically")
        
    except Exception as e:
        log_error("Failed to create demo system", error=str(e))
        print(f"❌ Error creating system: {e}")


def demo_log_viewing():
    """Demonstrate various log viewing capabilities."""
    print("\n" + "="*60)
    print("👀 DEMO: Log Viewing and Analysis")
    print("="*60)
    
    # Wait a moment for logs to be written
    time.sleep(1)
    
    print("\n📋 Viewing latest logs:")
    view_logs(lines=10)
    
    print("\n🔍 Searching for specific patterns:")
    search_logs("demo")
    
    print("\n📊 System activity summary:")
    get_summary()
    
    print("\n🤖 Agent-specific logs:")
    agent_logs = get_logs_for_agent("DemoAgent")
    print(f"Found {len(agent_logs)} logs for DemoAgent")
    for log in agent_logs[:3]:  # Show first 3
        print(f"  - {log.get('timestamp', 'N/A')}: {log.get('message', 'N/A')}")
    
    print("\n🧠 LLM-related logs:")
    llm_logs = get_llm_logs()
    print(f"Found {len(llm_logs)} LLM-related logs")
    if llm_logs:
        for log in llm_logs[:2]:  # Show first 2
            print(f"  - {log.get('timestamp', 'N/A')}: {log.get('mas_provider', 'N/A')} - {log.get('message', 'N/A')}")


def demo_log_export():
    """Demonstrate log export functionality."""
    print("\n" + "="*60)
    print("📤 DEMO: Log Export")
    print("="*60)
    
    # Export all logs to a file
    export_file = "./demo_logs/exported_logs.json"
    success = export_logs(export_file)
    
    if success:
        print(f"✅ Logs exported to: {export_file}")
        
        # Show file size
        if os.path.exists(export_file):
            size = os.path.getsize(export_file)
            print(f"📁 Export file size: {size} bytes")
    else:
        print("❌ Failed to export logs")


def demo_advanced_features():
    """Demonstrate advanced logging features."""
    print("\n" + "="*60)
    print("🚀 DEMO: Advanced Logging Features")
    print("="*60)
    
    # Get the logger for manual logging
    logger = mas.utils.logger.get_logger("advanced_demo")
    
    # Log a function call manually
    logger.log_function_call(
        "advanced_demo_function",
        args=("arg1", "arg2"),
        kwargs={"param1": "value1", "param2": 42},
        context={"demo": True, "level": "advanced"}
    )
    
    # Log a simulated LLM request
    logger.log_llm_request(
        provider="demo_provider",
        model="demo-model-v1",
        messages=[
            {"role": "system", "content": "You are a demo assistant"},
            {"role": "user", "content": "This is a demo request"}
        ],
        context={"demo": True}
    )
    
    # Log a simulated LLM response
    logger.log_llm_response(
        provider="demo_provider",
        model="demo-model-v1",
        response="This is a demo response from the LLM",
        metadata={"temperature": 0.7, "max_tokens": 100},
        usage={"prompt_tokens": 25, "completion_tokens": 15, "total_tokens": 40}
    )
    
    # Log a tool execution
    logger.log_tool_execution(
        tool_name="demo_calculation",
        agent_name="DemoAgent",
        parameters={"x": 10, "y": 5},
        result=55,
        execution_time=0.001
    )
    
    # Log an agent action
    logger.log_agent_action(
        agent_name="DemoAgent",
        action="process_request",
        input_data="Demo input data",
        output_data="Demo output data",
        context={"step": 1, "total_steps": 3}
    )
    
    # Log a task execution step
    logger.log_task_execution(
        task_name="demo_task",
        step=1,
        status="completed",
        agent="DemoAgent",
        tool="demo_calculation",
        context={"result": "success"}
    )
    
    print("✅ Advanced logging features demonstrated")


def demo_flutter_app_builder_integration():
    """Show how logging would work with flutter_app_builder."""
    print("\n" + "="*60)
    print("📱 DEMO: Flutter App Builder Integration")
    print("="*60)
    
    print("This demonstrates how you would use logging in flutter_app_builder:")
    print()
    
    demo_code = '''
# In your flutter_app_builder script:

import multiagenticswarm as mas
from multiagenticswarm.logging import setup_logging, view_logs, get_summary

# Setup logging at the beginning
log_config = setup_logging(
    verbose=True,
    log_directory="./flutter_builder_logs",
    enable_json_logs=True
)

# Use the system normally - everything gets logged automatically
system = mas.System(name="FlutterAppBuilder")
# ... create agents, tools, tasks ...

# After execution, view the logs
print("\\n=== Execution Summary ===")
get_summary()

print("\\n=== Recent Activity ===") 
view_logs(lines=20)

# Export logs for analysis
mas.export_logs("./flutter_builder_logs/session_export.json")
'''
    
    print(demo_code)
    print("✅ Integration example provided")


def main():
    """Run all logging demonstrations."""
    print("🚀 MultiAgenticSwarm Comprehensive Logging Demo")
    print("=" * 60)
    
    try:
        # Run all demos
        demo_basic_logging()
        demo_system_with_logging()
        demo_log_viewing()
        demo_log_export()
        demo_advanced_features()
        demo_flutter_app_builder_integration()
        
        print("\n" + "="*60)
        print("🎉 ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\n📋 Summary of what was demonstrated:")
        print("✅ Basic logging setup and configuration")
        print("✅ Automatic system-wide logging")
        print("✅ Log viewing and searching")
        print("✅ Log export functionality")
        print("✅ Advanced logging features")
        print("✅ Integration with example projects")
        
        print(f"\n📁 All demo logs are stored in: ./demo_logs/")
        print("💡 You can now examine the log files to see the structured output!")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
