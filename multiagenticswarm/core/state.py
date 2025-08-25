from typing import TypedDict, List, Dict, Any, Optional
import json

class Message(TypedDict):
    """
    Represents a single message in an agent's conversation history or inter-agent communication.
    """
    role: str           # e.g., "user", "agent", "system"
    content: str        # The message text/content
    timestamp: float    # Unix timestamp of when the message was sent

class AgentState(TypedDict, total=False):
    """
    State for a single agent.

    Fields:
        agent_id: Unique identifier for the agent.
        name: Human-readable name.
        messages: Conversation history (list of Message).
        outputs: List of outputs/results produced by the agent.
        progress: Progress as a float (0.0-1.0 or percent).
        tool_permissions: List of tool names the agent can use.
        tool_results: Results from tool calls.
        collaboration_context: Shared context/rules for collaboration.
        inter_agent_comm: Messages to/from other agents.
        memory_working: Working memory (short-term, task-specific).
        memory_short_term: Short-term memory (recent context).
        updates: General updates/events (replaces file writes).
    """
    agent_id: str
    name: str
    messages: List[Message]
    outputs: List[Any]
    progress: float
    tool_permissions: List[str]
    tool_results: Dict[str, Any]
    collaboration_context: Dict[str, Any]
    inter_agent_comm: List[Message]
    memory_working: List[Any]
    memory_short_term: List[Any]
    updates: List[Any]

class SystemState(TypedDict, total=False):
    """
    State for the entire multi-agent system.

    Fields:
        agents: Mapping of agent_id to AgentState.
        global_context: Global context/rules for the system.
        progress_board: List of progress updates (replaces ProgressBoard file).
        updates: General system updates/events.
    """
    agents: Dict[str, AgentState]
    global_context: Dict[str, Any]
    progress_board: List[Any]
    updates: List[Any]

def serialize_state(state: SystemState) -> str:
    """
    Serialize the system state to a JSON string.
    """
    return json.dumps(state)

def deserialize_state(state_str: str) -> SystemState:
    """
    Deserialize the system state from a JSON string.
    """
    return json.loads(state_str)
