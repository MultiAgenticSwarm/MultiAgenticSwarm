"""
Routing strategies for determining execution paths in multi-agent systems.

This module provides strategy functions that can be used with routers
to make sophisticated routing decisions in LangGraph workflows.
"""

from typing import Any, Dict, List, Callable, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ..utils.logger import get_logger

# Initialize logger for this module
logger = get_logger(__name__)


class RoutingStrategy(Enum):
    """
    Enumeration of available routing strategies.

    Each strategy represents a different approach to selecting which agent
    should handle a task in a multi-agent system.
    """
    CAPABILITY_BASED = "capability_based"
    PERFORMANCE_BASED = "performance_based"
    LOAD_BALANCED = "load_balanced"
    PRIORITY_BASED = "priority_based"
    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
    CONDITIONAL = "conditional"
    HYBRID = "hybrid"


@dataclass
class AgentCapability:
    """
    Represents an agent's capability in the multi-agent system.

    Capabilities are used to match agents to tasks based on their skills,
    proficiency levels, and associated tags.

    Attributes:
        name: The name of the capability
        description: Detailed description of what this capability enables
        proficiency: Skill level from 0.0 (novice) to 1.0 (expert)
        tags: Additional keywords for fuzzy matching
    """
    name: str
    description: str
    proficiency: float = 1.0  # 0.0 to 1.0
    tags: List[str] = None

    def __post_init__(self):
        """Initialize default values after dataclass initialization."""
        if self.tags is None:
            self.tags = []


@dataclass
class RoutingContext:
    """
    Context information for routing decisions.

    Provides comprehensive state information that routing strategies
    can use to make informed decisions about agent selection.

    Attributes:
        current_node: Name of the current execution node
        task: Description of the task to be performed
        requirements: List of required capabilities
        state: Current system state dictionary
        history: Historical execution path
        metadata: Additional contextual information
    """
    current_node: str
    task: str
    requirements: List[str]
    state: Dict[str, Any]
    history: List[str]
    metadata: Dict[str, Any]


