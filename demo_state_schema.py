#!/usr/bin/env python3
"""
Demonstration of the Core State Schema implementation.

This script shows how the new AgentState schema replaces file I/O based
state management with a centralized, type-safe state system.
"""

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from multiagenticswarm.core.state import (
    AgentState,
    create_initial_state,
    validate_state_schema,
    serialize_state_for_checkpoint,
    CURRENT_STATE_VERSION,
)
from multiagenticswarm.core.state_reducers import (
    merge_agent_outputs,
    aggregate_progress,
    resolve_permissions,
    merge_tool_results,
)


def demo_before_after():
    """Demonstrate the before/after state management approach."""
    print("🔄 BEFORE: File I/O Based State Management")
    print("=" * 50)
    print("❌ State scattered across multiple JSON files")
    print("❌ Slow file I/O operations")
    print("❌ No type safety")
    print("❌ Difficult to debug")
    print("❌ No checkpointing support")
    print()

    print("✅ AFTER: Centralized State Schema")
    print("=" * 50)
    print("✅ Single AgentState TypedDict")
    print("✅ State flows through LangGraph")
    print("✅ Full type safety with annotations")
    print("✅ Rich debugging capabilities")
    print("✅ Built-in checkpointing support")
    print()


def demo_state_creation():
    """Demonstrate creating and working with AgentState."""
    print("📋 Creating Initial State")
    print("=" * 30)

    # Create initial state with collaboration prompt
    collaboration_prompt = """
    Build a modern web application with the following requirements:
    - React frontend with TypeScript
    - Node.js backend with Express
    - PostgreSQL database
    - Docker deployment
    
    Agents should work in parallel on different components.
    """

    initial_message = HumanMessage(
        content="Let's start building this web application together!"
    )

    agent_roles = {
        "frontend_dev": "React/TypeScript developer",
        "backend_dev": "Node.js/Express developer",
        "database_dev": "PostgreSQL database designer",
        "devops_engineer": "Docker deployment specialist",
    }

    state = create_initial_state(
        collaboration_prompt=collaboration_prompt,
        initial_message=initial_message,
        agent_roles=agent_roles,
        workflow_pattern="parallel",
        execution_mode="supervisor",
    )

    print(f"✅ State created with {len(state)} fields")
    print(f"✅ State version: {state['state_version']}")
    print(f"✅ Workflow pattern: {state['workflow_pattern']}")
    print(f"✅ Agent roles: {list(state['agent_roles'].keys())}")
    print(f"✅ Initial messages: {len(state['messages'])}")
    print()

    return state


def demo_state_updates(state: AgentState):
    """Demonstrate state updates using reducers."""
    print("🔄 Updating State with Reducers")
    print("=" * 35)

    # 1. Update task progress
    print("1. Updating task progress...")
    existing_progress = state.get("task_progress", {})
    new_progress = {
        "frontend_setup": 0.3,
        "backend_setup": 0.5,
        "database_design": 0.8,
        "docker_config": 0.1,
    }
    updated_progress = aggregate_progress(existing_progress, new_progress)
    state["task_progress"] = updated_progress
    print(f"   Overall progress: {updated_progress.get('_overall', 0):.1%}")

    # 2. Update agent outputs
    print("2. Adding agent outputs...")
    existing_outputs = state.get("agent_outputs", {})
    new_outputs = {
        "frontend_dev": {
            "action": "Created React app structure",
            "files_created": ["src/App.tsx", "src/index.tsx"],
            "status": "in_progress",
        },
        "backend_dev": {
            "action": "Set up Express server",
            "files_created": ["server.js", "routes/api.js"],
            "status": "completed",
        },
    }
    updated_outputs = merge_agent_outputs(existing_outputs, new_outputs)
    state["agent_outputs"] = updated_outputs
    print(f"   Agent outputs from: {list(updated_outputs.keys())}")

    # 3. Update tool permissions
    print("3. Managing tool permissions...")
    existing_permissions = state.get("tool_permissions", {})
    new_permissions = {
        "frontend_dev": ["npm", "git", "file_editor"],
        "backend_dev": ["npm", "git", "file_editor", "database_client"],
        "devops_engineer": ["docker", "git", "file_editor", "ssh_client"],
    }
    updated_permissions = resolve_permissions(existing_permissions, new_permissions)
    state["tool_permissions"] = updated_permissions
    print(f"   Permissions configured for: {list(updated_permissions.keys())}")

    # 4. Add tool results
    print("4. Recording tool results...")
    existing_tool_results = state.get("tool_results", {})
    new_tool_results = {
        "npm": {"command": "npm init", "status": "success", "output": "Package.json created"},
        "git": {"command": "git init", "status": "success", "output": "Repository initialized"},
        "docker": {"command": "docker build", "status": "running", "output": "Building image..."},
    }
    updated_tool_results = merge_tool_results(existing_tool_results, new_tool_results)
    state["tool_results"] = updated_tool_results
    print(f"   Tool results recorded: {list(updated_tool_results.keys())}")

    print()
    return state


