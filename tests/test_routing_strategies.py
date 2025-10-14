"""
Comprehensive unit tests for routing strategies module.

This test suite validates all routing strategy classes and functions including:
- CapabilityMatcher: Tests capability matching and scoring
- PerformanceTracker: Tests performance metrics tracking and ranking
- ConditionalEvaluator: Tests condition evaluation logic
- HybridStrategy: Tests strategy combination methods
- Utility functions: Tests helper functions for creating routers
"""

import pytest
from typing import Dict, Any
from multiagenticswarm.core.routing_strategies import (
    RoutingStrategy,
    AgentCapability,
    RoutingContext,
    CapabilityMatcher,
    PerformanceTracker,
    ConditionalEvaluator,
    HybridStrategy,
    create_state_condition,
    create_capability_router,
    create_performance_router,
)


class TestRoutingStrategyEnum:
    """Test RoutingStrategy enumeration."""

    def test_enum_values(self):
        """Test that all expected routing strategies are defined."""
        assert RoutingStrategy.CAPABILITY_BASED.value == "capability_based"
        assert RoutingStrategy.PERFORMANCE_BASED.value == "performance_based"
        assert RoutingStrategy.LOAD_BALANCED.value == "load_balanced"
        assert RoutingStrategy.PRIORITY_BASED.value == "priority_based"
        assert RoutingStrategy.ROUND_ROBIN.value == "round_robin"
        assert RoutingStrategy.RANDOM.value == "random"
        assert RoutingStrategy.CONDITIONAL.value == "conditional"
        assert RoutingStrategy.HYBRID.value == "hybrid"

    def test_enum_membership(self):
        """Test that strategy names can be used to check membership."""
        assert "capability_based" in [s.value for s in RoutingStrategy]
        assert "hybrid" in [s.value for s in RoutingStrategy]


class TestAgentCapability:
    """Test AgentCapability dataclass."""

    def test_basic_creation(self):
        """Test creating a capability with minimal parameters."""
        cap = AgentCapability(name="coding", description="Write code")

        assert cap.name == "coding"
        assert cap.description == "Write code"
        assert cap.proficiency == 1.0
        assert cap.tags == []

    def test_full_creation(self):
        """Test creating a capability with all parameters."""
        cap = AgentCapability(
            name="data_analysis",
            description="Analyze data and generate insights",
            proficiency=0.85,
            tags=["analysis", "data", "statistics"]
        )

        assert cap.name == "data_analysis"
        assert cap.description == "Analyze data and generate insights"
        assert cap.proficiency == 0.85
        assert cap.tags == ["analysis", "data", "statistics"]

    def test_default_tags_initialization(self):
        """Test that tags default to empty list, not shared instance."""
        cap1 = AgentCapability(name="cap1", description="desc1")
        cap2 = AgentCapability(name="cap2", description="desc2")

        cap1.tags.append("test")

        assert "test" in cap1.tags
        assert "test" not in cap2.tags