class CapabilityMatcher:
    """
    Matches tasks to agents based on their capabilities.

    This class implements sophisticated capability matching including:
    - Exact capability name matching
    - Fuzzy substring matching
    - Tag-based matching
    - Proficiency-weighted scoring

    The matcher maintains a registry of agent capabilities and provides
    scoring mechanisms to rank agents by their suitability for a task.
    """

    def __init__(self):
        """Initialize the capability matcher with an empty registry."""
        self.agent_capabilities: Dict[str, List[AgentCapability]] = {}
        logger.debug("Initialized CapabilityMatcher")

    def register_agent(self, agent: str, capabilities: List[AgentCapability]):
        """
        Register an agent's capabilities in the matcher.

        Args:
            agent: Name of the agent to register
            capabilities: List of AgentCapability objects describing the agent's skills
        """
        self.agent_capabilities[agent] = capabilities
        logger.info(f"Registered agent '{agent}' with {len(capabilities)} capabilities")

    def match_agents(
            self,
            requirements: List[str],
            min_proficiency: float = 0.5
    ) -> List[Tuple[str, float]]:
        """
        Match agents to task requirements and return ranked results.

        Args:
            requirements: List of required capabilities for the task
            min_proficiency: Minimum proficiency threshold (0.0 to 1.0)

        Returns:
            List of (agent_name, match_score) tuples sorted by score (highest first)
        """
        logger.debug(f"Matching agents for requirements: {requirements}, min_proficiency: {min_proficiency}")
        matches = []

        for agent, capabilities in self.agent_capabilities.items():
            score = self._calculate_match_score(capabilities, requirements, min_proficiency)
            if score > 0:
                matches.append((agent, score))
                logger.debug(f"Agent '{agent}' matched with score: {score:.2f}")

        # Sort by score descending
        matches.sort(key=lambda x: x[1], reverse=True)

        logger.info(f"Found {len(matches)} matching agents for requirements")
        return matches

    def _calculate_match_score(
            self,
            capabilities: List[AgentCapability],
            requirements: List[str],
            min_proficiency: float
    ) -> float:
        """
        Calculate how well an agent's capabilities match the requirements.

        The score is calculated by:
        1. Finding the best matching capability for each requirement
        2. Weighting matches by proficiency level
        3. Normalizing by requirement coverage

        Args:
            capabilities: List of agent capabilities
            requirements: List of required capabilities
            min_proficiency: Minimum acceptable proficiency level

        Returns:
            Match score from 0.0 (no match) to 1.0 (perfect match)
        """
        if not requirements:
            return 1.0  # No requirements = all match

        total_score = 0.0
        matched_requirements = 0

        for requirement in requirements:
            best_match_score = 0.0

            for capability in capabilities:
                # Check if capability matches requirement
                match_score = self._match_capability(capability, requirement)

                if match_score > 0 and capability.proficiency >= min_proficiency:
                    # Weight by proficiency
                    weighted_score = match_score * capability.proficiency
                    best_match_score = max(best_match_score, weighted_score)

            if best_match_score > 0:
                matched_requirements += 1
                total_score += best_match_score

        if matched_requirements == 0:
            return 0.0

        # Average score normalized by requirement coverage
        coverage = matched_requirements / len(requirements)
        avg_score = total_score / matched_requirements

        return coverage * avg_score

    def _match_capability(self, capability: AgentCapability, requirement: str) -> float:
        """
        Match a single capability against a requirement string.

        Implements tiered matching:
        - Exact match: 1.0
        - Tag exact match: 0.9
        - Substring match: 0.8
        - Tag substring match: 0.7
        - Word overlap match: 0.5 * overlap_ratio

        Args:
            capability: The agent capability to match
            requirement: The requirement string to match against

        Returns:
            Match score from 0.0 (no match) to 1.0 (exact match)
        """
        requirement_lower = requirement.lower()
        capability_name_lower = capability.name.lower()

        # Exact match - highest score
        if requirement_lower == capability_name_lower:
            return 1.0

        # Substring match
        if requirement_lower in capability_name_lower or capability_name_lower in requirement_lower:
            return 0.8

        # Tag match
        for tag in capability.tags:
            if requirement_lower == tag.lower():
                return 0.9
            if requirement_lower in tag.lower() or tag.lower() in requirement_lower:
                return 0.7

        # Fuzzy match (simple word overlap)
        req_words = set(requirement_lower.split())
        cap_words = set(capability_name_lower.split())

        if req_words & cap_words:
            overlap = len(req_words & cap_words)
            max_words = max(len(req_words), len(cap_words))
            return 0.5 * (overlap / max_words)

        return 0.0


