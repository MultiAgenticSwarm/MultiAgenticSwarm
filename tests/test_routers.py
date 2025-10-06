"""
Comprehensive unit tests for routers module.

This test suite validates all router implementations including:
- BaseRouter: Tests base router functionality and history tracking
- SupervisorRouter: Tests LLM-based and capability-based routing
- LoadBalancerRouter: Tests load balancing strategies (round-robin, least-loaded, random, weighted)
- ConditionalRouter: Tests state-based conditional routing
- ConsensusRouter: Tests voting mechanisms (unanimous, majority, supermajority, weighted)
- SequentialRouter: Tests sequential execution flow
- ParallelRouter: Tests parallel execution and aggregation
"""

import pytest
from typing import Dict, Any, List
from collections import defaultdict
from multiagenticswarm.core.routers import (
    RoutingDecision,
    BaseRouter,
    SupervisorRouter,
    LoadBalancerRouter,
    ConditionalRouter,
    ConsensusRouter,
    SequentialRouter,
    ParallelRouter,
)


class TestRoutingDecision:
    """Test RoutingDecision class for routing metadata."""

    def test_basic_creation(self):
        """Test creating a routing decision with minimal parameters."""
        decision = RoutingDecision(next_node="agent1")

        assert decision.next_node == "agent1"
        assert decision.confidence == 1.0
        assert decision.reasoning is None
        assert decision.metadata == {}

    def test_full_creation(self):
        """Test creating a routing decision with all parameters."""
        decision = RoutingDecision(
            next_node="agent2",
            confidence=0.85,
            reasoning="Best match for capabilities",
            metadata={"score": 0.95, "method": "capability_based"}
        )

        assert decision.next_node == "agent2"
        assert decision.confidence == 0.85
        assert decision.reasoning == "Best match for capabilities"
        assert decision.metadata["score"] == 0.95
        assert decision.metadata["method"] == "capability_based"

    def test_string_representation(self):
        """Test string representation of routing decision."""
        decision = RoutingDecision(next_node="agent1", confidence=0.9)

        result = str(decision)

        assert "agent1" in result
        assert "0.9" in result


class TestBaseRouter:
    """Test BaseRouter abstract base class functionality."""

    def test_concrete_router_implementation(self):
        """Test that concrete router can be created from BaseRouter."""
        class SimpleRouter(BaseRouter):
            def route(self, state: Dict[str, Any]) -> str:
                return "agent1"

        router = SimpleRouter(name="TestRouter")

        assert router.name == "TestRouter"
        assert router.routing_history == []

    def test_route_with_metadata(self):
        """Test routing with metadata returns RoutingDecision."""
        class SimpleRouter(BaseRouter):
            def route(self, state: Dict[str, Any]) -> str:
                return "agent1"

        router = SimpleRouter()
        state = {"task": "test"}

        decision = router.route_with_metadata(state)

        assert isinstance(decision, RoutingDecision)
        assert decision.next_node == "agent1"
        assert decision.confidence == 1.0

    def test_routing_history_tracking(self):
        """Test that routing history is tracked correctly."""
        class SimpleRouter(BaseRouter):
            def route(self, state: Dict[str, Any]) -> str:
                return "agent1"

        router = SimpleRouter()

        # Make multiple routing decisions
        router.route_with_metadata({"task": "task1"})
        router.route_with_metadata({"task": "task2"})
        router.route_with_metadata({"task": "task3"})

        history = router.get_history()

        assert len(history) == 3
        assert all(isinstance(d, RoutingDecision) for d in history)

    def test_reset_history(self):
        """Test that routing history can be reset."""
        class SimpleRouter(BaseRouter):
            def route(self, state: Dict[str, Any]) -> str:
                return "agent1"

        router = SimpleRouter()

        # Add some history
        router.route_with_metadata({"task": "task1"})
        router.route_with_metadata({"task": "task2"})
        assert len(router.get_history()) == 2

        # Reset history
        router.reset_history()

        assert len(router.get_history()) == 0


