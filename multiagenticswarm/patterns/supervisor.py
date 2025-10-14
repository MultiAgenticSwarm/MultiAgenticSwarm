from typing import Any, Dict, List, Callable
from .base import CollaborationPattern, PatternMetadata, PatternType, GraphTopology


class SupervisorPattern(CollaborationPattern):
    """
    Supervisor pattern: Central supervisor node routes to worker agents, collects results, and makes decisions.

    Graph: [Start] → [Supervisor] → [Agent1/2/3] → [Supervisor] → [End]

    The supervisor:
    - Receives initial task
    - Delegates subtasks to appropriate agents
    - Collects and synthesizes results
    - Makes final decision
    """

    def _create_metadata(self) -> PatternMetadata:
        return PatternMetadata(
            name="Supervisor",
            description="Central coordinator delegates tasks to workers and synthesizes results",
            pattern_type=PatternType.SUPERVISOR,
            min_agents=1,
            requires_supervisor=True,
            tags=["coordination", "delegation", "centralized"],
        )

    def build_topology(self, agents: List[str], **kwargs) -> GraphTopology:
        """
        Build supervisor pattern topology.

        Args:
            agents: List of worker agent names
            **kwargs: Optional parameters:
                - supervisor_name: Name for supervisor node (default: "supervisor")
                - add_start_end: Whether to add start/end nodes (default: True)
        """
        self.validate_agents(agents)

        supervisor = kwargs.get("supervisor_name", "supervisor")
        add_start_end = kwargs.get("add_start_end", True)

        nodes = [supervisor] + agents
        edges = []
        special_nodes = {"supervisor": supervisor}

        if add_start_end:
            nodes = ["start"] + nodes + ["end"]
            entry_point = "start"
            exit_point = "end"

            # Start → Supervisor
            edges.append(("start", supervisor))
            # Supervisor → End
            edges.append((supervisor, "end"))
        else:
            entry_point = supervisor
            exit_point = supervisor

        # Supervisor ↔ Agents (bidirectional)
        for agent in agents:
            edges.append((supervisor, agent))
            edges.append((agent, supervisor))

        return GraphTopology(
            nodes=nodes,
            edges=edges,
            entry_point=entry_point,
            exit_point=exit_point,
            special_nodes=special_nodes,
        )

    def create_router(self, **kwargs) -> Callable[[Dict[str, Any]], str]:
        """
        Create supervisor routing function.

        Args:
            **kwargs: Optional parameters:
                - supervisor_name: Name of supervisor node
                - routing_strategy: "round_robin" | "capability_based" | "load_balanced" | "priority" | "custom"
                - aggregation_method: "supervisor_decision" | "merge_all" | "best_result"
                - quality_control: bool - Enable quality control (default: False)
                - custom_router: Custom routing function
        """
        supervisor = kwargs.get("supervisor_name", "supervisor")
        strategy = kwargs.get("routing_strategy", "capability_based")
        aggregation = kwargs.get("aggregation_method", "supervisor_decision")
        quality_control = kwargs.get("quality_control", False)
        custom_router = kwargs.get("custom_router")

        if custom_router:
            return custom_router

        def supervisor_router(state: Dict[str, Any]) -> str:
            """
            Route based on current node and task completion.

            Supervisor receives all inputs, assigns tasks to agents,
            reviews outputs, makes routing decisions, and handles conflicts.
            """
            current = state.get("current_node", supervisor)
            agents = state.get("agents", [])

            # If at supervisor, route to next agent or end
            if current == supervisor:
                # Check if all agents are done
                completed = state.get("completed_agents", set())

                if strategy == "round_robin":
                    # Distribute tasks evenly
                    for agent in agents:
                        if agent not in completed:
                            return agent

                elif strategy == "capability_based":
                    # Route based on agent capabilities
                    task_type = state.get("task_type")
                    agent_capabilities = state.get("agent_capabilities", {})
                    for agent in agents:
                        if agent not in completed:
                            capabilities = agent_capabilities.get(agent, [])
                            if task_type in capabilities or not task_type:
                                return agent

                elif strategy == "load_balanced":
                    # Route to least busy agent
                    agent_loads = state.get("agent_loads", {})
                    available = [a for a in agents if a not in completed]
                    if available:
                        return min(available, key=lambda a: agent_loads.get(a, 0))

                elif strategy == "priority":
                    # Route based on task priority
                    task_priority = state.get("task_priority", 0)
                    agent_priorities = state.get("agent_priorities", {})
                    for agent in agents:
                        if agent not in completed:
                            if agent_priorities.get(agent, 0) >= task_priority:
                                return agent

                # Quality control check before ending
                if quality_control and len(completed) == len(agents):
                    if not state.get("quality_approved", False):
                        # Supervisor reviews all outputs before approval
                        state["needs_review"] = True
                        return supervisor

                # All done, go to end
                return state.get("exit_point", "end")

            # If at agent, return to supervisor for review and next assignment
            elif current in agents:
                return supervisor

            return state.get("exit_point", "end")

        return supervisor_router
