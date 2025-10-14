"""
Router implementations for different collaboration patterns.

This module provides various router classes for controlling agent execution flow in multi-agent systems:

- **BaseRouter**: Abstract base class for all routers
- **SupervisorRouter**: LLM-based intelligent routing with capability matching
- **LoadBalancerRouter**: Distributes work across agents using various strategies
- **ConditionalRouter**: Routes based on state conditions and predicates
- **ConsensusRouter**: Routes based on voting and consensus mechanisms
- **SequentialRouter**: Routes through agents in a fixed sequence
- **ParallelRouter**: Manages parallel execution and aggregation

Each router implements sophisticated logging to track routing decisions, performance,
and system behavior for debugging and monitoring.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum
import random
from collections import defaultdict

from ..utils.logger import get_logger

# Initialize logger for this module
logger = get_logger(__name__)


class RoutingDecision:
    """
    Represents a routing decision with metadata.

    This class encapsulates information about a routing decision including
    the selected next node, confidence level, reasoning, and additional metadata.
    Used for tracking, debugging, and explainability.

    Attributes:
        next_node: Name of the next node to execute
        confidence: Confidence score for the decision (0.0 to 1.0)
        reasoning: Human-readable explanation of the decision
        metadata: Additional information about the decision
    """

    def __init__(
            self,
            next_node: str,
            confidence: float = 1.0,
            reasoning: Optional[str] = None,
            metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a routing decision.

        Args:
            next_node: Name of the next node to route to
            confidence: Confidence level (0.0 to 1.0, default: 1.0)
            reasoning: Optional explanation for the decision
            metadata: Optional additional metadata
        """
        self.next_node = next_node
        self.confidence = confidence
        self.reasoning = reasoning
        self.metadata = metadata or {}

        logger.debug(
            f"Created routing decision: next_node='{next_node}', "
            f"confidence={confidence:.2f}, reasoning='{reasoning}'"
        )

    def __str__(self):
        return f"Route to '{self.next_node}' (confidence: {self.confidence})"


class BaseRouter(ABC):
    """
    Abstract base class for all routers.

    Routers are responsible for determining the next node to execute in a graph
    based on the current state. They provide:
    - State-based decision making
    - Routing history tracking
    - Metadata-rich decision objects
    - Extensible routing logic

    Subclasses must implement the route() method to define routing logic.
    """

    def __init__(self, name: Optional[str] = None):
        """
        Initialize the base router.

        Args:
            name: Optional name for the router (defaults to class name)
        """
        self.name = name or self.__class__.__name__
        self.routing_history: List[RoutingDecision] = []

        logger.info(f"Initialized {self.name} router")

    @abstractmethod
    def route(self, state: Dict[str, Any]) -> str:
        """
        Determine the next node to execute.

        Args:
            state: Current graph state

        Returns:
            Name of the next node to execute
        """
        pass

    def route_with_metadata(self, state: Dict[str, Any]) -> RoutingDecision:
        """
        Route and return detailed decision information.

        This method wraps the basic route() method to provide rich metadata
        about the routing decision for tracking and debugging purposes.

        Args:
            state: Current graph state

        Returns:
            RoutingDecision with metadata
        """
        logger.debug(f"{self.name}: Routing with metadata from state: {state.get('current_node', 'start')}")

        next_node = self.route(state)
        decision = RoutingDecision(
            next_node=next_node,
            confidence=1.0,
            reasoning=f"Routed by {self.name}"
        )
        self.routing_history.append(decision)

        logger.info(f"{self.name}: Routed to '{next_node}' (history size: {len(self.routing_history)})")

        return decision

    def get_history(self) -> List[RoutingDecision]:
        """
        Get routing history.

        Returns:
            List of all routing decisions made by this router
        """
        return self.routing_history

    def reset_history(self):
        """
        Clear routing history.

        Useful for resetting state between runs or freeing memory.
        """
        history_size = len(self.routing_history)
        self.routing_history.clear()
        logger.debug(f"{self.name}: Cleared routing history ({history_size} entries)")