class TestSupervisorRouter:
    """Test SupervisorRouter for LLM-based and capability-based routing."""

    def test_initialization(self):
        """Test supervisor router initialization."""
        agents = ["agent1", "agent2", "agent3"]
        capabilities = {
            "agent1": ["coding", "debugging"],
            "agent2": ["testing", "documentation"]
        }

        router = SupervisorRouter(
            agents=agents,
            agent_capabilities=capabilities,
            supervisor_node="supervisor",
            end_node="end"
        )

        assert router.agents == agents
        assert router.agent_capabilities == capabilities
        assert router.supervisor_node == "supervisor"
        assert router.end_node == "end"

    def test_route_from_supervisor_to_agent(self):
        """Test routing from supervisor node to an agent."""
        agents = ["agent1", "agent2"]
        capabilities = {
            "agent1": ["coding"],
            "agent2": ["testing"]
        }

        router = SupervisorRouter(agents=agents, agent_capabilities=capabilities)

        state = {
            "current_node": "supervisor",
            "task_requirements": ["coding"],
            "completed_agents": set()
        }

        next_node = router.route(state)

        # Should route to an agent (capability-based)
        assert next_node in agents

    def test_route_from_agent_to_end_when_complete(self):
        """Test routing from agent to end when task is complete."""
        agents = ["agent1", "agent2"]

        router = SupervisorRouter(agents=agents)

        state = {
            "current_node": "agent1",
            "task_complete": True
        }

        next_node = router.route(state)

        assert next_node == "end"

    def test_route_from_agent_to_supervisor(self):
        """Test routing from agent back to supervisor."""
        agents = ["agent1", "agent2"]

        router = SupervisorRouter(agents=agents)

        state = {
            "current_node": "agent1",
            "task_complete": False
        }

        next_node = router.route(state)

        assert next_node == "supervisor"

    def test_capability_based_agent_selection(self):
        """Test that agent is selected based on capabilities."""
        agents = ["coding_agent", "testing_agent"]
        capabilities = {
            "coding_agent": ["python", "javascript", "coding"],
            "testing_agent": ["unit_testing", "integration_testing"]
        }

        router = SupervisorRouter(agents=agents, agent_capabilities=capabilities)

        state = {
            "current_node": "supervisor",
            "task_requirements": ["coding", "python"],
            "completed_agents": set()
        }

        next_node = router.route(state)

        # Should select coding_agent based on capability match
        assert next_node == "coding_agent"

    def test_no_available_agents_routes_to_end(self):
        """Test routing to end when no agents are available."""
        agents = ["agent1", "agent2"]

        router = SupervisorRouter(agents=agents)

        state = {
            "current_node": "supervisor",
            "completed_agents": {"agent1", "agent2"}
        }

        next_node = router.route(state)

        assert next_node == "end"

    def test_agent_performance_tracking(self):
        """Test that agent performance is tracked over time."""
        agents = ["agent1"]

        router = SupervisorRouter(agents=agents)

        # Simulate multiple executions
        for i in range(5):
            state = {
                "current_node": "agent1",
                "agent1_performance": 0.8 + (i * 0.02)
            }
            router.route(state)

        # Check performance tracking
        assert "agent1" in router.agent_performance
        assert len(router.agent_performance["agent1"]) == 5