def demo_state_validation(state: AgentState):
    """Demonstrate state validation and serialization."""
    print("🔍 State Validation & Serialization")
    print("=" * 40)

    # Validate state schema
    is_valid = validate_state_schema(state)
    print(f"✅ State schema validation: {'PASSED' if is_valid else 'FAILED'}")

    # Add some messages to demonstrate message handling
    state["messages"].extend(
        [
            AIMessage(content="Frontend structure is ready, starting component development."),
            AIMessage(content="Backend API endpoints configured successfully."),
            SystemMessage(content="Project setup phase completed. Moving to development phase."),
        ]
    )
    print(f"✅ Messages in state: {len(state['messages'])}")

    # Serialize for checkpointing
    serialized = serialize_state_for_checkpoint(state)
    checkpoint_size = len(str(serialized))
    print(f"✅ Serialization successful: {checkpoint_size} characters")

    # Show state statistics
    print(f"✅ State statistics:")
    print(f"   - Total fields: {len(state)}")
    print(f"   - Messages: {len(state['messages'])}")
    print(f"   - Agent outputs: {len(state['agent_outputs'])}")
    print(f"   - Tool permissions: {len(state['tool_permissions'])}")
    print(f"   - Task progress items: {len(state['task_progress'])}")

    print()


def demo_memory_layers(state: AgentState):
    """Demonstrate the memory layer system."""
    print("🧠 Memory Layer Management")
    print("=" * 30)

    # Working memory - current task context
    state["working_memory"] = {
        "current_phase": "development",
        "active_tasks": ["frontend_components", "api_development", "database_schema"],
        "blockers": ["waiting for design mockups"],
        "next_steps": ["implement user authentication", "create database migrations"],
    }

    # Short-term memory - recent conversation
    state["short_term_memory"] = {
        "last_decisions": [
            "Agreed to use TypeScript for better type safety",
            "Chose PostgreSQL over MongoDB for relational data",
            "Decided on Docker Compose for local development",
        ],
        "recent_questions": ["Should we use Redux or Context API?", "What about testing strategy?"],
    }

    # Shared memory - information visible to all agents
    state["shared_memory"] = {
        "project_requirements": "Web app with React frontend and Node.js backend",
        "coding_standards": "ESLint + Prettier, TypeScript strict mode",
        "deployment_target": "AWS ECS with RDS",
        "timeline": "2 weeks for MVP",
    }

    # Private memory - agent-specific information
    state["private_memory"] = {
        "frontend_dev": {
            "preferred_libs": ["Material-UI", "React Query", "Formik"],
            "experience_level": "senior",
            "current_focus": "component architecture",
        },
        "backend_dev": {
            "preferred_patterns": ["MVC", "dependency injection"],
            "experience_level": "senior",
            "current_focus": "API design",
        },
    }

    print("✅ Working memory: Current task context")
    print("✅ Short-term memory: Recent conversation context")
    print("✅ Shared memory: Project-wide information")
    print("✅ Private memory: Agent-specific data")
    print()