class SupervisorRouter(BaseRouter):
    """
    LLM-based router that makes intelligent decisions about agent selection.

    The supervisor examines:
    - Current task requirements
    - Agent capabilities
    - Agent availability and load
    - Previous performance
    - Task context

    Best for:
    - Complex decision-making
    - Dynamic task assignment
    - Capability-based routing
    - Quality control workflows
    """

    def __init__(
            self,
            agents: List[str],
            llm: Optional[Any] = None,
            agent_capabilities: Optional[Dict[str, List[str]]] = None,
            supervisor_node: str = "supervisor",
            end_node: str = "end"
    ):
        """
        Initialize supervisor router.

        Args:
            agents: List of agent names
            llm: Language model for decision-making
            agent_capabilities: Dict mapping agent names to their capabilities
            supervisor_node: Name of supervisor node
            end_node: Name of end node
        """
        super().__init__()
        self.agents = agents
        self.llm = llm
        self.agent_capabilities = agent_capabilities or {}
        self.supervisor_node = supervisor_node
        self.end_node = end_node
        self.agent_performance: Dict[str, List[float]] = defaultdict(list)

        logger.info(
            f"SupervisorRouter initialized with {len(agents)} agents, "
            f"LLM: {bool(llm)}, capabilities: {len(self.agent_capabilities)} agents"
        )

    def route(self, state: Dict[str, Any]) -> str:
        """
        Route based on LLM decision or capability matching.

        Process:
        1. Examine current task
        2. Evaluate agent capabilities
        3. Check agent availability
        4. Select best agent
        5. Route to agent or end
        """
        current = state.get("current_node", self.supervisor_node)
        logger.debug(f"SupervisorRouter: Routing from node '{current}'")

        # From supervisor, select best agent
        if current == self.supervisor_node:
            selected = self._select_agent(state)
            logger.info(f"SupervisorRouter: Selected agent '{selected}' from supervisor")
            return selected

        # From agent, return to supervisor
        elif current in self.agents:
            self._record_performance(current, state)

            # Check if task is complete
            if state.get("task_complete", False):
                logger.info(f"SupervisorRouter: Task complete, routing to end from '{current}'")
                return self.end_node

            # Check if requires another agent
            if state.get("requires_additional_agent", False):
                logger.info(f"SupervisorRouter: Additional agent required, returning to supervisor from '{current}'")
                return self.supervisor_node

            # Default: return to supervisor for review
            logger.debug(f"SupervisorRouter: Returning to supervisor from '{current}' for review")
            return self.supervisor_node

        logger.debug(f"SupervisorRouter: Routing to end (unknown state)")
        return self.end_node

    def _select_agent(self, state: Dict[str, Any]) -> str:
        """
        Select the best agent for the current task.

        Selection criteria:
        1. Capability match
        2. Performance history
        3. Current load
        4. Availability
        """
        task_requirements = state.get("task_requirements", [])
        completed_agents = state.get("completed_agents", set())

        logger.debug(
            f"SupervisorRouter: Selecting agent for requirements: {task_requirements}, "
            f"completed: {len(completed_agents)}"
        )

        # If using LLM, get LLM decision
        if self.llm:
            logger.debug("SupervisorRouter: Using LLM for agent selection")
            return self._llm_select_agent(state)

        # Otherwise, use capability-based selection
        available_agents = [a for a in self.agents if a not in completed_agents]

        if not available_agents:
            logger.warning("SupervisorRouter: No available agents, routing to end")
            return self.end_node

        # Score agents based on capabilities
        scores = {}
        for agent in available_agents:
            score = self._score_agent(agent, task_requirements, state)
            scores[agent] = score
            logger.debug(f"SupervisorRouter: Agent '{agent}' scored {score:.3f}")

        # Select highest scoring agent
        best_agent = max(scores.items(), key=lambda x: x[1])[0]
        logger.info(
            f"SupervisorRouter: Selected '{best_agent}' with score {scores[best_agent]:.3f} "
            f"from {len(available_agents)} available agents"
        )

        return best_agent

    def _llm_select_agent(self, state: Dict[str, Any]) -> str:
        """Use LLM to select agent based on task and context."""
        logger.debug("SupervisorRouter: Creating LLM selection prompt")

        # Create prompt with task details and agent capabilities
        prompt = self._create_selection_prompt(state)

        # Get LLM response
        if hasattr(self.llm, 'invoke'):
            try:
                logger.debug("SupervisorRouter: Invoking LLM for agent selection")
                response = self.llm.invoke(prompt)
                selected_agent = self._parse_agent_from_response(response)
                logger.info(f"SupervisorRouter: LLM selected agent '{selected_agent}'")
                return selected_agent
            except Exception as e:
                logger.error(f"SupervisorRouter: LLM invocation failed: {e}, falling back to capability-based")
                return self._select_agent(state)

        # Fallback to capability-based selection
        logger.warning("SupervisorRouter: LLM not available, using capability-based selection")
        return self._select_agent(state)

    def _create_selection_prompt(self, state: Dict[str, Any]) -> str:
        """Create prompt for LLM agent selection."""
        task = state.get("task", "")
        task_requirements = state.get("task_requirements", [])

        prompt = f"""You are a supervisor coordinating multiple agents.

Current Task: {task}
Requirements: {', '.join(task_requirements)}

Available Agents:
"""
        for agent in self.agents:
            capabilities = self.agent_capabilities.get(agent, [])
            performance = self._get_avg_performance(agent)
            prompt += f"\n- {agent}: {', '.join(capabilities)} (avg performance: {performance:.2f})"

        prompt += "\n\nSelect the best agent for this task. Respond with just the agent name."

        return prompt

    def _parse_agent_from_response(self, response: Any) -> str:
        """Parse agent name from LLM response."""
        # Convert response to string
        response_text = str(response).strip().lower()

        # Look for agent names in response
        for agent in self.agents:
            if agent.lower() in response_text:
                return agent

        # Fallback to first agent
        return self.agents[0] if self.agents else self.end_node

    def _score_agent(
            self,
            agent: str,
            requirements: List[str],
            state: Dict[str, Any]
    ) -> float:
        """
        Score an agent based on capability match and performance.

        Returns:
            Score between 0 and 1
        """
        score = 0.0

        # Capability match score
        agent_caps = set(self.agent_capabilities.get(agent, []))
        required_caps = set(requirements)

        if required_caps:
            match_ratio = len(agent_caps & required_caps) / len(required_caps)
            score += match_ratio * 0.7  # 70% weight on capabilities
        else:
            score += 0.7  # No requirements, all agents equal

        # Performance score
        avg_performance = self._get_avg_performance(agent)
        score += avg_performance * 0.3  # 30% weight on performance

        return score

    def _record_performance(self, agent: str, state: Dict[str, Any]):
        """Record agent performance for future routing decisions."""
        # Get performance metric from state
        performance = state.get(f"{agent}_performance", 1.0)
        self.agent_performance[agent].append(performance)

        # Keep only recent history (last 10 executions)
        if len(self.agent_performance[agent]) > 10:
            self.agent_performance[agent] = self.agent_performance[agent][-10:]

    def _get_avg_performance(self, agent: str) -> float:
        """Get average performance for an agent."""
        performances = self.agent_performance.get(agent, [1.0])
        return sum(performances) / len(performances) if performances else 1.0