class TestLoadBalancerRouter:
    """Test LoadBalancerRouter for load distribution strategies."""

    def test_initialization(self):
        """Test load balancer router initialization."""
        agents = ["agent1", "agent2", "agent3"]

        router = LoadBalancerRouter(
            agents=agents,
            strategy="round_robin",
            aggregator_node="aggregator",
            end_node="end"
        )

        assert router.agents == agents
        assert router.strategy == "round_robin"
        assert router.aggregator_node == "aggregator"
        assert router.end_node == "end"

    def test_round_robin_strategy(self):
        """Test round-robin load balancing."""
        agents = ["agent1", "agent2", "agent3"]

        router = LoadBalancerRouter(agents=agents, strategy="round_robin")

        # Should cycle through agents in order
        state1 = {"current_node": "start"}
        state2 = {"current_node": "start"}
        state3 = {"current_node": "start"}
        state4 = {"current_node": "start"}

        result1 = router.route(state1)
        result2 = router.route(state2)
        result3 = router.route(state3)
        result4 = router.route(state4)

        # Should cycle: agent1, agent2, agent3, agent1
        assert result1 == "agent1"
        assert result2 == "agent2"
        assert result3 == "agent3"
        assert result4 == "agent1"

    def test_least_loaded_strategy(self):
        """Test least-loaded agent selection."""
        agents = ["agent1", "agent2", "agent3"]

        router = LoadBalancerRouter(agents=agents, strategy="least_loaded")

        # Manually set different loads
        router.agent_loads = {
            "agent1": 5,
            "agent2": 2,  # Least loaded
            "agent3": 3
        }

        state = {"current_node": "start"}
        next_node = router.route(state)

        # Should select agent2 (least loaded)
        assert next_node == "agent2"

    def test_random_strategy(self):
        """Test random agent selection."""
        agents = ["agent1", "agent2", "agent3"]

        router = LoadBalancerRouter(agents=agents, strategy="random")

        # Make multiple selections
        selections = []
        for _ in range(20):
            state = {"current_node": "start"}
            selections.append(router.route(state))

        # Should select from available agents
        assert all(s in agents for s in selections)
        # With 20 selections, we should see some variety (probabilistic)
        assert len(set(selections)) > 1

    def test_weighted_strategy(self):
        """Test weighted random selection."""
        agents = ["agent1", "agent2", "agent3"]
        weights = {
            "agent1": 1.0,
            "agent2": 5.0,  # Much higher weight
            "agent3": 1.0
        }

        router = LoadBalancerRouter(
            agents=agents,
            strategy="weighted",
            agent_weights=weights
        )

        # Make multiple selections
        selections = []
        for _ in range(100):
            state = {"current_node": "start"}
            selections.append(router.route(state))

        # agent2 should be selected more often due to higher weight
        agent2_count = selections.count("agent2")
        agent1_count = selections.count("agent1")

        # With 100 selections, agent2 should be selected more
        assert agent2_count > agent1_count

    def test_route_from_agent_to_aggregator(self):
        """Test routing from agent to aggregator."""
        agents = ["agent1", "agent2"]

        router = LoadBalancerRouter(agents=agents)

        state = {
            "current_node": "agent1",
            "completed_agents": {"agent1"}
        }

        next_node = router.route(state)

        assert next_node == "aggregator"

    def test_route_from_aggregator_to_end(self):
        """Test routing from aggregator to end when complete."""
        agents = ["agent1", "agent2"]

        router = LoadBalancerRouter(agents=agents)

        state = {
            "current_node": "aggregator",
            "all_complete": True
        }

        next_node = router.route(state)

        assert next_node == "end"

    def test_get_load_stats(self):
        """Test getting load statistics."""
        agents = ["agent1", "agent2"]

        router = LoadBalancerRouter(agents=agents, strategy="round_robin")

        # Make some routing decisions
        router.route({"current_node": "start"})
        router.route({"current_node": "start"})

        stats = router.get_load_stats()

        assert "agent_loads" in stats
        assert "total_completed" in stats
        assert "current_index" in stats

    def test_reset_loads(self):
        """Test resetting load tracking."""
        agents = ["agent1", "agent2"]

        router = LoadBalancerRouter(agents=agents, strategy="round_robin")

        # Make some routing decisions
        router.route({"current_node": "start"})
        router.route({"current_node": "start"})

        # Reset loads
        router.reset_loads()

        assert all(load == 0 for load in router.agent_loads.values())
        assert router.completed_count == 0
        assert router.current_index == 0


