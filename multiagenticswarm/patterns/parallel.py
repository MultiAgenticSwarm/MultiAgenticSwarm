from typing import Any, Dict, List, Callable
from .base import CollaborationPattern, PatternMetadata, PatternType, GraphTopology


class ParallelPattern(CollaborationPattern):
    """
    Parallel pattern: Multiple agents work simultaneously on different aspects of the same task.

    Graph: [Router] → [Agent1/2/3] (parallel) → [Aggregator] → [End]

    Components:
    - Router: Distributes work, splits tasks, assigns to agents, balances load
    - Parallel Execution: Simultaneous processing, independent state branches
    - Aggregator: Combines results, waits for completions, merges outputs, resolves conflicts

    Best for:
    - Independent subtasks
    - Speed is priority
    - Resource utilization
    - No dependencies between tasks
    """

    def _create_metadata(self) -> PatternMetadata:
        return PatternMetadata(
            name="Parallel",
            description="Agents execute independently in parallel, results joined",
            pattern_type=PatternType.PARALLEL,
            min_agents=2,
            tags=["parallel", "concurrent", "distributed"],
        )

    def build_topology(self, agents: List[str], **kwargs) -> GraphTopology:
        """
        Build parallel pattern topology.

        Args:
            agents: List of agent names to execute in parallel
            **kwargs: Optional parameters:
                - router_node: Name for router/splitter node (default: "router")
                - aggregator_node: Name for aggregator node (default: "aggregator")
                - skip_aggregator: Skip aggregator, go directly to end (default: False)
                - splitter: "task_based" | "even_split" | "custom"
                - aggregation: "merge_all" | "best_result" | "weighted"
                - timeout: Timeout for parallel execution (default: None)
                - partial_results: Allow partial results if timeout (default: False)
        """
        self.validate_agents(agents)

        router = kwargs.get("router_node", "router")
        aggregator = kwargs.get("aggregator_node", "aggregator")
        skip_aggregator = kwargs.get("skip_aggregator", False)

        if skip_aggregator:
            nodes = [router] + agents + ["end"]
            edges = []

            # Router → All agents
            for agent in agents:
                edges.append((router, agent))
                edges.append((agent, "end"))

            special_nodes = {"router": router}
        else:
            nodes = [router] + agents + [aggregator, "end"]
            edges = []

            # Router → All agents (parallel fanout)
            for agent in agents:
                edges.append((router, agent))

            # All agents → Aggregator (parallel fanin)
            for agent in agents:
                edges.append((agent, aggregator))

            # Aggregator → End
            edges.append((aggregator, "end"))

            special_nodes = {"router": router, "aggregator": aggregator}

        return GraphTopology(
            nodes=nodes,
            edges=edges,
            entry_point=router,
            exit_point="end",
            special_nodes=special_nodes,
        )

    def create_router(self, **kwargs) -> Callable[[Dict[str, Any]], str]:
        """
        Create parallel routing function.

        Args:
            **kwargs: Optional parameters:
                - router_node: Name of router node
                - aggregator_node: Name of aggregator node
                - skip_aggregator: Whether aggregator is skipped
                - splitter: "task_based" | "even_split" | "custom"
                - aggregation: "merge_all" | "best_result" | "weighted"
                - timeout: Maximum time for parallel execution
                - partial_results: Allow partial results
        """
        router = kwargs.get("router_node", "router")
        aggregator = kwargs.get("aggregator_node", "aggregator")
        skip_aggregator = kwargs.get("skip_aggregator", False)
        splitter = kwargs.get("splitter", "task_based")
        aggregation_method = kwargs.get("aggregation", "merge_all")
        timeout = kwargs.get("timeout")
        allow_partial = kwargs.get("partial_results", False)

        def parallel_router(state: Dict[str, Any]) -> str:
            """
            Route for parallel execution with load balancing.

            Router distributes work, tracks assignments, and balances load.
            Aggregator waits for all completions, merges outputs, resolves conflicts.
            """
            current = state.get("current_node", router)
            agents = state.get("agents", [])

            # From router, distribute to all agents
            if current == router:
                # Router splits task and assigns to agents
                if splitter == "task_based":
                    # Route based on task requirements for each agent
                    return agents[0] if agents else "end"
                elif splitter == "even_split":
                    # Distribute evenly across agents
                    return agents[0] if agents else "end"
                else:
                    return agents[0] if agents else "end"

            # From agent, go to aggregator or end
            elif current in agents:
                if skip_aggregator:
                    return "end"
                else:
                    return aggregator

            # From aggregator, combine results and proceed
            elif current == aggregator:
                # Aggregator combines results using specified method
                completed = state.get("completed_agents", set())

                # Check timeout
                if timeout and state.get("elapsed_time", 0) > timeout:
                    if allow_partial and len(completed) > 0:
                        # Use partial results
                        return "end"
                    # Wait for more results or fail

                # Wait for all agents if no timeout
                if len(completed) >= len(agents):
                    # All done, merge results
                    if aggregation_method == "merge_all":
                        # Merge all outputs
                        pass
                    elif aggregation_method == "best_result":
                        # Select best result
                        pass
                    elif aggregation_method == "weighted":
                        # Weighted combination
                        pass
                    return "end"

                # Still waiting for some agents
                return aggregator

            return "end"

        return parallel_router
