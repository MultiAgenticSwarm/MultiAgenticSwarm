#!/usr/bin/env python3
"""
Example: Using Agent as LangGraph Node

This example demonstrates how to use the refactored Agent class as a node
in a LangGraph StateGraph workflow.

This example showcases the implementation of Ticket #6: Refactor Agent as LangGraph Node
"""

import sys
import os
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from multiagenticswarm.core import Agent, AgentState


def demonstrate_basic_node_usage():
    """Demonstrate basic agent node usage."""
    print("🔹 Basic Agent Node Usage")
    print("-" * 40)

    # Create an agent
    agent = Agent(
        name="demo_agent",
        description="A demonstration agent",
        system_prompt="You are a helpful assistant that provides clear, concise responses.",
        llm_provider="openai",  # Configure with your provider
        llm_model="gpt-3.5-turbo"
    )

    # Create initial state
    state = agent.create_initial_state(
        "Explain the benefits of using state-based agent execution",
        context={"demo_mode": True}
    )

    print(f"✓ Created agent: {agent.name}")
    print(f"✓ Initial state has {len(state['messages'])} message(s)")

    # Execute as node (this is how it would be called in a StateGraph)
    try:
        updated_state = agent(state)
        response = agent.extract_response_from_state(updated_state)
        print(f"✓ Agent execution completed")
        print(f"✓ Response: {response[:100]}..." if len(response) > 100 else f"✓ Response: {response}")
    except Exception as e:
        print(f"⚠ Agent execution failed: {e}")
        print("  (This is expected without proper LLM configuration)")

    return agent, state


def demonstrate_multi_agent_workflow():
    """Demonstrate how multiple agents can work with shared state."""
    print("\n🔹 Multi-Agent Workflow with Shared State")
    print("-" * 40)

    # Create specialized agents
    agents = {
        "researcher": Agent(
            name="researcher",
            description="Research and information gathering specialist",
            system_prompt="You research topics and gather comprehensive information."
        ),
        "writer": Agent(
            name="writer",
            description="Content writing and communication specialist",
            system_prompt="You write clear, engaging content based on research."
        ),
        "reviewer": Agent(
            name="reviewer",
            description="Quality assurance and review specialist",
            system_prompt="You review content for quality, accuracy, and completeness."
        )
    }

    # Create shared state for the workflow
    shared_state: AgentState = {
        "messages": [
            {"role": "user", "content": "Create a brief guide about multi-agent systems"}
        ],
        "agent_outputs": {},
        "tool_permissions": {
            "researcher": ["web_search", "document_reader"],
            "writer": ["text_editor", "document_writer"],
            "reviewer": ["grammar_checker", "fact_checker"]
        },
        "tool_results": {},
        "current_agent": None,
        "execution_context": {
            "project": "multi_agent_guide",
            "target_audience": "developers",
            "max_length": 500
        },
        "errors": []
    }

    print(f"✓ Created {len(agents)} specialized agents")
    print(f"✓ Shared state configured with tool permissions")

    # Simulate workflow execution (in real StateGraph, this would be automatic)
    workflow_order = ["researcher", "writer", "reviewer"]

    for agent_name in workflow_order:
        agent = agents[agent_name]
        print(f"\n  🤖 {agent_name.title()} executing...")

        try:
            # Each agent processes the shared state
            updated_state = agent(shared_state.copy())

            # In a real workflow, state would be passed between nodes
            # Here we simulate by checking the output
            output = updated_state.get("agent_outputs", {}).get(agent_name, {})
            if output.get("success", False):
                print(f"     ✓ {agent_name} completed successfully")
            else:
                print(f"     ⚠ {agent_name} execution failed (expected without LLM config)")

        except Exception as e:
            print(f"     ⚠ {agent_name} error: {e}")

    return agents, shared_state


def demonstrate_state_evolution():
    """Demonstrate how state evolves through agent processing."""
    print("\n🔹 State Evolution Through Agent Processing")
    print("-" * 40)

    agent = Agent(
        name="state_demo_agent",
        description="Agent for demonstrating state evolution"
    )

    # Start with minimal state
    initial_state: AgentState = {
        "messages": [{"role": "user", "content": "Hello!"}],
        "agent_outputs": {},
        "tool_permissions": {},
        "tool_results": {},
        "current_agent": None,
        "execution_context": {"step": 1},
        "errors": []
    }

    print("📊 Initial state:")
    print(f"   Messages: {len(initial_state['messages'])}")
    print(f"   Agent outputs: {len(initial_state['agent_outputs'])}")
    print(f"   Context: {initial_state['execution_context']}")

    # Process through agent
    try:
        final_state = agent(initial_state)

        print("\n📊 Final state:")
        print(f"   Messages: {len(final_state['messages'])}")
        print(f"   Agent outputs: {len(final_state['agent_outputs'])}")
        print(f"   Current agent: {final_state.get('current_agent')}")
        print(f"   Errors: {len(final_state.get('errors', []))}")

        # Show what the agent added
        if agent.name in final_state.get('agent_outputs', {}):
            agent_result = final_state['agent_outputs'][agent.name]
            print(f"   Agent execution time: {agent_result.get('execution_time', 0):.3f}s")
            print(f"   Agent success: {agent_result.get('success', False)}")

    except Exception as e:
        print(f"⚠ State processing failed: {e}")


def demonstrate_compatibility_bridge():
    """Demonstrate backward compatibility features."""
    print("\n🔹 Backward Compatibility Bridge")
    print("-" * 40)

    agent = Agent(name="compatibility_demo", description="Compatibility demonstration")

    # Old style: direct execution
    print("📎 Legacy execute() method still available:")
    print("   agent.execute('Hello', context={'old_style': True})")
    print("   (Returns dict with output, execution_time, etc.)")

    # New style: state-based
    print("\n📎 New state-based execution:")
    print("   state = agent.create_initial_state('Hello', {'new_style': True})")
    print("   updated_state = agent(state)")
    print("   response = agent.extract_response_from_state(updated_state)")

    # Bridge method
    print("\n📎 Bridge method for gradual migration:")
    print("   result = await agent.execute_as_node('Hello', {'bridge': True})")
    print("   (Takes legacy inputs, returns legacy format, uses new node internally)")

    # Node compatibility check
    print(f"\n📎 Node compatibility: {agent.is_node_compatible()}")

    try:
        node_info = agent.get_node_info()
        print(f"📎 Node info available: {list(node_info.keys())}")
    except Exception as e:
        print(f"📎 Node info failed: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Agent as LangGraph Node - Example Usage")
    print("   Implementation of Ticket #6")
    print("=" * 60)

    try:
        # Run demonstrations
        demonstrate_basic_node_usage()
        demonstrate_multi_agent_workflow()
        demonstrate_state_evolution()
        demonstrate_compatibility_bridge()

        print("\n" + "=" * 60)
        print("✅ SUCCESS: All demonstrations completed")
        print("\n🔧 Next Steps for Full Integration:")
        print("   1. Configure LLM provider (OpenAI API key, etc.)")
        print("   2. Wait for Ticket #1: Full state schema from Dev 1")
        print("   3. Wait for Ticket #9: Tool system refactor from Dev 3")
        print("   4. Integrate with StateGraph compilation (Ticket #4)")
        print("\n📚 The agent is now ready to work as a LangGraph node!")

    except Exception as e:
        print(f"\n❌ Error in demonstration: {e}")
        import traceback
        traceback.print_exc()