class TestConditionalRouter:
    """Test ConditionalRouter for state-based conditional routing."""

    def test_initialization(self):
        """Test conditional router initialization."""
        conditions = {
            "high_priority": lambda s: s.get("priority") == "high"
        }
        routing_map = {
            "high_priority": "priority_agent"
        }

        router = ConditionalRouter(
            conditions=conditions,
            routing_map=routing_map,
            default_route="default_agent"
        )

        assert "high_priority" in router.conditions
        assert router.routing_map["high_priority"] == "priority_agent"
        assert router.default_route == "default_agent"

    def test_route_with_matching_condition(self):
        """Test routing when a condition matches."""
        conditions = {
            "is_urgent": lambda s: s.get("urgent") == True
        }
        routing_map = {
            "is_urgent": "urgent_agent"
        }

        router = ConditionalRouter(
            conditions=conditions,
            routing_map=routing_map,
            default_route="normal_agent"
        )

        state = {"urgent": True}
        next_node = router.route(state)

        assert next_node == "urgent_agent"

    def test_route_with_no_matching_condition(self):
        """Test routing to default when no conditions match."""
        conditions = {
            "is_urgent": lambda s: s.get("urgent") == True
        }
        routing_map = {
            "is_urgent": "urgent_agent"
        }

        router = ConditionalRouter(
            conditions=conditions,
            routing_map=routing_map,
            default_route="normal_agent"
        )

        state = {"urgent": False}
        next_node = router.route(state)

        assert next_node == "normal_agent"

    def test_multiple_conditions_first_match_wins(self):
        """Test that first matching condition is used."""
        conditions = {
            "condition1": lambda s: s.get("value") > 5,
            "condition2": lambda s: s.get("value") > 3
        }
        routing_map = {
            "condition1": "agent1",
            "condition2": "agent2"
        }

        router = ConditionalRouter(
            conditions=conditions,
            routing_map=routing_map
        )

        state = {"value": 10}  # Matches both conditions
        next_node = router.route(state)

        # Should use first matching condition
        assert next_node == "agent1"

    def test_add_condition(self):
        """Test adding a new condition dynamically."""
        router = ConditionalRouter(
            conditions={},
            routing_map={},
            default_route="default"
        )

        # Add new condition
        router.add_condition(
            "new_condition",
            lambda s: s.get("status") == "active",
            "active_agent"
        )

        assert "new_condition" in router.conditions
        assert router.routing_map["new_condition"] == "active_agent"

    def test_remove_condition(self):
        """Test removing a condition."""
        conditions = {
            "condition1": lambda s: True
        }
        routing_map = {
            "condition1": "agent1"
        }

        router = ConditionalRouter(
            conditions=conditions,
            routing_map=routing_map
        )

        # Remove condition
        router.remove_condition("condition1")

        assert "condition1" not in router.conditions
        assert "condition1" not in router.routing_map

    def test_condition_error_handling(self):
        """Test that condition errors don't crash routing."""
        conditions = {
            "bad_condition": lambda s: s["nonexistent_key"]["nested"],
            "good_condition": lambda s: True
        }
        routing_map = {
            "bad_condition": "agent1",
            "good_condition": "agent2"
        }

        router = ConditionalRouter(
            conditions=conditions,
            routing_map=routing_map,
            default_route="default"
        )

        state = {"value": 1}
        next_node = router.route(state)

        # Should skip bad condition and use good one
        assert next_node == "agent2"