class PerformanceTracker:
    """
    Tracks agent performance metrics for performance-based routing.

    This class maintains historical performance data for agents including:
    - Success rate (percentage of successful executions)
    - Average execution time
    - Quality scores (when provided)

    Performance data is used to route tasks to the best-performing agents,
    improving overall system efficiency and reliability.
    """

    def __init__(self, history_size: int = 100):
        """
        Initialize the performance tracker.

        Args:
            history_size: Maximum number of historical records to maintain per agent
        """
        self.history_size = history_size
        self.agent_metrics: Dict[str, Dict[str, List[float]]] = {}
        logger.debug(f"Initialized PerformanceTracker with history_size={history_size}")

    def record_execution(
            self,
            agent: str,
            success: bool,
            execution_time: float,
            quality_score: Optional[float] = None
    ):
        """
        Record the outcome of an agent execution for performance tracking.

        Args:
            agent: Name of the agent that executed
            success: Whether the execution was successful
            execution_time: Time taken in seconds
            quality_score: Optional quality metric (0.0 to 1.0)
        """
        if agent not in self.agent_metrics:
            self.agent_metrics[agent] = {
                "success": [],
                "execution_time": [],
                "quality": []
            }

        metrics = self.agent_metrics[agent]

        # Record metrics
        metrics["success"].append(1.0 if success else 0.0)
        metrics["execution_time"].append(execution_time)
        if quality_score is not None:
            metrics["quality"].append(quality_score)

        # Trim to history size to prevent unbounded memory growth
        for key in metrics:
            if len(metrics[key]) > self.history_size:
                metrics[key] = metrics[key][-self.history_size:]

        logger.debug(
            f"Recorded execution for agent '{agent}': "
            f"success={success}, time={execution_time:.2f}s, quality={quality_score}"
        )

    def get_success_rate(self, agent: str) -> float:
        """
        Get the success rate for an agent.

        Args:
            agent: Name of the agent

        Returns:
            Success rate from 0.0 to 1.0, or 1.0 if no history exists
        """
        if agent not in self.agent_metrics:
            return 1.0  # Default to perfect score if no history

        successes = self.agent_metrics[agent]["success"]
        if not successes:
            return 1.0

        return sum(successes) / len(successes)

    def get_avg_execution_time(self, agent: str) -> float:
        """
        Get the average execution time for an agent.

        Args:
            agent: Name of the agent

        Returns:
            Average execution time in seconds, or 0.0 if no history exists
        """
        if agent not in self.agent_metrics:
            return 0.0

        times = self.agent_metrics[agent]["execution_time"]
        if not times:
            return 0.0

        return sum(times) / len(times)

    def get_quality_score(self, agent: str) -> float:
        """
        Get the average quality score for an agent.

        Args:
            agent: Name of the agent

        Returns:
            Average quality score from 0.0 to 1.0, or 1.0 if no history exists
        """
        if agent not in self.agent_metrics:
            return 1.0  # Default to perfect score

        qualities = self.agent_metrics[agent]["quality"]
        if not qualities:
            return 1.0

        return sum(qualities) / len(qualities)

    def get_performance_score(self, agent: str, weights: Optional[Dict[str, float]] = None) -> float:
        """
        Calculate an overall performance score for an agent.

        The score is a weighted combination of:
        - Success rate (default weight: 0.4)
        - Speed score (default weight: 0.3)
        - Quality score (default weight: 0.3)

        Args:
            agent: Name of the agent
            weights: Custom weights for metrics (success, speed, quality)

        Returns:
            Overall performance score from 0.0 to 1.0
        """
        if weights is None:
            weights = {
                "success": 0.4,
                "speed": 0.3,
                "quality": 0.3
            }

        success_rate = self.get_success_rate(agent)

        # Speed score (inverse of execution time, normalized)
        avg_time = self.get_avg_execution_time(agent)
        all_times = []
        for metrics in self.agent_metrics.values():
            all_times.extend(metrics["execution_time"])

        if all_times and avg_time > 0:
            max_time = max(all_times)
            speed_score = 1.0 - (avg_time / max_time)
        else:
            speed_score = 1.0

        quality_score = self.get_quality_score(agent)

        # Weighted combination
        performance = (
                weights.get("success", 0.4) * success_rate +
                weights.get("speed", 0.3) * speed_score +
                weights.get("quality", 0.3) * quality_score
        )

        return performance

    def rank_agents(self, agents: List[str], weights: Optional[Dict[str, float]] = None) -> List[Tuple[str, float]]:
        """
        Rank a list of agents by their performance scores.

        Args:
            agents: List of agent names to rank
            weights: Optional custom weights for performance calculation

        Returns:
            List of (agent_name, score) tuples sorted by score (highest first)
        """
        logger.debug(f"Ranking {len(agents)} agents by performance")
        rankings = []

        for agent in agents:
            score = self.get_performance_score(agent, weights)
            rankings.append((agent, score))

        rankings.sort(key=lambda x: x[1], reverse=True)

        if rankings:
            logger.info(f"Top performing agent: '{rankings[0][0]}' with score {rankings[0][1]:.2f}")

        return rankings