class LoadBalancerRouter(BaseRouter):
    """
    Router that distributes work evenly across agents.

    Strategies:
    - Round-robin: Cycle through agents
    - Least-loaded: Select agent with fewest tasks
    - Random: Random distribution
    - Weighted: Distribute based on agent capacity

    Best for:
    - Parallel processing
    - High-throughput scenarios
    - Resource utilization
    - Fair distribution
    """

    def __init__(
            self,
            agents: List[str],
            strategy: str = "round_robin",
            agent_weights: Optional[Dict[str, float]] = None,
            aggregator_node: str = "aggregator",
            end_node: str = "end"
    ):
        """
        Initialize load balancer router.

        Args:
            agents: List of agent names
            strategy: "round_robin" | "least_loaded" | "random" | "weighted"
            agent_weights: Dict mapping agent names to capacity weights
            aggregator_node: Name of aggregation node
            end_node: Name of end node
        """
        super().__init__()
        self.agents = agents
        self.strategy = strategy
        self.agent_weights = agent_weights or {a: 1.0 for a in agents}
        self.aggregator_node = aggregator_node
        self.end_node = end_node

        # Tracking
        self.current_index = 0
        self.agent_loads: Dict[str, int] = {a: 0 for a in agents}
        self.completed_count = 0

    def route(self, state: Dict[str, Any]) -> str:
        """
        Route based on load balancing strategy.

        Process:
        1. Check current node
        2. If distributing, select next agent by strategy
        3. If agent finished, route to aggregator
        4. If all complete, route to end
        """
        current = state.get("current_node")
        completed_agents = state.get("completed_agents", set())

        # From agent, go to aggregator
        if current in self.agents:
            self.agent_loads[current] -= 1
            self.completed_count += 1

            # Check if all agents completed
            if len(completed_agents) >= len(self.agents):
                return self.aggregator_node

            return self.aggregator_node

        # From aggregator, check if done
        elif current == self.aggregator_node:
            if state.get("all_complete", False):
                return self.end_node
            # If more tasks, continue distributing
            return self._select_next_agent(state)

        # Initial distribution
        else:
            return self._select_next_agent(state)

    def _select_next_agent(self, state: Dict[str, Any]) -> str:
        """Select next agent based on strategy."""
        if self.strategy == "round_robin":
            return self._round_robin()
        elif self.strategy == "least_loaded":
            return self._least_loaded()
        elif self.strategy == "random":
            return self._random()
        elif self.strategy == "weighted":
            return self._weighted()
        else:
            return self._round_robin()

    def _round_robin(self) -> str:
        """Round-robin selection."""
        agent = self.agents[self.current_index % len(self.agents)]
        self.current_index += 1
        self.agent_loads[agent] += 1
        return agent

    def _least_loaded(self) -> str:
        """Select agent with lowest current load."""
        agent = min(self.agent_loads.items(), key=lambda x: x[1])[0]
        self.agent_loads[agent] += 1
        return agent

    def _random(self) -> str:
        """Random agent selection."""
        agent = random.choice(self.agents)
        self.agent_loads[agent] += 1
        return agent

    def _weighted(self) -> str:
        """Weighted random selection based on agent capacity."""
        # Calculate probability based on weights and current load
        probabilities = []
        for agent in self.agents:
            weight = self.agent_weights.get(agent, 1.0)
            load = self.agent_loads[agent]
            # Higher weight and lower load = higher probability
            prob = weight / (load + 1)
            probabilities.append(prob)

        # Normalize probabilities
        total = sum(probabilities)
        probabilities = [p / total for p in probabilities]

        # Select agent
        agent = random.choices(self.agents, weights=probabilities)[0]
        self.agent_loads[agent] += 1
        return agent

    def get_load_stats(self) -> Dict[str, Any]:
        """Get current load statistics."""
        return {
            "agent_loads": dict(self.agent_loads),
            "total_completed": self.completed_count,
            "current_index": self.current_index
        }

    def reset_loads(self):
        """Reset load tracking."""
        self.agent_loads = {a: 0 for a in self.agents}
        self.completed_count = 0
        self.current_index = 0