class TestCapabilityMatcher:
    """Test CapabilityMatcher class for agent-task matching."""

    def test_initialization(self):
        """Test that matcher initializes with empty registry."""
        matcher = CapabilityMatcher()

        assert matcher.agent_capabilities == {}

    def test_register_agent(self):
        """Test registering an agent with capabilities."""
        matcher = CapabilityMatcher()

        capabilities = [
            AgentCapability("coding", "Write code", proficiency=0.9),
            AgentCapability("debugging", "Fix bugs", proficiency=0.8)
        ]

        matcher.register_agent("Agent1", capabilities)

        assert "Agent1" in matcher.agent_capabilities
        assert len(matcher.agent_capabilities["Agent1"]) == 2
        assert matcher.agent_capabilities["Agent1"][0].name == "coding"

    def test_exact_match(self):
        """Test exact capability name matching."""
        matcher = CapabilityMatcher()

        capabilities = [
            AgentCapability("coding", "Write code", proficiency=1.0)
        ]

        matcher.register_agent("Agent1", capabilities)

        matches = matcher.match_agents(["coding"], min_proficiency=0.5)

        assert len(matches) == 1
        assert matches[0][0] == "Agent1"
        assert matches[0][1] == 1.0  # Perfect match score

    def test_substring_match(self):
        """Test substring capability matching."""
        matcher = CapabilityMatcher()

        capabilities = [
            AgentCapability("python_coding", "Write Python code", proficiency=1.0)
        ]

        matcher.register_agent("Agent1", capabilities)

        matches = matcher.match_agents(["coding"], min_proficiency=0.5)

        assert len(matches) == 1
        assert matches[0][0] == "Agent1"
        assert matches[0][1] == 0.8  # Substring match score

    def test_tag_match(self):
        """Test tag-based capability matching."""
        matcher = CapabilityMatcher()

        capabilities = [
            AgentCapability(
                "development",
                "Software development",
                proficiency=1.0,
                tags=["coding", "programming", "software"]
            )
        ]

        matcher.register_agent("Agent1", capabilities)

        matches = matcher.match_agents(["coding"], min_proficiency=0.5)

        assert len(matches) == 1
        assert matches[0][0] == "Agent1"
        assert matches[0][1] == 0.9  # Tag exact match score

    def test_proficiency_filtering(self):
        """Test that low proficiency agents are filtered out."""
        matcher = CapabilityMatcher()

        capabilities1 = [
            AgentCapability("coding", "Write code", proficiency=0.3)
        ]
        capabilities2 = [
            AgentCapability("coding", "Write code", proficiency=0.8)
        ]

        matcher.register_agent("Agent1", capabilities1)
        matcher.register_agent("Agent2", capabilities2)

        matches = matcher.match_agents(["coding"], min_proficiency=0.5)

        # Only Agent2 should match (proficiency >= 0.5)
        assert len(matches) == 1
        assert matches[0][0] == "Agent2"

    def test_ranking_by_score(self):
        """Test that agents are ranked by match score."""
        matcher = CapabilityMatcher()

        capabilities1 = [
            AgentCapability("coding", "Write code", proficiency=0.7)
        ]
        capabilities2 = [
            AgentCapability("coding", "Write code", proficiency=1.0)
        ]

        matcher.register_agent("Agent1", capabilities1)
        matcher.register_agent("Agent2", capabilities2)

        matches = matcher.match_agents(["coding"], min_proficiency=0.5)

        # Agent2 should be first (higher proficiency)
        assert len(matches) == 2
        assert matches[0][0] == "Agent2"
        assert matches[1][0] == "Agent1"
        assert matches[0][1] > matches[1][1]

    def test_multiple_requirements(self):
        """Test matching with multiple requirements."""
        matcher = CapabilityMatcher()

        capabilities1 = [
            AgentCapability("coding", "Write code", proficiency=1.0),
        ]
        capabilities2 = [
            AgentCapability("coding", "Write code", proficiency=1.0),
            AgentCapability("testing", "Test code", proficiency=1.0),
        ]

        matcher.register_agent("Agent1", capabilities1)
        matcher.register_agent("Agent2", capabilities2)

        matches = matcher.match_agents(["coding", "testing"], min_proficiency=0.5)

        # Agent2 should rank higher (meets both requirements)
        assert len(matches) == 2
        assert matches[0][0] == "Agent2"
        assert matches[0][1] > matches[1][1]

    def test_no_requirements(self):
        """Test that empty requirements matches all agents."""
        matcher = CapabilityMatcher()

        capabilities = [
            AgentCapability("coding", "Write code", proficiency=1.0)
        ]

        matcher.register_agent("Agent1", capabilities)

        matches = matcher.match_agents([], min_proficiency=0.5)

        assert len(matches) == 1
        assert matches[0][1] == 1.0  # Perfect score for no requirements


