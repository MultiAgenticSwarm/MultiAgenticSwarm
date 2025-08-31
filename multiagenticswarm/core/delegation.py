"""
Simple delegation strategies for multi-agent collaboration.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from ..utils.logger import get_logger

logger = get_logger(__name__)


class DelegationStrategy(str, Enum):
    """Delegation strategy types."""

    HIERARCHICAL = "hierarchical"  # Top-down task breakdown
    AUTONOMOUS = "autonomous"  # Bottom-up self-organization
    COLLABORATIVE = "collaborative"  # Peer-to-peer negotiation


class SimpleDelegator:
    """
    Simple task delegation coordinator that respects collaboration prompts.

    Implements three delegation approaches:
    - Hierarchical: Designated lead breaks down tasks
    - Autonomous: Agents self-organize based on capabilities
    - Collaborative: Agents negotiate through progress board
    """

    def __init__(self, strategy: str, collaboration_prompt: str, progress_board):
        """
        Initialize delegator with strategy and collaboration prompt.

        Args:
            strategy: Delegation strategy to use
            collaboration_prompt: Instructions for how agents should collaborate
            progress_board: ProgressBoard tool for communication
        """
        self.strategy = strategy
        self.collaboration_prompt = collaboration_prompt
        self.progress_board = progress_board
        self.logger = get_logger(f"{__name__}.SimpleDelegator")

    async def delegate_task(
        self,
        main_task: str,
        agents: List[str],
        strategy: Optional[DelegationStrategy] = None,
        lead_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Delegate a main task to agents using specified strategy.

        Args:
            main_task: The main task to be delegated
            agents: List of agent names to delegate to
            strategy: Override the default strategy if provided
            lead_agent: Designated lead agent for hierarchical strategy

        Returns:
            Delegation plan and coordination info
        """
        used_strategy = strategy or self.strategy

        self.logger.info(
            f"Delegating task using {used_strategy} strategy to {len(agents)} agents"
        )

        # Delegate based on strategy
        if used_strategy == DelegationStrategy.HIERARCHICAL:
            return await self._hierarchical_delegation(
                main_task, agents, lead_agent, self.collaboration_prompt
            )
        elif used_strategy == DelegationStrategy.AUTONOMOUS:
            return await self._autonomous_delegation(
                main_task, agents, self.collaboration_prompt
            )
        elif used_strategy == DelegationStrategy.COLLABORATIVE:
            return await self._collaborative_delegation(
                main_task, agents, self.collaboration_prompt
            )
        else:
            raise ValueError(f"Unknown delegation strategy: {used_strategy}")

    async def _hierarchical_delegation(
        self,
        main_task: str,
        agents: List[str],
        lead_agent: Optional[str],
        collaboration_prompt: Optional[str],
    ) -> Dict[str, Any]:
        """
        Hierarchical delegation: Lead agent breaks down tasks.

        Args:
            main_task: Main task to delegate
            agents: Available agents
            lead_agent: Designated lead agent
            collaboration_prompt: Collaboration instructions

        Returns:
            Hierarchical delegation plan
        """
        # Use first agent as lead if not specified
        lead = lead_agent or agents[0]
        subordinates = [a for a in agents if a != lead]

        # Post delegation start
        self.progress_board.post_update(
            agent_name="SimpleDelegator",
            message=f"Starting hierarchical delegation with lead: {lead}",
            update_type="delegation_start",
            tags=["delegation", "hierarchical"],
        )

        # Lead agent analyzes task and collaboration prompt
        delegation_plan = {
            "strategy": "hierarchical",
            "lead_agent": lead,
            "subordinate_agents": subordinates,
            "main_task": main_task,
            "collaboration_prompt": collaboration_prompt,
            "task_breakdown": [],
            "coordination_method": "lead_directed",
        }

        # Post delegation plan
        self.progress_board.post_update(
            agent_name=lead,
            message=f"Lead agent analyzing task: {main_task[:100]}...",
            update_type="task_analysis",
            tags=["analysis", "lead"],
        )

        # In a real implementation, the lead agent would use LLM to break down tasks
        # For now, we create a basic structure
        basic_breakdown = self._create_basic_flutter_breakdown(
            main_task, agents, collaboration_prompt
        )
        delegation_plan["task_breakdown"] = basic_breakdown

        # Assign tasks based on collaboration prompt roles
        if collaboration_prompt and "Agent1" in collaboration_prompt:
            # Parse roles from collaboration prompt
            role_assignments = self._parse_collaboration_roles(
                collaboration_prompt, agents
            )
            delegation_plan["role_assignments"] = role_assignments

        self.logger.info(
            f"Hierarchical delegation completed with {len(basic_breakdown)} subtasks"
        )
        return delegation_plan

    async def _autonomous_delegation(
        self, main_task: str, agents: List[str], collaboration_prompt: Optional[str]
    ) -> Dict[str, Any]:
        """
        Autonomous delegation: Agents self-organize based on capabilities.

        Args:
            main_task: Main task to delegate
            agents: Available agents
            collaboration_prompt: Collaboration instructions

        Returns:
            Autonomous delegation plan
        """
        # Post delegation start
        self.progress_board.post_update(
            agent_name="SimpleDelegator",
            message=f"Starting autonomous delegation with {len(agents)} agents",
            update_type="delegation_start",
            tags=["delegation", "autonomous"],
        )

        delegation_plan = {
            "strategy": "autonomous",
            "agents": agents,
            "main_task": main_task,
            "collaboration_prompt": collaboration_prompt,
            "agent_proposals": [],
            "coordination_method": "self_organization",
        }

        # Each agent analyzes task and proposes contribution
        for agent in agents:
            self.progress_board.post_update(
                agent_name=agent,
                message=f"Analyzing task for autonomous contribution: {main_task[:50]}...",
                update_type="task_analysis",
                tags=["analysis", "autonomous"],
            )

            # Create proposal based on agent name/role hints
            proposal = self._create_agent_proposal(
                agent, main_task, collaboration_prompt
            )
            delegation_plan["agent_proposals"].append(proposal)

            # Post proposal
            self.progress_board.post_update(
                agent_name=agent,
                message=f"Proposed contribution: {proposal['contribution'][:50]}...",
                update_type="proposal",
                tags=["proposal", "autonomous"],
            )

        self.logger.info(
            f"Autonomous delegation completed with {len(agents)} proposals"
        )
        return delegation_plan

    async def _collaborative_delegation(
        self, main_task: str, agents: List[str], collaboration_prompt: Optional[str]
    ) -> Dict[str, Any]:
        """
        Collaborative delegation: Agents negotiate through progress board.

        Args:
            main_task: Main task to delegate
            agents: Available agents
            collaboration_prompt: Collaboration instructions

        Returns:
            Collaborative delegation plan
        """
        # Post delegation start
        self.progress_board.post_update(
            agent_name="SimpleDelegator",
            message=f"Starting collaborative delegation with {len(agents)} agents",
            update_type="delegation_start",
            tags=["delegation", "collaborative"],
        )

        delegation_plan = {
            "strategy": "collaborative",
            "agents": agents,
            "main_task": main_task,
            "collaboration_prompt": collaboration_prompt,
            "negotiation_rounds": [],
            "coordination_method": "peer_negotiation",
        }

        # Conduct multiple rounds of negotiation
        for round_num in range(1, 4):  # 3 rounds max
            round_negotiations = []

            self.progress_board.post_update(
                agent_name="SimpleDelegator",
                message=f"Starting negotiation round {round_num}",
                update_type="negotiation_round",
                tags=["negotiation", f"round_{round_num}"],
            )

            # Each agent proposes or adjusts based on previous rounds
            for agent in agents:
                # In round 1, initial proposals
                if round_num == 1:
                    proposal = self._create_agent_proposal(
                        agent, main_task, collaboration_prompt
                    )
                    message = f"Initial proposal: {proposal['contribution']}"
                else:
                    # Later rounds: adjustments based on coordination
                    proposal = self._create_adjustment_proposal(
                        agent, delegation_plan, round_num
                    )
                    message = (
                        f"Round {round_num} adjustment: {proposal['contribution']}"
                    )

                round_negotiations.append(
                    {
                        "agent": agent,
                        "round": round_num,
                        "proposal": proposal,
                        "timestamp": self.progress_board.post_update(
                            agent_name=agent,
                            message=message,
                            update_type="negotiation_proposal",
                            tags=["negotiation", f"round_{round_num}"],
                        )["timestamp"],
                    }
                )

            delegation_plan["negotiation_rounds"].append(
                {"round": round_num, "negotiations": round_negotiations}
            )

            # Check for consensus (simplified - agents agree on non-overlapping tasks)
            if self._check_consensus(round_negotiations):
                self.progress_board.post_update(
                    agent_name="SimpleDelegator",
                    message=f"Consensus reached in round {round_num}",
                    update_type="consensus",
                    tags=["negotiation", "consensus"],
                )
                break

        # Final coordination message
        self.progress_board.coordinate_with_team(
            agent_name="SimpleDelegator",
            message="Collaborative delegation completed. Beginning coordinated development.",
            coordination_type="start_coordination",
        )

        self.logger.info(
            f"Collaborative delegation completed after {len(delegation_plan['negotiation_rounds'])} rounds"
        )
        return delegation_plan

    def _create_basic_flutter_breakdown(
        self, main_task: str, agents: List[str], collaboration_prompt: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Create basic Flutter app task breakdown."""
        # Basic Flutter development tasks
        subtasks = [
            {
                "id": 1,
                "name": "UI Development",
                "description": "Create user interface screens and widgets",
                "assigned_agent": None,
                "dependencies": [],
                "estimated_hours": 8,
                "components": ["screens", "widgets", "navigation"],
            },
            {
                "id": 2,
                "name": "Audio Features",
                "description": "Implement audio playback and controls",
                "assigned_agent": None,
                "dependencies": [],
                "estimated_hours": 6,
                "components": ["audio_service", "player_controls", "streaming"],
            },
            {
                "id": 3,
                "name": "Data Management",
                "description": "Create data models and state management",
                "assigned_agent": None,
                "dependencies": [],
                "estimated_hours": 4,
                "components": ["models", "providers", "storage"],
            },
            {
                "id": 4,
                "name": "Integration & Testing",
                "description": "Integrate components and test app",
                "assigned_agent": None,
                "dependencies": [1, 2, 3],
                "estimated_hours": 3,
                "components": ["integration", "testing", "debugging"],
            },
        ]

        # Assign based on collaboration prompt hints or agent names
        if collaboration_prompt:
            role_assignments = self._parse_collaboration_roles(
                collaboration_prompt, agents
            )
            for subtask in subtasks:
                for agent, roles in role_assignments.items():
                    if any(role.lower() in subtask["name"].lower() for role in roles):
                        subtask["assigned_agent"] = agent
                        break

        # Fallback assignment by agent name hints
        for subtask in subtasks:
            if subtask["assigned_agent"] is None:
                for agent in agents:
                    if (
                        ("ui" in agent.lower() and "ui" in subtask["name"].lower())
                        or (
                            "audio" in agent.lower()
                            and "audio" in subtask["name"].lower()
                        )
                        or (
                            "data" in agent.lower()
                            and "data" in subtask["name"].lower()
                        )
                    ):
                        subtask["assigned_agent"] = agent
                        break

                # Default assignment
                if subtask["assigned_agent"] is None:
                    subtask["assigned_agent"] = agents[subtask["id"] % len(agents)]

        return subtasks

    def _parse_collaboration_roles(
        self, collaboration_prompt: str, agents: List[str]
    ) -> Dict[str, List[str]]:
        """Parse agent roles from collaboration prompt."""
        role_assignments = {}

        # Simple parsing - look for agent role descriptions
        lines = collaboration_prompt.split("\n")
        current_agent = None

        for line in lines:
            line = line.strip()

            # Look for agent role definitions
            if any(agent.lower() in line.lower() for agent in agents):
                for agent in agents:
                    if agent.lower() in line.lower():
                        current_agent = agent
                        role_assignments[agent] = []
                        break

            # Extract role keywords
            if current_agent and (
                "focuses on" in line.lower()
                or "handles" in line.lower()
                or "manages" in line.lower()
            ):
                roles = []
                if "ui" in line.lower() or "interface" in line.lower():
                    roles.append("UI")
                if (
                    "audio" in line.lower()
                    or "music" in line.lower()
                    or "playback" in line.lower()
                ):
                    roles.append("Audio")
                if (
                    "data" in line.lower()
                    or "state" in line.lower()
                    or "model" in line.lower()
                ):
                    roles.append("Data")

                if roles and current_agent in role_assignments:
                    role_assignments[current_agent].extend(roles)

        return role_assignments

    def _create_agent_proposal(
        self, agent: str, main_task: str, collaboration_prompt: Optional[str]
    ) -> Dict[str, Any]:
        """Create a proposal for what an agent can contribute."""
        # Analyze agent name/role for capabilities
        capabilities = []
        focus_areas = []

        agent_lower = agent.lower()
        if "ui" in agent_lower or "interface" in agent_lower:
            capabilities.extend(["UI Development", "Widget Creation", "Navigation"])
            focus_areas.append("User Interface")

        if "audio" in agent_lower or "music" in agent_lower:
            capabilities.extend(["Audio Playback", "Music Controls", "Streaming"])
            focus_areas.append("Audio Features")

        if "data" in agent_lower or "state" in agent_lower:
            capabilities.extend(["Data Models", "State Management", "Storage"])
            focus_areas.append("Data Management")

        if not capabilities:  # Generic agent
            capabilities = ["General Development", "Code Review", "Testing"]
            focus_areas.append("General Support")

        # Create contribution proposal
        if "flutter" in main_task.lower() and "music" in main_task.lower():
            if "ui" in agent_lower:
                contribution = "I'll handle the Flutter UI - screens, widgets, navigation, and user interface design using Material Design 3"
                estimated_time = "6-8 hours"
            elif "audio" in agent_lower:
                contribution = "I'll implement audio playback features - music player controls, streaming service, and audio state management"
                estimated_time = "5-7 hours"
            elif "data" in agent_lower:
                contribution = "I'll create data models, state management providers, and handle app data persistence"
                estimated_time = "4-6 hours"
            else:
                contribution = f"I'll provide {focus_areas[0].lower()} support and help with integration and testing"
                estimated_time = "3-5 hours"
        else:
            contribution = f"I can contribute {', '.join(capabilities).lower()} to support the main task"
            estimated_time = "4-6 hours"

        return {
            "agent": agent,
            "contribution": contribution,
            "capabilities": capabilities,
            "focus_areas": focus_areas,
            "estimated_time": estimated_time,
            "dependencies": [],
            "collaboration_notes": "Ready to coordinate with team members",
        }

    def _create_adjustment_proposal(
        self, agent: str, delegation_plan: Dict[str, Any], round_num: int
    ) -> Dict[str, Any]:
        """Create an adjusted proposal based on previous negotiation rounds."""
        # Get previous proposals
        previous_proposals = []
        for round_data in delegation_plan.get("negotiation_rounds", []):
            for negotiation in round_data.get("negotiations", []):
                if negotiation["agent"] == agent:
                    previous_proposals.append(negotiation["proposal"])

        base_proposal = (
            previous_proposals[-1]
            if previous_proposals
            else self._create_agent_proposal(
                agent,
                delegation_plan["main_task"],
                delegation_plan["collaboration_prompt"],
            )
        )

        # Make adjustments based on round
        if round_num == 2:
            # Add coordination elements
            base_proposal[
                "contribution"
            ] += " | Will coordinate interface definitions with team"
            base_proposal["collaboration_notes"] = (
                "Sharing interfaces early and requesting code reviews"
            )
        elif round_num == 3:
            # Final adjustments
            base_proposal[
                "contribution"
            ] += " | Ready for final coordination and integration"
            base_proposal["collaboration_notes"] = (
                "Finalized approach, ready to begin development"
            )

        return base_proposal

    def _check_consensus(self, negotiations: List[Dict[str, Any]]) -> bool:
        """Check if agents have reached consensus (simplified logic)."""
        # Simple consensus: each agent has non-overlapping focus areas
        focus_areas = set()
        for negotiation in negotiations:
            agent_focus = negotiation["proposal"]["focus_areas"]
            for area in agent_focus:
                if area in focus_areas:
                    return False  # Overlap found
                focus_areas.add(area)

        return len(focus_areas) >= len(negotiations)  # Each agent has unique focus
