from typing import Any, Dict, List, Callable, Optional
from .base import CollaborationPattern, PatternMetadata, PatternType, GraphTopology


class CompositePattern(CollaborationPattern):
    """
    Composite pattern: Combines multiple patterns into a larger workflow.

    Supports:
    - Sequential composition: Pattern A → Pattern B
    - Nested composition: Pattern A contains Pattern B
    - Conditional routing between patterns
    """

    def __init__(
        self, patterns: List[CollaborationPattern], name: Optional[str] = None, **kwargs
    ):
        """
        Initialize composite pattern.

        Args:
            patterns: List of patterns to compose
            name: Optional name for the composite
            **kwargs: Composition options:
                - composition_type: "sequential" | "nested" | "conditional"
        """
        self._patterns = patterns
        self._composition_type = kwargs.get("composition_type", "sequential")
        super().__init__(name or f"Composite[{','.join(p.name for p in patterns)}]")

    def _create_metadata(self) -> PatternMetadata:
        return PatternMetadata(
            name=self._name,
            description=f"Composition of {len(self._patterns)} patterns",
            pattern_type=PatternType.CUSTOM,
            min_agents=max(p.metadata.min_agents for p in self._patterns),
            composable=True,
            tags=["composite", "composed", self._composition_type],
        )

    def build_topology(self, agents: List[str], **kwargs) -> GraphTopology:
        """
        Build composite pattern topology by merging sub-patterns.

        Args:
            agents: List of all agents (distributed across patterns)
            **kwargs: Composition parameters:
                - agent_assignment: Dict mapping pattern index to agent list
        """
        self.validate_agents(agents)

        agent_assignment = kwargs.get("agent_assignment", {})

        if self._composition_type == "sequential":
            return self._build_sequential_composition(agents, agent_assignment)
        elif self._composition_type == "nested":
            return self._build_nested_composition(agents, agent_assignment)
        elif self._composition_type == "conditional":
            return self._build_conditional_composition(agents, agent_assignment)
        else:
            raise ValueError(f"Unknown composition type: {self._composition_type}")

    def _build_sequential_composition(
        self, agents: List[str], agent_assignment: Dict[int, List[str]]
    ) -> GraphTopology:
        """Build sequential composition: Pattern1 → Pattern2 → ..."""
        all_nodes = ["start"]
        all_edges = []
        special_nodes = {}

        prev_exit = "start"

        for i, pattern in enumerate(self._patterns):
            # Get agents for this pattern
            pattern_agents = agent_assignment.get(i, agents)

            # Build pattern topology (without start/end)
            topology = pattern.build_topology(pattern_agents, add_start_end=False)

            # Prefix nodes to avoid conflicts
            prefix = f"p{i}_"
            prefixed_nodes = [
                f"{prefix}{n}" for n in topology.nodes if n not in ["start", "end"]
            ]

            # Add nodes
            all_nodes.extend(prefixed_nodes)

            # Connect previous pattern to this pattern's entry
            pattern_entry = f"{prefix}{topology.entry_point}"
            all_edges.append((prev_exit, pattern_entry))

            # Add internal edges (with prefix)
            for source, target in topology.edges:
                if source not in ["start", "end"] and target not in ["start", "end"]:
                    all_edges.append((f"{prefix}{source}", f"{prefix}{target}"))

            # Track special nodes
            for key, node in topology.special_nodes.items():
                special_nodes[f"{prefix}{key}"] = f"{prefix}{node}"

            # Update previous exit
            prev_exit = f"{prefix}{topology.exit_point}"

        # Add final end node
        all_nodes.append("end")
        all_edges.append((prev_exit, "end"))

        return GraphTopology(
            nodes=all_nodes,
            edges=all_edges,
            entry_point="start",
            exit_point="end",
            special_nodes=special_nodes,
        )

    def _build_nested_composition(
        self, agents: List[str], agent_assignment: Dict[int, List[str]]
    ) -> GraphTopology:
        """Build nested composition: Outer pattern contains inner patterns."""
        # For nested, the first pattern is the outer pattern
        outer_pattern = self._patterns[0]
        inner_patterns = self._patterns[1:]

        # Get outer topology
        outer_agents = agent_assignment.get(0, agents[: len(agents) // 2])
        outer_topology = outer_pattern.build_topology(outer_agents)

        # Replace each agent node with a sub-pattern
        all_nodes = []
        all_edges = []
        special_nodes = dict(outer_topology.special_nodes)

        for node in outer_topology.nodes:
            if node in outer_agents and inner_patterns:
                # Replace this agent with a pattern
                pattern_idx = outer_agents.index(node) % len(inner_patterns)
                inner_pattern = inner_patterns[pattern_idx]

                # Get agents for inner pattern
                inner_agents = agent_assignment.get(
                    pattern_idx + 1, [f"{node}_sub_{i}" for i in range(2)]
                )
                inner_topology = inner_pattern.build_topology(
                    inner_agents, add_start_end=False
                )

                # Add inner nodes with prefix
                prefix = f"{node}_"
                for inner_node in inner_topology.nodes:
                    all_nodes.append(f"{prefix}{inner_node}")

                # Add inner edges
                for source, target in inner_topology.edges:
                    all_edges.append((f"{prefix}{source}", f"{prefix}{target}"))

                # Update outer edges to connect to inner pattern
                inner_entry = f"{prefix}{inner_topology.entry_point}"
                inner_exit = f"{prefix}{inner_topology.exit_point}"

                for source, target in outer_topology.edges:
                    if target == node:
                        all_edges.append((source, inner_entry))
                    elif source == node:
                        all_edges.append((inner_exit, target))
                    elif source != node and target != node:
                        all_edges.append((source, target))
            else:
                # Keep original node
                all_nodes.append(node)

        # Add outer edges (non-agent edges)
        for source, target in outer_topology.edges:
            if source not in outer_agents and target not in outer_agents:
                all_edges.append((source, target))

        return GraphTopology(
            nodes=all_nodes,
            edges=all_edges,
            entry_point=outer_topology.entry_point,
            exit_point=outer_topology.exit_point,
            special_nodes=special_nodes,
        )

    def _build_conditional_composition(
        self, agents: List[str], agent_assignment: Dict[int, List[str]]
    ) -> GraphTopology:
        """Build conditional composition: Router decides which pattern to use."""
        all_nodes = ["start", "router"]
        all_edges = [("start", "router")]
        special_nodes = {"router": "router"}

        pattern_exits = []

        for i, pattern in enumerate(self._patterns):
            pattern_agents = agent_assignment.get(i, agents)
            topology = pattern.build_topology(pattern_agents, add_start_end=False)

            prefix = f"p{i}_"
            prefixed_nodes = [
                f"{prefix}{n}" for n in topology.nodes if n not in ["start", "end"]
            ]

            all_nodes.extend(prefixed_nodes)

            # Router → Pattern entry
            pattern_entry = f"{prefix}{topology.entry_point}"
            all_edges.append(("router", pattern_entry))

            # Add internal edges
            for source, target in topology.edges:
                if source not in ["start", "end"] and target not in ["start", "end"]:
                    all_edges.append((f"{prefix}{source}", f"{prefix}{target}"))

            # Track exit
            pattern_exits.append(f"{prefix}{topology.exit_point}")

        # All pattern exits → end
        all_nodes.append("end")
        for exit_node in pattern_exits:
            all_edges.append((exit_node, "end"))

        return GraphTopology(
            nodes=all_nodes,
            edges=all_edges,
            entry_point="start",
            exit_point="end",
            special_nodes=special_nodes,
        )

    def create_router(self, **kwargs) -> Callable[[Dict[str, Any]], str]:
        """
        Create composite routing function.

        Args:
            **kwargs: Routing options:
                - pattern_routers: List of router functions for each pattern
                - condition_function: For conditional composition
        """
        pattern_routers = kwargs.get("pattern_routers", [])
        condition_function = kwargs.get("condition_function")

        def composite_router(state: Dict[str, Any]) -> str:
            """Route within composite pattern."""
            current = state.get("current_node", "start")

            if self._composition_type == "conditional" and current == "router":
                # Use condition to select pattern
                if condition_function:
                    pattern_idx = condition_function(state)
                    return f"p{pattern_idx}_{self._patterns[pattern_idx].metadata.name}"

            # Delegate to appropriate sub-pattern router
            for i, router in enumerate(pattern_routers):
                if current.startswith(f"p{i}_"):
                    return router(state)

            return "end"

        return composite_router