class TestPerformanceTracker:
    """Test PerformanceTracker class for agent performance monitoring."""

    def test_initialization(self):
        """Test tracker initializes with empty metrics."""
        tracker = PerformanceTracker(history_size=50)

        assert tracker.history_size == 50
        assert tracker.agent_metrics == {}

    def test_record_execution(self):
        """Test recording an execution result."""
        tracker = PerformanceTracker()

        tracker.record_execution("Agent1", success=True, execution_time=1.5, quality_score=0.9)

        assert "Agent1" in tracker.agent_metrics
        assert tracker.agent_metrics["Agent1"]["success"] == [1.0]
        assert tracker.agent_metrics["Agent1"]["execution_time"] == [1.5]
        assert tracker.agent_metrics["Agent1"]["quality"] == [0.9]

    def test_multiple_recordings(self):
        """Test recording multiple executions."""
        tracker = PerformanceTracker()

        tracker.record_execution("Agent1", success=True, execution_time=1.0)
        tracker.record_execution("Agent1", success=False, execution_time=2.0)
        tracker.record_execution("Agent1", success=True, execution_time=1.5)

        assert len(tracker.agent_metrics["Agent1"]["success"]) == 3
        assert tracker.agent_metrics["Agent1"]["success"] == [1.0, 0.0, 1.0]

    def test_history_size_limit(self):
        """Test that history is trimmed to size limit."""
        tracker = PerformanceTracker(history_size=3)

        for i in range(5):
            tracker.record_execution("Agent1", success=True, execution_time=float(i))

        # Should only keep last 3 records
        assert len(tracker.agent_metrics["Agent1"]["execution_time"]) == 3
        assert tracker.agent_metrics["Agent1"]["execution_time"] == [2.0, 3.0, 4.0]

    def test_get_success_rate(self):
        """Test calculating success rate."""
        tracker = PerformanceTracker()

        tracker.record_execution("Agent1", success=True, execution_time=1.0)
        tracker.record_execution("Agent1", success=True, execution_time=1.0)
        tracker.record_execution("Agent1", success=False, execution_time=1.0)
        tracker.record_execution("Agent1", success=True, execution_time=1.0)

        success_rate = tracker.get_success_rate("Agent1")

        assert success_rate == 0.75  # 3 out of 4 successful

    def test_get_success_rate_no_history(self):
        """Test that default success rate is 1.0 with no history."""
        tracker = PerformanceTracker()

        success_rate = tracker.get_success_rate("UnknownAgent")

        assert success_rate == 1.0

    def test_get_avg_execution_time(self):
        """Test calculating average execution time."""
        tracker = PerformanceTracker()

        tracker.record_execution("Agent1", success=True, execution_time=1.0)
        tracker.record_execution("Agent1", success=True, execution_time=2.0)
        tracker.record_execution("Agent1", success=True, execution_time=3.0)

        avg_time = tracker.get_avg_execution_time("Agent1")

        assert avg_time == 2.0

    def test_get_quality_score(self):
        """Test calculating average quality score."""
        tracker = PerformanceTracker()

        tracker.record_execution("Agent1", success=True, execution_time=1.0, quality_score=0.8)
        tracker.record_execution("Agent1", success=True, execution_time=1.0, quality_score=0.9)
        tracker.record_execution("Agent1", success=True, execution_time=1.0, quality_score=1.0)

        quality = tracker.get_quality_score("Agent1")

        assert quality == 0.9

    def test_get_performance_score(self):
        """Test calculating overall performance score."""
        tracker = PerformanceTracker()

        # Record perfect performance for multiple agents to get proper normalization
        tracker.record_execution("Agent1", success=True, execution_time=1.0, quality_score=1.0)
        tracker.record_execution("Agent2", success=True, execution_time=2.0, quality_score=0.8)

        score = tracker.get_performance_score("Agent1")

        # Should be high (weighted combination of metrics)
        # Agent1 has perfect success (1.0), fastest speed (0.5 normalized), perfect quality (1.0)
        # Score = 0.4 * 1.0 + 0.3 * 0.5 + 0.3 * 1.0 = 0.85
        assert 0.0 <= score <= 1.0
        assert score >= 0.8  # Should be high for good performance

    def test_get_performance_score_custom_weights(self):
        """Test performance score with custom weights."""
        tracker = PerformanceTracker()

        tracker.record_execution("Agent1", success=True, execution_time=1.0, quality_score=0.5)

        # Weight success heavily
        weights = {"success": 1.0, "speed": 0.0, "quality": 0.0}
        score = tracker.get_performance_score("Agent1", weights)

        assert score == 1.0  # Only success matters

    def test_rank_agents(self):
        """Test ranking multiple agents by performance."""
        tracker = PerformanceTracker()

        # Agent1: High success, slow
        tracker.record_execution("Agent1", success=True, execution_time=10.0, quality_score=1.0)
        tracker.record_execution("Agent1", success=True, execution_time=10.0, quality_score=1.0)

        # Agent2: Medium success, fast
        tracker.record_execution("Agent2", success=True, execution_time=1.0, quality_score=0.8)
        tracker.record_execution("Agent2", success=False, execution_time=1.0, quality_score=0.8)

        # Agent3: Low success, fast
        tracker.record_execution("Agent3", success=False, execution_time=1.0, quality_score=0.5)

        rankings = tracker.rank_agents(["Agent1", "Agent2", "Agent3"])

        assert len(rankings) == 3
        # Rankings should be sorted by score (highest first)
        assert rankings[0][1] >= rankings[1][1] >= rankings[2][1]


