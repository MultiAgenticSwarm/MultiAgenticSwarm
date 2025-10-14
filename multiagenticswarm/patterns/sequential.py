from typing import Any, Dict, List, Callable
from .base import CollaborationPattern, PatternMetadata, PatternType, GraphTopology


class SequentialPattern(CollaborationPattern):
    """
    Sequential pattern: Agents work in a defined sequence, each building on the previous agent's work.

    Graph: [Agent1] → [Agent2] → [Agent3] → [Agent4] → [End]

    Characteristics:
    - Linear flow of execution
    - Each agent completes before next starts
    - State passed along chain
    - Clear input/output contracts
    - State transformation at each step
    - Error propagation along chain

    Best for:
    - Clear task dependencies
    - Pipeline processing
    - Step-by-step refinement
    - Order matters
    """

    def _create_metadata(self) -> PatternMetadata:
        return PatternMetadata(
            name="Sequential",
            description="Agents execute in fixed order, each building on previous results",
            pattern_type=PatternType.SEQUENTIAL,
            min_agents=1,
            tags=["sequential", "pipeline", "ordered"],
        )

    def build_topology(self, agents: List[str], **kwargs) -> GraphTopology:
        """
        Build sequential pattern topology.

        Args:
            agents: List of agent names in execution order
            **kwargs: Optional parameters:
                - allow_skip: Allow skipping agents based on conditions (default: False)
                - error_handling: "skip_on_failure" | "stop_on_failure" | "retry"
                - state_passing: "cumulative" | "last_only" | "selective"
        """
        self.validate_agents(agents)

        allow_skip = kwargs.get("allow_skip", False)
        error_handling = kwargs.get("error_handling", "skip_on_failure")

        nodes = ["start"] + agents + ["end"]
        edges = []

        # Create linear chain
        prev = "start"
        for agent in agents:
            edges.append((prev, agent))
            prev = agent

        # Last agent to end
        edges.append((prev, "end"))

        # Optional: Allow skipping (add skip edges for error handling)
        if allow_skip or error_handling == "skip_on_failure":
            for i, agent in enumerate(agents):
                # Each agent can skip to any later agent or end on failure
                for j in range(i + 2, len(agents)):
                    edges.append((agent, agents[j]))
                edges.append((agent, "end"))

        return GraphTopology(
            nodes=nodes,
            edges=edges,
            entry_point="start",
            exit_point="end",
            special_nodes={"sequence": agents},
        )

    def create_router(self, **kwargs) -> Callable[[Dict[str, Any]], str]:
        """
        Create sequential routing function.

        Args:
            **kwargs: Optional parameters:
                - allow_skip: Whether agents can be skipped
                - skip_condition: Function to determine if agent should be skipped
                - error_handling: "skip_on_failure" | "stop_on_failure" | "retry"
                - state_passing: "cumulative" | "last_only" | "selective"
                - max_retries: Maximum retries per agent (default: 0)
        """
        allow_skip = kwargs.get("allow_skip", False)
        skip_condition = kwargs.get("skip_condition")
        error_handling = kwargs.get("error_handling", "skip_on_failure")
        state_passing = kwargs.get("state_passing", "cumulative")
        max_retries = kwargs.get("max_retries", 0)

        def sequential_router(state: Dict[str, Any]) -> str:
            """
            Route to next agent in sequence.

            Features:
            - Linear execution order
            - State transformation at each step
            - Error propagation handling
            - Conditional skipping
            - Retry mechanism
            """
            current = state.get("current_node", "start")
            agents = state.get("agents", [])

            # From start, go to first agent
            if current == "start":
                return agents[0] if agents else "end"

            # From agent, go to next agent or end
            elif current in agents:
                idx = agents.index(current)

                # Handle errors
                if state.get(f"{current}_error"):
                    retries = state.get(f"{current}_retries", 0)

                    if error_handling == "stop_on_failure":
                        return "end"
                    elif error_handling == "retry" and retries < max_retries:
                        state[f"{current}_retries"] = retries + 1
                        return current
                    elif error_handling == "skip_on_failure":
                        # Skip to next agent
                        if idx + 1 < len(agents):
                            return agents[idx + 1]
                        else:
                            return "end"

                # State passing
                if state_passing == "cumulative":
                    # Pass all previous states
                    state["cumulative_state"] = state.get("cumulative_state", {})
                    state["cumulative_state"][current] = state.get(f"{current}_output")
                elif state_passing == "last_only":
                    # Pass only last agent's output
                    state["pipeline_state"] = state.get(f"{current}_output")

                # Check if we can skip based on condition
                if allow_skip and skip_condition:
                    # Check each remaining agent
                    for i in range(idx + 1, len(agents)):
                        if not skip_condition(agents[i], state):
                            return agents[i]
                    return "end"

                # Normal sequential flow
                if idx + 1 < len(agents):
                    return agents[idx + 1]
                else:
                    return "end"

            return "end"

        return sequential_router