class ConditionalEvaluator:
    """
    Evaluates conditions for conditional routing decisions.

    This class provides a flexible condition evaluation system supporting:
    - Simple comparisons (==, !=, >, <, >=, <=, in)
    - Logical operators (AND, OR, NOT)
    - State path expressions using dot notation
    - Custom evaluator functions

    Conditions are evaluated against the current system state to determine
    which routing path should be taken.
    """

    def __init__(self):
        """Initialize the conditional evaluator with an empty custom evaluator registry."""
        self.custom_evaluators: Dict[str, Callable] = {}
        logger.debug("Initialized ConditionalEvaluator")

    def register_evaluator(self, name: str, func: Callable[[Dict[str, Any]], bool]):
        """
        Register a custom condition evaluator function.

        Args:
            name: Name identifier for the custom evaluator
            func: Function that takes state dict and returns boolean
        """
        self.custom_evaluators[name] = func
        logger.info(f"Registered custom evaluator: '{name}'")

    def evaluate(self, condition: str, state: Dict[str, Any]) -> bool:
        """
        Evaluate a condition string against the current state.

        Supported condition syntax:
        - "key == value" - equality check
        - "key > value" - greater than
        - "key < value" - less than
        - "key in [value1, value2]" - membership check
        - "custom_func()" - custom evaluator
        - "cond1 AND cond2" - logical AND
        - "cond1 OR cond2" - logical OR
        - "NOT cond" - logical negation

        Args:
            condition: Condition string to evaluate
            state: Current state dictionary

        Returns:
            True if condition is met, False otherwise
        """
        logger.debug(f"Evaluating condition: '{condition}'")

        # Handle custom evaluators
        if condition in self.custom_evaluators:
            try:
                result = self.custom_evaluators[condition](state)
                logger.debug(f"Custom evaluator '{condition}' returned: {result}")
                return result
            except Exception as e:
                logger.error(f"Error in custom evaluator '{condition}': {e}")
                return False

        # Handle logical operators
        if " AND " in condition:
            parts = condition.split(" AND ")
            result = all(self.evaluate(part.strip(), state) for part in parts)
            logger.debug(f"AND evaluation result: {result}")
            return result

        if " OR " in condition:
            parts = condition.split(" OR ")
            result = any(self.evaluate(part.strip(), state) for part in parts)
            logger.debug(f"OR evaluation result: {result}")
            return result

        if condition.startswith("NOT "):
            inner = condition[4:].strip()
            result = not self.evaluate(inner, state)
            logger.debug(f"NOT evaluation result: {result}")
            return result

        # Handle comparisons
        return self._evaluate_comparison(condition, state)

    def _evaluate_comparison(self, condition: str, state: Dict[str, Any]) -> bool:
        """
        Evaluate a comparison condition (e.g., "key == value").

        Args:
            condition: Comparison condition string
            state: Current state dictionary

        Returns:
            Result of the comparison
        """
        # Parse comparison
        operators = ["==", "!=", ">=", "<=", ">", "<", " in "]

        for op in operators:
            if op in condition:
                left, right = condition.split(op, 1)
                left = left.strip()
                right = right.strip()

                # Get left value from state
                left_value = self._get_state_value(left, state)

                # Parse right value
                right_value = self._parse_value(right)

                # Evaluate
                result = self._compare(left_value, op.strip(), right_value)
                logger.debug(f"Comparison: {left_value} {op.strip()} {right_value} = {result}")
                return result

        # No operator found - check boolean state value
        value = self._get_state_value(condition, state)
        return bool(value)

    def _get_state_value(self, path: str, state: Dict[str, Any]) -> Any:
        """
        Extract a value from state using dot notation path.

        Example: "user.profile.name" extracts state["user"]["profile"]["name"]

        Args:
            path: Dot-notation path string
            state: State dictionary to extract from

        Returns:
            Value at the path, or None if path doesn't exist
        """
        parts = path.split(".")
        value = state

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None

        return value

    def _parse_value(self, value_str: str) -> Any:
        """
        Parse a value string to the appropriate Python type.

        Handles: booleans, None, integers, floats, lists, and strings.

        Args:
            value_str: String representation of the value

        Returns:
            Parsed value in appropriate type
        """
        value_str = value_str.strip()

        # Boolean
        if value_str.lower() == "true":
            return True
        if value_str.lower() == "false":
            return False

        # None
        if value_str.lower() == "none":
            return None

        # Number
        try:
            if "." in value_str:
                return float(value_str)
            return int(value_str)
        except ValueError:
            pass

        # List
        if value_str.startswith("[") and value_str.endswith("]"):
            items = value_str[1:-1].split(",")
            return [self._parse_value(item.strip()) for item in items]

        # String (remove quotes if present)
        if (value_str.startswith('"') and value_str.endswith('"')) or \
                (value_str.startswith("'") and value_str.endswith("'")):
            return value_str[1:-1]

        return value_str

    def _compare(self, left: Any, operator: str, right: Any) -> bool:
        """
        Compare two values using the specified operator.

        Args:
            left: Left-hand value
            operator: Comparison operator (==, !=, >, <, >=, <=, in)
            right: Right-hand value

        Returns:
            Result of the comparison, or False if comparison fails
        """
        try:
            if operator == "==":
                return left == right
            elif operator == "!=":
                return left != right
            elif operator == ">":
                return left > right
            elif operator == "<":
                return left < right
            elif operator == ">=":
                return left >= right
            elif operator == "<=":
                return left <= right
            elif operator == "in":
                return left in right
        except (TypeError, ValueError) as e:
            logger.warning(f"Comparison failed: {left} {operator} {right} - {e}")
            return False

        return False