class TestConditionalEvaluator:
    """Test ConditionalEvaluator class for condition evaluation."""

    def test_initialization(self):
        """Test evaluator initializes with empty custom evaluators."""
        evaluator = ConditionalEvaluator()

        assert evaluator.custom_evaluators == {}

    def test_register_custom_evaluator(self):
        """Test registering a custom evaluator function."""
        evaluator = ConditionalEvaluator()

        def custom_check(state: Dict[str, Any]) -> bool:
            return state.get("value", 0) > 5

        evaluator.register_evaluator("high_value", custom_check)

        assert "high_value" in evaluator.custom_evaluators

    def test_equality_comparison(self):
        """Test == operator in condition."""
        evaluator = ConditionalEvaluator()
        state = {"status": "active"}

        result = evaluator.evaluate("status == active", state)

        assert result is True

    def test_inequality_comparison(self):
        """Test != operator in condition."""
        evaluator = ConditionalEvaluator()
        state = {"status": "active"}

        result = evaluator.evaluate("status != inactive", state)

        assert result is True

    def test_greater_than_comparison(self):
        """Test > operator in condition."""
        evaluator = ConditionalEvaluator()
        state = {"count": 10}

        result = evaluator.evaluate("count > 5", state)

        assert result is True

    def test_less_than_comparison(self):
        """Test < operator in condition."""
        evaluator = ConditionalEvaluator()
        state = {"count": 3}

        result = evaluator.evaluate("count < 5", state)

        assert result is True

    def test_and_operator(self):
        """Test AND logical operator."""
        evaluator = ConditionalEvaluator()
        state = {"count": 10, "status": "active"}

        result = evaluator.evaluate("count > 5 AND status == active", state)

        assert result is True

    def test_or_operator(self):
        """Test OR logical operator."""
        evaluator = ConditionalEvaluator()
        state = {"count": 3, "status": "active"}

        result = evaluator.evaluate("count > 5 OR status == active", state)

        assert result is True

    def test_not_operator(self):
        """Test NOT logical operator."""
        evaluator = ConditionalEvaluator()
        state = {"enabled": False}

        result = evaluator.evaluate("NOT enabled", state)

        assert result is True

    def test_nested_state_access(self):
        """Test dot notation for nested state access."""
        evaluator = ConditionalEvaluator()
        state = {
            "user": {
                "profile": {
                    "name": "John"
                }
            }
        }

        result = evaluator.evaluate("user.profile.name == John", state)

        assert result is True

    def test_boolean_parsing(self):
        """Test parsing boolean values in conditions."""
        evaluator = ConditionalEvaluator()
        state = {"enabled": True}

        result = evaluator.evaluate("enabled == true", state)

        assert result is True

    def test_number_parsing(self):
        """Test parsing integer and float values."""
        evaluator = ConditionalEvaluator()
        state = {"count": 42, "rate": 3.14}

        assert evaluator.evaluate("count == 42", state) is True
        assert evaluator.evaluate("rate > 3.0", state) is True

    def test_list_parsing(self):
        """Test parsing list values in conditions."""
        evaluator = ConditionalEvaluator()
        state = {"item": "apple"}

        result = evaluator.evaluate("item in [apple, banana, orange]", state)

        assert result is True

    def test_custom_evaluator_execution(self):
        """Test executing registered custom evaluator."""
        evaluator = ConditionalEvaluator()

        def is_premium(state: Dict[str, Any]) -> bool:
            return state.get("tier") == "premium"

        evaluator.register_evaluator("is_premium", is_premium)

        state = {"tier": "premium"}
        result = evaluator.evaluate("is_premium", state)

        assert result is True

    def test_invalid_comparison_returns_false(self):
        """Test that invalid comparisons return False instead of raising errors."""
        evaluator = ConditionalEvaluator()
        state = {"value": "text"}

        # Comparing string to number should return False, not error
        result = evaluator.evaluate("value > 10", state)

        assert result is False


