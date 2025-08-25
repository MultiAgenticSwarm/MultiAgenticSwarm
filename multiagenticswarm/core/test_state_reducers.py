import unittest
from datetime import datetime
from .state import AgentState, Message, SystemState, serialize_state, deserialize_state
from .state_reducers import (
    add_message, merge_outputs, update_progress, add_tool_result,
    add_inter_agent_message, add_update, add_agent
)

class TestStateReducers(unittest.TestCase):
    def test_add_message(self):
        state: AgentState = {"agent_id": "a1", "messages": []}
        msg: Message = {"role": "user", "content": "Hello", "timestamp": 123.0}
        new_state = add_message(state, msg)
        self.assertEqual(len(new_state["messages"]), 1)
        self.assertEqual(new_state["messages"][0]["content"], "Hello")

    def test_merge_outputs(self):
        state: AgentState = {"outputs": [1]}
        new_state = merge_outputs(state, [2, 3])
        self.assertEqual(new_state["outputs"], [1, 2, 3])

    def test_update_progress(self):
        state: AgentState = {"progress": 0.1}
        new_state = update_progress(state, 0.5)
        self.assertEqual(new_state["progress"], 0.5)

    def test_add_tool_result(self):
        state: AgentState = {"tool_results": {"t1": "old"}}
        new_state = add_tool_result(state, "t2", "new")
        self.assertEqual(new_state["tool_results"]["t2"], "new")

    def test_add_inter_agent_message(self):
        state: AgentState = {"inter_agent_comm": []}
        msg: Message = {"role": "agent", "content": "Ping", "timestamp": 456.0}
        new_state = add_inter_agent_message(state, msg)
        self.assertEqual(len(new_state["inter_agent_comm"]), 1)
        self.assertEqual(new_state["inter_agent_comm"][0]["content"], "Ping")

    def test_add_update(self):
        state: AgentState = {"updates": []}
        new_state = add_update(state, {"foo": "bar"})
        self.assertEqual(new_state["updates"][0]["foo"], "bar")

    def test_add_agent(self):
        system_state: SystemState = {"agents": {}}
        agent_state: AgentState = {"agent_id": "a1"}
        new_state = add_agent(system_state, "a1", agent_state)
        self.assertIn("a1", new_state["agents"])

    def test_serialize_deserialize(self):
        system_state: SystemState = {
            "agents": {"a1": {"agent_id": "a1", "messages": []}},
            "progress_board": [],
            "updates": []
        }
        s = serialize_state(system_state)
        restored = deserialize_state(s)
        self.assertEqual(restored["agents"]["a1"]["agent_id"], "a1")

if __name__ == "__main__":
    unittest.main()