class TestConsensusRouter:
    """Test ConsensusRouter for voting-based routing."""

    def test_initialization(self):
        """Test consensus router initialization."""
        agents = ["agent1", "agent2", "agent3"]

        router = ConsensusRouter(
            agents=agents,
            voting_method="majority",
            vote_threshold=0.5,
            decision_node="decision",
            end_node="end"
        )

        assert router.agents == agents
        assert router.voting_method == "majority"
        assert router.vote_threshold == 0.5

    def test_unanimous_vote_success(self):
        """Test unanimous voting when all agree."""
        agents = ["agent1", "agent2", "agent3"]

        router = ConsensusRouter(agents=agents, voting_method="unanimous")

        state = {
            "current_node": "decision",
            "agent1_vote": "approve",
            "agent2_vote": "approve",
            "agent3_vote": "approve"
        }

        consensus = router._evaluate_consensus(state)

        assert consensus is True
        assert state["majority_vote"] == "approve"

    def test_unanimous_vote_failure(self):
        """Test unanimous voting when not all agree."""
        agents = ["agent1", "agent2", "agent3"]

        router = ConsensusRouter(agents=agents, voting_method="unanimous")

        state = {
            "current_node": "decision",
            "agent1_vote": "approve",
            "agent2_vote": "approve",
            "agent3_vote": "reject"
        }

        consensus = router._evaluate_consensus(state)

        assert consensus is False

    def test_majority_vote_success(self):
        """Test majority voting when majority agrees."""
        agents = ["agent1", "agent2", "agent3"]

        router = ConsensusRouter(agents=agents, voting_method="majority")

        state = {
            "current_node": "decision",
            "agent1_vote": "approve",
            "agent2_vote": "approve",
            "agent3_vote": "reject"
        }

        consensus = router._evaluate_consensus(state)

        assert consensus is True
        assert state["majority_vote"] == "approve"

    def test_majority_vote_failure(self):
        """Test majority voting when no majority exists."""
        agents = ["agent1", "agent2"]

        router = ConsensusRouter(agents=agents, voting_method="majority")

        state = {
            "current_node": "decision",
            "agent1_vote": "approve",
            "agent2_vote": "reject"
        }

        consensus = router._evaluate_consensus(state)

        assert consensus is False  # 50/50 split, no majority

    def test_supermajority_vote(self):
        """Test supermajority voting with custom threshold."""
        agents = ["agent1", "agent2", "agent3", "agent4"]

        router = ConsensusRouter(
            agents=agents,
            voting_method="supermajority",
            vote_threshold=0.75  # 75% required
        )

        # 3 out of 4 = 75%
        state = {
            "current_node": "decision",
            "agent1_vote": "approve",
            "agent2_vote": "approve",
            "agent3_vote": "approve",
            "agent4_vote": "reject"
        }

        consensus = router._evaluate_consensus(state)

        assert consensus is True
        assert state["vote_percentage"] == 0.75

    def test_weighted_vote(self):
        """Test weighted voting where agents have different weights."""
        agents = ["agent1", "agent2", "agent3"]
        weights = {
            "agent1": 2.0,  # Double weight
            "agent2": 1.0,
            "agent3": 1.0
        }

        router = ConsensusRouter(
            agents=agents,
            voting_method="weighted",
            agent_weights=weights
        )

        # agent1 (weight 2.0) votes approve, others vote reject
        # Total weight: 4.0, approve weight: 2.0 (50% - not majority)
        state = {
            "current_node": "decision",
            "agent1_vote": "approve",
            "agent2_vote": "reject",
            "agent3_vote": "reject"
        }

        consensus = router._evaluate_consensus(state)

        # 50% is not > 50%, so no consensus
        assert consensus is False

    def test_route_from_agent_to_decision(self):
        """Test routing from agent to decision node."""
        agents = ["agent1", "agent2"]

        router = ConsensusRouter(agents=agents)

        state = {
            "current_node": "agent1",
            "completed_agents": {"agent1", "agent2"}
        }

        next_node = router.route(state)

        assert next_node == "decision"

    def test_route_from_decision_to_end_with_consensus(self):
        """Test routing from decision to end when consensus reached."""
        agents = ["agent1", "agent2"]

        router = ConsensusRouter(agents=agents, voting_method="majority")

        state = {
            "current_node": "decision",
            "agent1_vote": "approve",
            "agent2_vote": "approve"
        }

        next_node = router.route(state)

        assert next_node == "end"
        assert state.get("consensus_reached") is True

    def test_get_vote_summary(self):
        """Test getting vote summary statistics."""
        agents = ["agent1", "agent2", "agent3"]

        router = ConsensusRouter(agents=agents, voting_method="majority")

        state = {
            "agent1_vote": "approve",
            "agent2_vote": "approve",
            "agent3_vote": "reject",
            "consensus_reached": True,
            "majority_vote": "approve"
        }

        summary = router.get_vote_summary(state)

        assert summary["total_votes"] == 3
        assert summary["vote_distribution"]["approve"] == 2
        assert summary["vote_distribution"]["reject"] == 1
        assert summary["consensus_reached"] is True
        assert summary["winning_vote"] == "approve"


