from typing import Any, Dict, List, Callable
from .base import CollaborationPattern, PatternMetadata, PatternType, GraphTopology


class CompetitivePattern(CollaborationPattern):
    """
    Competitive pattern: Multiple agents compete to provide the best solution.

    Graph: [Initiator] → [Agent1/2/3] → [Evaluator] → [Best Result] → [End]

    Process:
    1. Competition Setup: Same problem to all, different approaches allowed, time/resource limits
    2. Evaluation: Compare all results, apply scoring rubric based on metrics
    3. Selection: Select winner, document reasoning, optional fallback strategy

    Evaluation Criteria:
    - Quality metrics
    - Performance scores
    - Resource efficiency
    - Time to completion

    Best for:
    - Quality optimization
    - Multiple approaches to same problem
    - Performance comparison
    - Best-of-breed selection
    - Tournament-style evaluation
    """

    def _create_metadata(self) -> PatternMetadata:
        return PatternMetadata(
            name="Competitive",
            description="Agents compete for best solution, judge selects winner",
            pattern_type=PatternType.COMPETITIVE,
            min_agents=2,
            requires_judge=True,
            tags=["competitive", "tournament", "selection", "quality"],
        )

    def build_topology(self, agents: List[str], **kwargs) -> GraphTopology:
        """
        Build competitive pattern topology.

        Args:
            agents: List of competing agent names
            **kwargs: Optional parameters:
                - initiator_node: Name for initiator node (default: "initiator")
                - evaluator_node: Name for evaluator node (default: "evaluator")
                - elimination_rounds: Enable tournament elimination (default: False)
                - evaluation_metrics: List of metrics ["quality", "speed", "cost"]
                - selection_strategy: "highest_score" | "weighted" | "pareto"
        """
        self.validate_agents(agents)

        initiator = kwargs.get("initiator_node", "initiator")
        evaluator = kwargs.get("evaluator_node", "evaluator")
        elimination_rounds = kwargs.get("elimination_rounds", False)

        nodes = [initiator] + agents + [evaluator, "end"]
        edges = []

        # Initiator → All agents (parallel competition)
        for agent in agents:
            edges.append((initiator, agent))

        # All agents → Evaluator
        for agent in agents:
            edges.append((agent, evaluator))

        # Optional: Elimination rounds (evaluator sends back to subset)
        if elimination_rounds:
            for agent in agents:
                edges.append((evaluator, agent))

        # Evaluator → End
        edges.append((evaluator, "end"))

        return GraphTopology(
            nodes=nodes,
            edges=edges,
            entry_point=initiator,
            exit_point="end",
            special_nodes={"initiator": initiator, "evaluator": evaluator},
        )

    def create_router(self, **kwargs) -> Callable[[Dict[str, Any]], str]:
        """
        Create competitive routing function.

        Args:
            **kwargs: Optional parameters:
                - initiator_node: Name of initiator node
                - evaluator_node: Name of evaluator node
                - elimination_rounds: Whether to use elimination
                - evaluation_metrics: ["quality", "speed", "cost", "performance"]
                - selection_strategy: "highest_score" | "weighted" | "pareto"
                - scoring_function: Custom function to score agent results
                - metric_weights: Dict of metric weights {"quality": 0.5, "speed": 0.3, "cost": 0.2}
                - fallback: "use_all_results" | "use_top_n" | "fail"
        """
        initiator = kwargs.get("initiator_node", "initiator")
        evaluator = kwargs.get("evaluator_node", "evaluator")
        elimination_rounds = kwargs.get("elimination_rounds", False)
        evaluation_metrics = kwargs.get(
            "evaluation_metrics", ["quality", "speed", "cost"]
        )
        selection_strategy = kwargs.get("selection_strategy", "highest_score")
        scoring_function = kwargs.get("scoring_function")
        metric_weights = kwargs.get("metric_weights", {})
        fallback = kwargs.get("fallback", "use_all_results")

        # Default weights if not provided
        if not metric_weights:
            weight_per_metric = 1.0 / len(evaluation_metrics)
            metric_weights = {m: weight_per_metric for m in evaluation_metrics}

        def competitive_router(state: Dict[str, Any]) -> str:
            """
            Route for competitive evaluation.

            Process:
            1. Initiator distributes same problem to all competitors
            2. Agents compete independently with time/resource limits
            3. Evaluator compares results using scoring rubric
            4. Best result selected with documented reasoning
            """
            current = state.get("current_node", initiator)
            agents = state.get("agents", [])

            # From initiator, distribute to all competitors
            if current == initiator:
                return agents[0] if agents else evaluator

            # From agent, go to evaluator
            elif current in agents:
                return evaluator

            # From evaluator, evaluate and route
            elif current == evaluator:
                completed = state.get("completed_agents", set())

                # Ensure we have results from all agents
                if len(completed) < len(agents):
                    return evaluator  # Wait for all

                # Evaluate all results
                if scoring_function:
                    scores = {
                        agent: scoring_function(state.get(f"{agent}_result"))
                        for agent in completed
                    }
                else:
                    # Calculate scores based on metrics
                    scores = {}
                    for agent in completed:
                        result = state.get(f"{agent}_result", {})
                        agent_score = 0.0

                        for metric in evaluation_metrics:
                            metric_value = result.get(metric, 0)
                            weight = metric_weights.get(metric, 0)
                            agent_score += metric_value * weight

                        scores[agent] = agent_score

                # Apply selection strategy
                if selection_strategy == "highest_score":
                    winner = max(scores.items(), key=lambda x: x[1])[0]
                    state["winner"] = winner
                    state["winner_score"] = scores[winner]
                    state["all_scores"] = scores

                elif selection_strategy == "weighted":
                    # Already done above with metric_weights
                    winner = max(scores.items(), key=lambda x: x[1])[0]
                    state["winner"] = winner
                    state["winner_score"] = scores[winner]

                elif selection_strategy == "pareto":
                    # Multi-objective optimization (Pareto optimal)
                    # Find non-dominated solutions
                    pareto_front = []
                    for agent in completed:
                        result = state.get(f"{agent}_result", {})
                        is_dominated = False
                        for other in completed:
                            if agent == other:
                                continue
                            other_result = state.get(f"{other}_result", {})
                            # Check if other dominates agent
                            better_in_all = all(
                                other_result.get(m, 0) >= result.get(m, 0)
                                for m in evaluation_metrics
                            )
                            better_in_some = any(
                                other_result.get(m, 0) > result.get(m, 0)
                                for m in evaluation_metrics
                            )
                            if better_in_all and better_in_some:
                                is_dominated = True
                                break
                        if not is_dominated:
                            pareto_front.append(agent)

                    # Select from Pareto front (e.g., first one or based on weights)
                    if pareto_front:
                        state["winner"] = pareto_front[0]
                        state["pareto_front"] = pareto_front

                # Handle elimination rounds
                if elimination_rounds:
                    remaining = state.get("remaining_agents", agents)

                    if len(remaining) == 1:
                        # We have a winner
                        state["winner"] = remaining[0]
                        state["tournament_complete"] = True
                        return "end"

                    # Eliminate lowest performers (keep top half)
                    sorted_agents = sorted(
                        scores.items(), key=lambda x: x[1], reverse=True
                    )
                    remaining = [a for a, _ in sorted_agents[: len(sorted_agents) // 2]]
                    state["remaining_agents"] = remaining
                    state["agents"] = remaining  # Update active agents

                    # Start new round with remaining agents
                    return initiator

                # Single round: select best and end
                # Apply fallback strategy if needed
                if not state.get("winner") and fallback == "use_all_results":
                    state["all_results"] = {
                        agent: state.get(f"{agent}_result") for agent in completed
                    }
                elif fallback == "use_top_n":
                    top_n = state.get("fallback_top_n", 3)
                    sorted_agents = sorted(
                        scores.items(), key=lambda x: x[1], reverse=True
                    )
                    state["top_results"] = {
                        a: scores[a] for a, _ in sorted_agents[:top_n]
                    }

                return "end"

            return "end"

        return competitive_router
