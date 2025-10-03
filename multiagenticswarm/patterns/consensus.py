from typing import Any, Dict, List, Callable
from .base import CollaborationPattern, PatternMetadata, PatternType, GraphTopology


class ConsensusPattern(CollaborationPattern):
    """
    Consensus pattern: Multiple agents work on the same task and must agree on the result.

    Graph: [Distributor] → [Agent1/2/3] → [Voting] → [Decision] → [End]

    Process:
    1. Distribution: Same task to all agents, identical inputs, independent processing
    2. Voting: Collect all outputs, compare results, apply voting rules
    3. Decision: Determine consensus using rules (unanimous, majority, weighted, threshold)

    Best for:
    - High reliability needed
    - Multiple perspectives valuable
    - Risk mitigation
    - Quality assurance
    - Democratic decision making
    """

    def _create_metadata(self) -> PatternMetadata:
        return PatternMetadata(
            name="Consensus",
            description="Agents propose solutions, consensus node aggregates and decides",
            pattern_type=PatternType.CONSENSUS,
            min_agents=2,
            tags=["consensus", "voting", "aggregation", "democratic"],
        )

    def build_topology(self, agents: List[str], **kwargs) -> GraphTopology:
        """
        Build consensus pattern topology.

        Args:
            agents: List of agent names to contribute proposals
            **kwargs: Optional parameters:
                - distributor_node: Name for distributor node (default: "distributor")
                - voting_node: Name for voting node (default: "voting")
                - decision_node: Name for decision node (default: "decision")
                - voting_rounds: Number of voting rounds (default: 1)
                - voting_method: "unanimous" | "majority" | "weighted" | "threshold"
        """
        self.validate_agents(agents)

        distributor = kwargs.get("distributor_node", "distributor")
        voting = kwargs.get("voting_node", "voting")
        decision = kwargs.get("decision_node", "decision")
        voting_rounds = kwargs.get("voting_rounds", 1)

        nodes = [distributor] + agents + [voting, decision, "end"]
        edges = []

        # Distributor → All agents (parallel proposal phase)
        for agent in agents:
            edges.append((distributor, agent))

        # All agents → Voting
        for agent in agents:
            edges.append((agent, voting))

        # Voting → Decision
        edges.append((voting, decision))

        # Optional: Multi-round voting
        if voting_rounds > 1:
            # Decision can send back to distributor for refinement
            edges.append((decision, distributor))

        # Decision → End
        edges.append((decision, "end"))

        return GraphTopology(
            nodes=nodes,
            edges=edges,
            entry_point=distributor,
            exit_point="end",
            special_nodes={
                "distributor": distributor,
                "voting": voting,
                "decision": decision,
            },
        )

    def create_router(self, **kwargs) -> Callable[[Dict[str, Any]], str]:
        """
        Create consensus routing function.

        Args:
            **kwargs: Optional parameters:
                - distributor_node: Name of distributor node
                - voting_node: Name of voting node
                - decision_node: Name of decision node
                - voting_rounds: Number of rounds
                - voting_method: "unanimous" | "majority" | "weighted" | "threshold"
                - minimum_votes: Minimum votes required
                - consensus_threshold: Threshold for agreement (0-1)
                - tie_breaker: "senior_agent" | "random" | "weighted"
        """
        distributor = kwargs.get("distributor_node", "distributor")
        voting = kwargs.get("voting_node", "voting")
        decision = kwargs.get("decision_node", "decision")
        voting_rounds = kwargs.get("voting_rounds", 1)
        voting_method = kwargs.get("voting_method", "majority")
        minimum_votes = kwargs.get("minimum_votes", 2)
        consensus_threshold = kwargs.get("consensus_threshold", 0.7)
        tie_breaker = kwargs.get("tie_breaker", "senior_agent")

        def consensus_router(state: Dict[str, Any]) -> str:
            """
            Route for consensus building.

            Process:
            1. Distributor sends identical task to all agents
            2. Agents work independently (no collaboration)
            3. Voting collects and compares all outputs
            4. Decision applies voting rules and determines consensus
            """
            current = state.get("current_node", distributor)
            agents = state.get("agents", [])

            # From distributor, go to first agent (executor handles parallel)
            if current == distributor:
                return agents[0] if agents else voting

            # From agent, go to voting
            elif current in agents:
                return voting

            # From voting, go to decision
            elif current == voting:
                # Collect all outputs and compare
                completed = state.get("completed_agents", set())

                if len(completed) >= minimum_votes:
                    # Enough votes collected, proceed to decision
                    state["votes"] = {
                        agent: state.get(f"{agent}_result") for agent in completed
                    }
                    return decision
                else:
                    # Wait for more votes
                    return voting

            # From decision, check consensus and route
            elif current == decision:
                current_round = state.get("voting_round", 1)
                votes = state.get("votes", {})

                # Apply voting method
                consensus_reached = False

                if voting_method == "unanimous":
                    # All agents must agree
                    results = list(votes.values())
                    consensus_reached = len(set(str(r) for r in results)) == 1

                elif voting_method == "majority":
                    # More than 50% must agree
                    from collections import Counter

                    results = [str(v) for v in votes.values()]
                    most_common = Counter(results).most_common(1)
                    if most_common:
                        agreement = most_common[0][1] / len(results)
                        consensus_reached = agreement > 0.5

                elif voting_method == "weighted":
                    # Weighted voting based on agent weights
                    agent_weights = state.get("agent_weights", {})
                    weighted_votes = {}
                    for agent, vote in votes.items():
                        weight = agent_weights.get(agent, 1.0)
                        weighted_votes[vote] = weighted_votes.get(vote, 0) + weight
                    total_weight = sum(agent_weights.get(a, 1.0) for a in votes.keys())
                    if weighted_votes:
                        max_weight = max(weighted_votes.values())
                        consensus_reached = (
                            max_weight / total_weight
                        ) >= consensus_threshold

                elif voting_method == "threshold":
                    # Threshold-based agreement
                    from collections import Counter

                    results = [str(v) for v in votes.values()]
                    most_common = Counter(results).most_common(1)
                    if most_common:
                        agreement = most_common[0][1] / len(results)
                        consensus_reached = agreement >= consensus_threshold

                # Check if consensus reached or max rounds exhausted
                if consensus_reached or current_round >= voting_rounds:
                    # Consensus reached or max rounds done
                    if not consensus_reached and tie_breaker:
                        # Apply tie breaker
                        if tie_breaker == "senior_agent":
                            # Use most experienced agent's vote
                            senior = state.get("senior_agent", agents[0])
                            state["final_decision"] = votes.get(senior)
                        elif tie_breaker == "random":
                            import random

                            state["final_decision"] = random.choice(
                                list(votes.values())
                            )
                    return "end"
                else:
                    # Go back for refinement round
                    state["voting_round"] = current_round + 1
                    return distributor

            return "end"

        return consensus_router