class TestSequentialRouter:
    """Test SequentialRouter for sequential execution flow."""

    def test_initialization(self):
        """Test sequential router initialization."""
        sequence = ["agent1", "agent2", "agent3"]

        router = SequentialRouter(
            sequence=sequence,
            end_node="end",
            skip_on_error=False
        )

        assert router.sequence == sequence
        assert router.end_node == "end"
        assert router.skip_on_error is False

    def test_route_through_sequence(self):
        """Test routing through the sequence in order."""
        sequence = ["agent1", "agent2", "agent3"]

        router = SequentialRouter(sequence=sequence)

        # Start from beginning
        state1 = {"current_node": "start"}
        next1 = router.route(state1)
        assert next1 == "agent1"

        # Move to next
        state2 = {"current_node": "agent1"}
        next2 = router.route(state2)
        assert next2 == "agent2"

        # Move to next
        state3 = {"current_node": "agent2"}
        next3 = router.route(state3)
        assert next3 == "agent3"

        # End of sequence
        state4 = {"current_node": "agent3"}
        next4 = router.route(state4)
        assert next4 == "end"

    def test_skip_on_error(self):
        """Test skipping to next agent on error when enabled."""
        sequence = ["agent1", "agent2", "agent3"]

        router = SequentialRouter(sequence=sequence, skip_on_error=True)

        # Agent1 has error
        state = {
            "current_node": "agent1",
            "agent1_error": True
        }

        next_node = router.route(state)

        # Should skip to agent2
        assert next_node == "agent2"

    def test_no_skip_on_error(self):
        """Test normal progression even with error when skip disabled."""
        sequence = ["agent1", "agent2", "agent3"]

        router = SequentialRouter(sequence=sequence, skip_on_error=False)

        # Agent1 has error but skip is disabled
        state = {
            "current_node": "agent1",
            "agent1_error": True
        }

        next_node = router.route(state)

        # Should still go to agent2 (normal progression)
        assert next_node == "agent2"

    def test_reset_sequence(self):
        """Test resetting sequence to beginning."""
        sequence = ["agent1", "agent2"]

        router = SequentialRouter(sequence=sequence)

        # Progress through sequence
        router.current_index = 2

        # Reset
        router.reset_sequence()

        assert router.current_index == 0