class ConditionalRouter(BaseRouter):
    """
    Router that makes decisions based on state conditions.

    Supports:
    - If-then-else logic
    - State-based branching
    - Dynamic path selection
    - Custom condition functions

    Best for:
    - Conditional workflows
    - State-dependent routing
    - Error handling paths
    - Dynamic branching
    """

    def __init__(
            self,
            conditions: Dict[str, Callable[[Dict[str, Any]], bool]],
            routing_map: Dict[str, str],
            default_route: str = "end"
    ):
        """
        Initialize conditional router.

        Args:
            conditions: Dict mapping condition names to condition functions
            routing_map: Dict mapping condition names to next node names
            default_route: Default node if no conditions match
        """
        super().__init__()
        self.conditions = conditions
        self.routing_map = routing_map
        self.default_route = default_route

    def route(self, state: Dict[str, Any]) -> str:
        """
        Route based on state conditions.

        Process:
        1. Evaluate all conditions
        2. Find first matching condition
        3. Route to corresponding node
        4. Use default if no match
        """
        # Evaluate conditions in order
        for condition_name, condition_func in self.conditions.items():
            try:
                if condition_func(state):
                    next_node = self.routing_map.get(condition_name, self.default_route)
                    return next_node
            except Exception as e:
                # Log error and continue to next condition
                print(f"Error evaluating condition '{condition_name}': {e}")
                continue

        # No conditions matched, use default
        return self.default_route

    def add_condition(
            self,
            name: str,
            condition: Callable[[Dict[str, Any]], bool],
            target: str
    ):
        """Add a new condition and routing target."""
        self.conditions[name] = condition
        self.routing_map[name] = target

    def remove_condition(self, name: str):
        """Remove a condition."""
        self.conditions.pop(name, None)
        self.routing_map.pop(name, None)