def demo_communication_system(state: AgentState):
    """Demonstrate the inter-agent communication system."""
    print("💬 Inter-Agent Communication")
    print("=" * 35)

    # Agent messages - internal communications
    state["agent_messages"] = [
        {
            "from": "frontend_dev",
            "to": "backend_dev",
            "message": "What's the expected format for the user profile API?",
            "timestamp": "2024-01-15T10:30:00Z",
            "priority": "normal",
        },
        {
            "from": "backend_dev",
            "to": "frontend_dev",
            "message": "Here's the API spec: GET /api/users/:id returns {id, name, email, avatar}",
            "timestamp": "2024-01-15T10:32:00Z",
            "priority": "normal",
        },
    ]

    # Help requests - assistance between agents
    state["help_requests"] = [
        {
            "requesting_agent": "devops_engineer",
            "topic": "Docker networking",
            "details": "Need help with connecting containers in development environment",
            "priority": "high",
            "status": "open",
            "timestamp": "2024-01-15T11:00:00Z",
        }
    ]

    # Broadcast messages - system-wide announcements
    state["broadcast_messages"] = [
        {
            "from": "system",
            "message": "Development phase has started. All agents may begin their tasks.",
            "timestamp": "2024-01-15T09:00:00Z",
            "type": "phase_change",
        }
    ]

    print(f"✅ Agent messages: {len(state['agent_messages'])} direct communications")
    print(f"✅ Help requests: {len(state['help_requests'])} assistance requests")
    print(f"✅ Broadcast messages: {len(state['broadcast_messages'])} system announcements")
    print()


def demo_debugging_features(state: AgentState):
    """Demonstrate debugging and monitoring capabilities."""
    print("🐛 Debugging & Monitoring")
    print("=" * 30)

    # Execution trace
    state["execution_trace"] = [
        {
            "id": "trace_001",
            "timestamp": "2024-01-15T09:01:00Z",
            "agent": "frontend_dev",
            "action": "analyze_requirements",
            "duration_ms": 1500,
            "status": "completed",
        },
        {
            "id": "trace_002",
            "timestamp": "2024-01-15T09:02:30Z",
            "agent": "backend_dev",
            "action": "setup_project_structure",
            "duration_ms": 3000,
            "status": "completed",
        },
        {
            "id": "trace_003",
            "timestamp": "2024-01-15T09:05:00Z",
            "agent": "frontend_dev",
            "action": "create_components",
            "duration_ms": 8000,
            "status": "in_progress",
        },
    ]

    # Performance metrics
    state["performance_metrics"] = {
        "total_execution_time_ms": 12500,
        "agent_response_times": {
            "frontend_dev": {"avg_ms": 2200, "max_ms": 8000},
            "backend_dev": {"avg_ms": 1800, "max_ms": 3000},
        },
        "tool_execution_stats": {
            "npm": {"calls": 5, "avg_duration_ms": 2000},
            "git": {"calls": 3, "avg_duration_ms": 500},
        },
        "memory_usage_mb": 45.2,
    }

    # Error log
    state["error_log"] = [
        "[2024-01-15T09:03:15Z] Warning: npm package version conflict detected",
        "[2024-01-15T09:04:22Z] Info: Automatically resolved dependency conflict",
    ]

    # Debug flags
    state["debug_flags"] = {
        "verbose_logging": True,
        "trace_tool_calls": True,
        "measure_performance": True,
        "validate_state_changes": True,
    }

    print(f"✅ Execution trace: {len(state['execution_trace'])} recorded actions")
    print(f"✅ Performance metrics: Response times and resource usage tracked")
    print(f"✅ Error log: {len(state['error_log'])} entries")
    print(f"✅ Debug flags: {sum(state['debug_flags'].values())} features enabled")
    print()


def main():
    """Run the complete demonstration."""
    print("🚀 Core State Schema Demonstration")
    print("=" * 50)
    print()

    # Show before/after comparison
    demo_before_after()

    # Create initial state
    state = demo_state_creation()

    # Demonstrate state updates
    state = demo_state_updates(state)

    # Validate and serialize state
    demo_state_validation(state)

    # Show memory layers
    demo_memory_layers(state)

    # Show communication system
    demo_communication_system(state)

    # Show debugging features
    demo_debugging_features(state)

    print("🎉 Demonstration Complete!")
    print("=" * 30)
    print("The Core State Schema provides:")
    print("✅ Centralized state management")
    print("✅ Type safety with TypedDict")
    print("✅ Custom reducers for conflict resolution")
    print("✅ Comprehensive memory management")
    print("✅ Rich inter-agent communication")
    print("✅ Advanced debugging capabilities")
    print("✅ Full checkpointing support")
    print()
    print("Ready for production use in MultiAgenticSwarm! 🎯")


if __name__ == "__main__":
    main()