class HybridStrategy:
    """
    Combines multiple routing strategies for more sophisticated routing.

    This class allows you to:
    - Switch between strategies based on conditions
    - Combine strategies using consensus voting
    - Use weighted voting across multiple strategies

    Useful when no single strategy is optimal for all scenarios.
    """

    def __init__(self):
        """Initialize the hybrid strategy with empty strategy registry."""
        self.strategies: Dict[str, Callable] = {}
        self.strategy_weights: Dict[str, float] = {}
        logger.debug("Initialized HybridStrategy")

    def add_strategy(
            self,
            name: str,
            strategy_func: Callable[[Dict[str, Any]], str],
            weight: float = 1.0
    ):
        """
        Add a routing strategy to the hybrid strategy.

        Args:
            name: Identifier for the strategy
            strategy_func: Function that takes state and returns next node name
            weight: Weight for voting (higher = more influence)
        """
        self.strategies[name] = strategy_func
        self.strategy_weights[name] = weight
        logger.info(f"Added strategy '{name}' with weight {weight}")

    def route_by_condition(
            self,
            state: Dict[str, Any],
            conditions: Dict[str, Callable[[Dict[str, Any]], bool]]
    ) -> str:
        """
        Route using the first strategy whose condition is met.

        Evaluates conditions in order and uses the corresponding strategy
        when a condition returns True.

        Args:
            state: Current system state
            conditions: Dict mapping strategy names to condition functions

        Returns:
            Next node name selected by the first matching strategy
        """
        logger.debug("Routing by condition")

        for strategy_name, condition_func in conditions.items():
            try:
                if condition_func(state):
                    if strategy_name in self.strategies:
                        result = self.strategies[strategy_name](state)
                        logger.info(f"Condition matched for strategy '{strategy_name}', routing to: {result}")
                        return result
            except Exception as e:
                logger.error(f"Error evaluating condition for strategy '{strategy_name}': {e}")

        # Default to first strategy
        first_strategy = next(iter(self.strategies.values()))
        result = first_strategy(state)
        logger.info(f"No conditions matched, using default strategy, routing to: {result}")
        return result

    def route_by_consensus(self, state: Dict[str, Any]) -> str:
        """
        Route by majority vote of all strategies.

        Each strategy votes for a next node, and the node with the most
        votes is selected.

        Args:
            state: Current system state

        Returns:
            Next node name with the most votes
        """
        logger.debug("Routing by consensus")
        votes = {}

        for strategy_name, strategy_func in self.strategies.items():
            try:
                next_node = strategy_func(state)
                votes[next_node] = votes.get(next_node, 0) + 1
                logger.debug(f"Strategy '{strategy_name}' voted for: {next_node}")
            except Exception as e:
                logger.error(f"Error in strategy '{strategy_name}': {e}")

        # Return node with most votes
        if votes:
            result = max(votes.items(), key=lambda x: x[1])[0]
            logger.info(f"Consensus routing result: {result} (votes: {votes})")
            return result

        logger.warning("No votes collected, returning default 'end'")
        return "end"

    def route_by_weighted_vote(self, state: Dict[str, Any]) -> str:
        """
        Route by weighted vote of all strategies.

        Each strategy votes for a next node, weighted by its assigned weight.
        The node with the highest weighted vote total is selected.

        Args:
            state: Current system state

        Returns:
            Next node name with highest weighted votes
        """
        logger.debug("Routing by weighted vote")
        weighted_votes = {}

        for strategy_name, strategy_func in self.strategies.items():
            try:
                next_node = strategy_func(state)
                weight = self.strategy_weights.get(strategy_name, 1.0)
                weighted_votes[next_node] = weighted_votes.get(next_node, 0) + weight
                logger.debug(f"Strategy '{strategy_name}' (weight={weight}) voted for: {next_node}")
            except Exception as e:
                logger.error(f"Error in strategy '{strategy_name}': {e}")

        # Return node with highest weighted vote
        if weighted_votes:
            result = max(weighted_votes.items(), key=lambda x: x[1])[0]
            logger.info(f"Weighted vote routing result: {result} (votes: {weighted_votes})")
            return result

        logger.warning("No weighted votes collected, returning default 'end'")
        return "end"