class ConsensusRouter(BaseRouter):
    """
    Router for consensus patterns with voting logic.

    Voting methods:
    - Unanimous: All agents must agree
    - Majority: More than 50% agreement
    - Supermajority: Configurable threshold (e.g., 2/3)
    - Weighted: Agents have different vote weights

    Best for:
    - Reliability-critical decisions
    - Multiple validation passes
    - Quality assurance
    - Democratic workflows
    """

    def __init__(
            self,
            agents: List[str],
            voting_method: str = "majority",
            vote_threshold: float = 0.5,
            agent_weights: Optional[Dict[str, float]] = None,
            decision_node: str = "decision",
            end_node: str = "end"
    ):
        """
        Initialize consensus router.

        Args:
            agents: List of agent names
            voting_method: "unanimous" | "majority" | "supermajority" | "weighted"
            vote_threshold: Threshold for supermajority (0.0 to 1.0)
            agent_weights: Dict mapping agent names to vote weights
            decision_node: Name of decision/voting node
            end_node: Name of end node
        """
        super().__init__()
        self.agents = agents
        self.voting_method = voting_method
        self.vote_threshold = vote_threshold
        self.agent_weights = agent_weights or {a: 1.0 for a in agents}
        self.decision_node = decision_node
        self.end_node = end_node

    def route(self, state: Dict[str, Any]) -> str:
        """
        Route based on consensus voting.

        Process:
        1. Collect votes from all agents
        2. Apply voting method
        3. Determine consensus
        4. Route to next step or end
        """
        current = state.get("current_node")
        completed_agents = state.get("completed_agents", set())

        # From agent, go to decision node
        if current in self.agents:
            # Check if all agents have voted
            if len(completed_agents) >= len(self.agents):
                return self.decision_node
            # Wait for more votes
            return self.decision_node

        # From decision node, evaluate consensus
        elif current == self.decision_node:
            consensus = self._evaluate_consensus(state)

            if consensus:
                state["consensus_reached"] = True
                state["consensus_result"] = state.get("majority_vote")
                return self.end_node
            else:
                # No consensus - handle based on configuration
                if state.get("require_consensus", True):
                    # Re-vote or fail
                    state["consensus_reached"] = False
                    return self.end_node
                else:
                    # Use tie-breaker or majority
                    state["consensus_reached"] = False
                    return self.end_node

        return self.end_node

    def _evaluate_consensus(self, state: Dict[str, Any]) -> bool:
        """
        Evaluate whether consensus is reached.

        Returns:
            True if consensus reached, False otherwise
        """
        # Collect votes from state
        votes = {}
        for agent in self.agents:
            vote = state.get(f"{agent}_vote")
            if vote is not None:
                votes[agent] = vote

        if not votes:
            return False

        # Apply voting method
        if self.voting_method == "unanimous":
            return self._unanimous_vote(votes, state)
        elif self.voting_method == "majority":
            return self._majority_vote(votes, state)
        elif self.voting_method == "supermajority":
            return self._supermajority_vote(votes, state)
        elif self.voting_method == "weighted":
            return self._weighted_vote(votes, state)

        return False

    def _unanimous_vote(self, votes: Dict[str, Any], state: Dict[str, Any]) -> bool:
        """Check for unanimous agreement."""
        if not votes:
            return False

        first_vote = list(votes.values())[0]
        unanimous = all(v == first_vote for v in votes.values())

        if unanimous:
            state["majority_vote"] = first_vote
            state["vote_count"] = len(votes)

        return unanimous

    def _majority_vote(self, votes: Dict[str, Any], state: Dict[str, Any]) -> bool:
        """Check for majority agreement (>50%)."""
        if not votes:
            return False

        # Count votes
        vote_counts = defaultdict(int)
        for vote in votes.values():
            vote_counts[vote] += 1

        # Find majority
        total_votes = len(votes)
        majority_threshold = total_votes / 2

        for vote_value, count in vote_counts.items():
            if count > majority_threshold:
                state["majority_vote"] = vote_value
                state["vote_count"] = count
                state["vote_percentage"] = count / total_votes
                return True

        return False

    def _supermajority_vote(self, votes: Dict[str, Any], state: Dict[str, Any]) -> bool:
        """Check for supermajority agreement (configurable threshold)."""
        if not votes:
            return False

        # Count votes
        vote_counts = defaultdict(int)
        for vote in votes.values():
            vote_counts[vote] += 1

        # Find supermajority
        total_votes = len(votes)

        for vote_value, count in vote_counts.items():
            percentage = count / total_votes
            if percentage >= self.vote_threshold:
                state["majority_vote"] = vote_value
                state["vote_count"] = count
                state["vote_percentage"] = percentage
                return True

        return False

    def _weighted_vote(self, votes: Dict[str, Any], state: Dict[str, Any]) -> bool:
        """Check for weighted majority."""
        if not votes:
            return False

        # Calculate weighted votes
        weighted_votes = defaultdict(float)
        total_weight = 0.0

        for agent, vote in votes.items():
            weight = self.agent_weights.get(agent, 1.0)
            weighted_votes[vote] += weight
            total_weight += weight

        # Find weighted majority
        for vote_value, weight in weighted_votes.items():
            percentage = weight / total_weight
            if percentage > 0.5:  # Weighted majority
                state["majority_vote"] = vote_value
                state["vote_weight"] = weight
                state["vote_percentage"] = percentage
                return True

        return False

    def get_vote_summary(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Get summary of voting results."""
        votes = {}
        for agent in self.agents:
            vote = state.get(f"{agent}_vote")
            if vote is not None:
                votes[agent] = vote

        vote_counts = defaultdict(int)
        for vote in votes.values():
            vote_counts[vote] += 1

        return {
            "total_votes": len(votes),
            "vote_distribution": dict(vote_counts),
            "consensus_reached": state.get("consensus_reached", False),
            "winning_vote": state.get("majority_vote"),
            "voting_method": self.voting_method
        }


class SequentialRouter(BaseRouter):
    """
    Router for sequential patterns.

    Routes through agents in a fixed order.

    Best for:
    - Pipeline processing
    - Step-by-step workflows
    - Ordered dependencies
    - Chain of responsibility
    """

    def __init__(
            self,
            sequence: List[str],
            end_node: str = "end",
            skip_on_error: bool = False
    ):
        """
        Initialize sequential router.

        Args:
            sequence: Ordered list of agent names
            end_node: Name of end node
            skip_on_error: Whether to skip to next on error
        """
        super().__init__()
        self.sequence = sequence
        self.end_node = end_node
        self.skip_on_error = skip_on_error
        self.current_index = 0

    def route(self, state: Dict[str, Any]) -> str:
        """
        Route to next agent in sequence.

        Process:
        1. Check current position in sequence
        2. Route to next agent
        3. Handle end of sequence
        4. Handle errors if configured
        """
        current = state.get("current_node")

        # Find current position in sequence
        if current in self.sequence:
            current_idx = self.sequence.index(current)

            # Check for errors
            if state.get(f"{current}_error") and self.skip_on_error:
                # Skip to next
                pass

            # Move to next in sequence
            next_idx = current_idx + 1

            if next_idx < len(self.sequence):
                return self.sequence[next_idx]
            else:
                return self.end_node

        # Start of sequence
        elif not current or current == "start":
            return self.sequence[0] if self.sequence else self.end_node

        return self.end_node

    def reset_sequence(self):
        """Reset sequence to beginning."""
        self.current_index = 0


class ParallelRouter(BaseRouter):
    """
    Router for parallel patterns.

    Distributes to all agents simultaneously, then aggregates.

    Best for:
    - Independent tasks
    - Parallel processing
    - Fan-out/fan-in
    - Concurrent execution
    """

    def __init__(
            self,
            agents: List[str],
            aggregator_node: str = "aggregator",
            end_node: str = "end",
            wait_for_all: bool = True
    ):
        """
        Initialize parallel router.

        Args:
            agents: List of agent names to execute in parallel
            aggregator_node: Name of aggregation node
            end_node: Name of end node
            wait_for_all: Whether to wait for all agents before aggregating
        """
        super().__init__()
        self.agents = agents
        self.aggregator_node = aggregator_node
        self.end_node = end_node
        self.wait_for_all = wait_for_all

    def route(self, state: Dict[str, Any]) -> str:
        """
        Route for parallel execution.

        Process:
        1. Fan out to all agents
        2. Track completions
        3. Fan in to aggregator when ready
        4. Route to end
        """
        current = state.get("current_node")
        completed_agents = state.get("completed_agents", set())

        # From agent, check if all complete
        if current in self.agents:
            if self.wait_for_all:
                # Wait for all agents
                if len(completed_agents) >= len(self.agents):
                    return self.aggregator_node
                else:
                    # Continue waiting (stay in parallel execution)
                    return current
            else:
                # Go to aggregator immediately
                return self.aggregator_node

        # From aggregator, go to end
        elif current == self.aggregator_node:
            return self.end_node

        # Initial fanout - return first agent (LangGraph handles parallel execution)
        else:
            return self.agents[0] if self.agents else self.end_node

    def get_completion_status(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Get status of parallel execution."""
        completed = state.get("completed_agents", set())

        return {
            "total_agents": len(self.agents),
            "completed_agents": len(completed),
            "pending_agents": len(self.agents) - len(completed),
            "completion_percentage": len(completed) / len(self.agents) if self.agents else 0,
            "all_complete": len(completed) >= len(self.agents)
        }
