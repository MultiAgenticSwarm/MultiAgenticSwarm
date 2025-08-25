from typing import List, Any
from .state import AgentState, Message, SystemState

def add_message(state: AgentState, message: Message) -> AgentState:
    new_state = state.copy()
    messages = list(new_state.get("messages", []))
    messages.append(message)
    new_state["messages"] = messages
    return new_state

def merge_outputs(state: AgentState, new_outputs: List[Any]) -> AgentState:
    new_state = state.copy()
    outputs = list(new_state.get("outputs", []))
    outputs.extend(new_outputs)
    new_state["outputs"] = outputs
    return new_state

def update_progress(state: AgentState, progress: float) -> AgentState:
    new_state = state.copy()
    new_state["progress"] = progress
    return new_state

def add_tool_result(state: AgentState, tool_name: str, result: Any) -> AgentState:
    new_state = state.copy()
    tool_results = dict(new_state.get("tool_results", {}))
    tool_results[tool_name] = result
    new_state["tool_results"] = tool_results
    return new_state

def add_inter_agent_message(state: AgentState, message: Message) -> AgentState:
    new_state = state.copy()
    comms = list(new_state.get("inter_agent_comm", []))
    comms.append(message)
    new_state["inter_agent_comm"] = comms
    return new_state

def add_update(state: AgentState, update: Any) -> AgentState:
    new_state = state.copy()
    updates = list(new_state.get("updates", []))
    updates.append(update)
    new_state["updates"] = updates
    return new_state

def add_agent(system_state: SystemState, agent_id: str, agent_state: AgentState) -> SystemState:
    new_state = system_state.copy()
    agents = dict(new_state.get("agents", {}))
    agents[agent_id] = agent_state
    new_state["agents"] = agents
    return new_state