class TestParallelRouter:
    """Test ParallelRouter for parallel execution patterns."""

    def test_initialization(self):
        """Test parallel router initialization."""
        agents = ["agent1", "agent2", "agent3"]

        router = ParallelRouter(
            agents=agents,
            aggregator_node="aggregator",
            end_node="end",
            wait_for_all=True
        )

        assert router.agents == agents
        assert router.aggregator_node == "aggregator"
        assert router.end_node == "end"
        assert router.wait_for_all is True

    def test_initial_fanout(self):
        """Test initial fanout to first agent."""
        agents = ["agent1", "agent2", "agent3"]

        router = ParallelRouter(agents=agents)

        state = {"current_node": "start"}
        next_node = router.route(state)

        # Should return first agent (LangGraph handles parallel execution)
        assert next_node == "agent1"

    def test_route_to_aggregator_when_all_complete(self):
        """Test routing to aggregator when all agents complete."""
        agents = ["agent1", "agent2", "agent3"]

        router = ParallelRouter(agents=agents, wait_for_all=True)

        state = {
            "current_node": "agent1",
            "completed_agents": {"agent1", "agent2", "agent3"}
        }

        next_node = router.route(state)

        assert next_node == "aggregator"

    def test_wait_when_not_all_complete(self):
        """Test waiting when not all agents complete and wait_for_all=True."""
        agents = ["agent1", "agent2", "agent3"]

        router = ParallelRouter(agents=agents, wait_for_all=True)

        state = {
            "current_node": "agent1",
            "completed_agents": {"agent1"}  # Only 1 of 3 complete
        }

        next_node = router.route(state)

        # Should stay in current node (waiting)
        assert next_node == "agent1"

    def test_no_wait_goes_to_aggregator_immediately(self):
        """Test going to aggregator immediately when wait_for_all=False."""
        agents = ["agent1", "agent2", "agent3"]

        router = ParallelRouter(agents=agents, wait_for_all=False)

        state = {
            "current_node": "agent1",
            "completed_agents": {"agent1"}
        }

        next_node = router.route(state)

        # Should go to aggregator immediately
        assert next_node == "aggregator"

    def test_route_from_aggregator_to_end(self):
        """Test routing from aggregator to end."""
        agents = ["agent1", "agent2"]

        router = ParallelRouter(agents=agents)

        state = {"current_node": "aggregator"}
        next_node = router.route(state)

        assert next_node == "end"

    def test_get_completion_status(self):
        """Test getting completion status of parallel execution."""
        agents = ["agent1", "agent2", "agent3", "agent4"]

        router = ParallelRouter(agents=agents)

        state = {
            "completed_agents": {"agent1", "agent2"}  # 2 of 4 complete
        }

        status = router.get_completion_status(state)

        assert status["total_agents"] == 4
        assert status["completed_agents"] == 2
        assert status["pending_agents"] == 2
        assert status["completion_percentage"] == 0.5
        assert status["all_complete"] is False


# Integration tests

class TestRouterIntegration:
    """Integration tests combining multiple router types."""

    def test_supervisor_with_conditional_routing(self):
        """Test combining supervisor and conditional routing logic."""
        # Supervisor router
        supervisor = SupervisorRouter(
            agents=["specialist", "generalist"],
            agent_capabilities={
                "specialist": ["advanced_task"],
                "generalist": ["basic_task"]
            }
        )

        # Conditional router
        conditional = ConditionalRouter(
            conditions={
                "is_complex": lambda s: s.get("complexity") == "high"
            },
            routing_map={
                "is_complex": "specialist"
            },
            default_route="generalist"
        )

        # Test complex task
        state_complex = {"complexity": "high"}
        result = conditional.route(state_complex)
        assert result == "specialist"

        # Test simple task
        state_simple = {"complexity": "low"}
        result = conditional.route(state_simple)
        assert result == "generalist"

    def test_load_balancer_with_consensus(self):
        """Test load balancing followed by consensus."""
        # Load balancer distributes work
        load_balancer = LoadBalancerRouter(
            agents=["agent1", "agent2", "agent3"],
            strategy="round_robin"
        )

        # Consensus router evaluates results
        consensus = ConsensusRouter(
            agents=["agent1", "agent2", "agent3"],
            voting_method="majority"
        )

        # Distribute work
        assignments = []
        for i in range(3):
            state = {"current_node": "start"}
            assignments.append(load_balancer.route(state))

        # Each agent should get one task
        assert set(assignments) == {"agent1", "agent2", "agent3"}

        # Then evaluate consensus
        state = {
            "current_node": "decision",
            "agent1_vote": "approve",
            "agent2_vote": "approve",
            "agent3_vote": "reject"
        }

        consensus_result = consensus._evaluate_consensus(state)
        assert consensus_result is True  # Majority wins


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