class TestHybridStrategy:
    """Test HybridStrategy class for combining routing strategies."""

    def test_initialization(self):
        """Test hybrid strategy initializes with empty strategies."""
        strategy = HybridStrategy()

        assert strategy.strategies == {}
        assert strategy.strategy_weights == {}

    def test_add_strategy(self):
        """Test adding a strategy to the hybrid."""
        strategy = HybridStrategy()

        def simple_router(state: Dict[str, Any]) -> str:
            return "agent1"

        strategy.add_strategy("simple", simple_router, weight=1.5)

        assert "simple" in strategy.strategies
        assert strategy.strategy_weights["simple"] == 1.5

    def test_route_by_condition(self):
        """Test routing based on first matching condition."""
        strategy = HybridStrategy()

        def route_to_a(state: Dict[str, Any]) -> str:
            return "agentA"

        def route_to_b(state: Dict[str, Any]) -> str:
            return "agentB"

        strategy.add_strategy("strategyA", route_to_a)
        strategy.add_strategy("strategyB", route_to_b)

        conditions = {
            "strategyA": lambda s: s.get("type") == "typeA",
            "strategyB": lambda s: s.get("type") == "typeB",
        }

        state = {"type": "typeA"}
        result = strategy.route_by_condition(state, conditions)

        assert result == "agentA"

    def test_route_by_consensus(self):
        """Test routing by majority vote."""
        strategy = HybridStrategy()

        # Three strategies, two vote for agentA
        strategy.add_strategy("s1", lambda s: "agentA")
        strategy.add_strategy("s2", lambda s: "agentA")
        strategy.add_strategy("s3", lambda s: "agentB")

        state = {}
        result = strategy.route_by_consensus(state)

        assert result == "agentA"  # Majority vote

    def test_route_by_weighted_vote(self):
        """Test routing by weighted vote."""
        strategy = HybridStrategy()

        # agentB has higher total weight
        strategy.add_strategy("s1", lambda s: "agentA", weight=1.0)
        strategy.add_strategy("s2", lambda s: "agentB", weight=2.0)

        state = {}
        result = strategy.route_by_weighted_vote(state)

        assert result == "agentB"  # Higher weighted vote


class TestUtilityFunctions:
    """Test utility functions for creating routers."""

    def test_create_state_condition(self):
        """Test creating a state condition function."""
        condition_func = create_state_condition("count", ">", "5")

        state_true = {"count": 10}
        state_false = {"count": 3}

        assert condition_func(state_true) is True
        assert condition_func(state_false) is False

    def test_create_capability_router(self):
        """Test creating a capability-based router."""
        matcher = CapabilityMatcher()

        capabilities = [
            AgentCapability("coding", "Write code", proficiency=1.0)
        ]
        matcher.register_agent("CodeAgent", capabilities)

        router = create_capability_router(matcher, min_proficiency=0.5)

        state = {"task_requirements": ["coding"]}
        result = router(state)

        assert result == "CodeAgent"

    def test_create_capability_router_no_match(self):
        """Test capability router with no matching agents."""
        matcher = CapabilityMatcher()

        router = create_capability_router(matcher)

        state = {"task_requirements": ["nonexistent"], "default_agent": "DefaultAgent"}
        result = router(state)

        assert result == "DefaultAgent"

    def test_create_performance_router(self):
        """Test creating a performance-based router."""
        tracker = PerformanceTracker()

        # Agent1 performs better
        tracker.record_execution("Agent1", success=True, execution_time=1.0, quality_score=1.0)
        tracker.record_execution("Agent1", success=True, execution_time=1.0, quality_score=1.0)

        tracker.record_execution("Agent2", success=False, execution_time=5.0, quality_score=0.5)

        router = create_performance_router(tracker, ["Agent1", "Agent2"])

        state = {}
        result = router(state)

        assert result == "Agent1"  # Better performance

    def test_create_performance_router_no_data(self):
        """Test performance router with no performance data."""
        tracker = PerformanceTracker()

        router = create_performance_router(tracker, ["Agent1", "Agent2"])

        state = {}
        result = router(state)

        # Should return first agent when no data
        assert result == "Agent1"

    def test_create_performance_router_empty_agents(self):
        """Test performance router with no agents."""
        tracker = PerformanceTracker()

        router = create_performance_router(tracker, [])

        state = {}
        result = router(state)

        assert result == "end"  # Default when no agents