# Utility functions for common routing patterns

def create_state_condition(
        key: str,
        operator: str,
        value: Any
) -> Callable[[Dict[str, Any]], bool]:
    """
    Create a simple state condition function for routing.

    This is a convenience function to create condition functions without
    manually instantiating ConditionalEvaluator.

    Args:
        key: State key to check
        operator: Comparison operator (==, !=, >, <, >=, <=, in)
        value: Value to compare against

    Returns:
        Condition function that evaluates the condition
    """
    evaluator = ConditionalEvaluator()
    condition = f"{key} {operator} {value}"

    def condition_func(state: Dict[str, Any]) -> bool:
        return evaluator.evaluate(condition, state)

    return condition_func


def create_capability_router(
        capability_matcher: CapabilityMatcher,
        min_proficiency: float = 0.5
) -> Callable[[Dict[str, Any]], str]:
    """
    Create a capability-based routing function.

    The returned function routes tasks to agents based on capability matching.

    Args:
        capability_matcher: CapabilityMatcher instance with registered agents
        min_proficiency: Minimum proficiency threshold for matching

    Returns:
        Router function compatible with LangGraph
    """
    def router(state: Dict[str, Any]) -> str:
        """Route to best matching agent based on capabilities."""
        requirements = state.get("task_requirements", [])
        matches = capability_matcher.match_agents(requirements, min_proficiency)

        if matches:
            # Return best match
            selected = matches[0][0]
            logger.info(f"Capability-based routing selected agent: {selected}")
            return selected

        # No matches - return end or default
        default = state.get("default_agent", "end")
        logger.warning(f"No capability matches found, routing to default: {default}")
        return default

    return router


def create_performance_router(
        performance_tracker: PerformanceTracker,
        agents: List[str]
) -> Callable[[Dict[str, Any]], str]:
    """
    Create a performance-based routing function.

    The returned function routes tasks to the best-performing agent based
    on historical performance metrics.

    Args:
        performance_tracker: PerformanceTracker instance with agent metrics
        agents: List of available agent names

    Returns:
        Router function compatible with LangGraph
    """
    def router(state: Dict[str, Any]) -> str:
        """Route to best performing agent."""
        rankings = performance_tracker.rank_agents(agents)

        if rankings:
            # Return best performing agent
            selected = rankings[0][0]
            logger.info(f"Performance-based routing selected agent: {selected} (score: {rankings[0][1]:.2f})")
            return selected

        # No performance data - return first agent
        default = agents[0] if agents else "end"
        logger.warning(f"No performance data available, routing to default: {default}")
        return default

    return router