class TestRoutingContext:
    """Test RoutingContext dataclass."""

    def test_routing_context_creation(self):
        """Test creating a routing context with all fields."""
        context = RoutingContext(
            current_node="node1",
            task="Process data",
            requirements=["data_processing", "analysis"],
            state={"status": "active"},
            history=["node0", "node1"],
            metadata={"priority": "high"}
        )

        assert context.current_node == "node1"
        assert context.task == "Process data"
        assert context.requirements == ["data_processing", "analysis"]
        assert context.state == {"status": "active"}
        assert context.history == ["node0", "node1"]
        assert context.metadata == {"priority": "high"}


# Integration tests combining multiple components

class TestIntegration:
    """Integration tests combining multiple routing strategy components."""

    def test_capability_and_performance_routing(self):
        """Test combining capability matching with performance tracking."""
        # Setup capability matcher
        matcher = CapabilityMatcher()

        cap1 = [AgentCapability("coding", "Code", proficiency=1.0)]
        cap2 = [AgentCapability("coding", "Code", proficiency=0.9)]

        matcher.register_agent("Agent1", cap1)
        matcher.register_agent("Agent2", cap2)

        # Setup performance tracker
        tracker = PerformanceTracker()

        # Agent2 has better performance despite lower capability
        tracker.record_execution("Agent1", success=False, execution_time=10.0)
        tracker.record_execution("Agent2", success=True, execution_time=1.0)

        # Get both recommendations
        cap_matches = matcher.match_agents(["coding"], min_proficiency=0.5)
        perf_rankings = tracker.rank_agents(["Agent1", "Agent2"])

        # Capability matcher prefers Agent1 (higher proficiency)
        assert cap_matches[0][0] == "Agent1"

        # Performance tracker prefers Agent2 (better performance)
        assert perf_rankings[0][0] == "Agent2"

    def test_hybrid_strategy_with_conditions(self):
        """Test using hybrid strategy to combine multiple routing approaches."""
        # Create hybrid strategy
        hybrid = HybridStrategy()

        # Add capability-based strategy
        matcher = CapabilityMatcher()
        matcher.register_agent("SpecialistAgent", [
            AgentCapability("specialized_task", "Special", proficiency=1.0)
        ])
        cap_router = create_capability_router(matcher)
        hybrid.add_strategy("capability", cap_router, weight=1.0)

        # Add simple fallback strategy
        hybrid.add_strategy("fallback", lambda s: "GeneralistAgent", weight=0.5)

        # Test with matching requirements
        state = {"task_requirements": ["specialized_task"]}
        result = hybrid.route_by_weighted_vote(state)

        # Should route to specialist when requirements match
        assert result == "SpecialistAgent"

    def test_conditional_routing_with_evaluator(self):
        """Test conditional routing using ConditionalEvaluator."""
        evaluator = ConditionalEvaluator()

        # Register custom condition
        def is_urgent(state: Dict[str, Any]) -> bool:
            return state.get("priority") == "urgent"

        evaluator.register_evaluator("is_urgent", is_urgent)

        # Use in routing decision
        state_urgent = {"priority": "urgent"}
        state_normal = {"priority": "normal"}

        assert evaluator.evaluate("is_urgent", state_urgent) is True
        assert evaluator.evaluate("is_urgent", state_normal) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
