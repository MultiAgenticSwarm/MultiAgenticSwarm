"""
Enhanced collaborative system with universal agent capabilities and centralized progress tracking.
"""

import asyncio
import os
import subprocess
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from .system import System
from .agent import Agent
from .delegation import SimpleDelegator, DelegationStrategy
from ..tools.collaboration_tools import create_progress_board_tool
from ..utils.logger import get_logger

logger = get_logger(__name__)


class UniversalAgent(Agent):
    """
    Enhanced agent with universal collaboration capabilities.

    All agents have the same collaboration features:
    - Progress tracking and reporting
    - Project analysis capabilities
    - Team coordination through progress board
    - Collaboration prompt awareness
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        system_prompt: str = "",
        llm_provider: str = "anthropic",  # Default to Anthropic
        llm_model: str = "claude-3-5-sonnet-20241022",  # Use latest Claude model
        llm_config: Optional[Dict[str, Any]] = None,
        max_iterations: int = 10,
        memory_enabled: bool = True,
        agent_id: Optional[str] = None,
        progress_board=None,
        collaboration_prompt: str = ""
    ):
        """
        Initialize universal agent with collaboration capabilities.

        Args:
            progress_board: ProgressBoard tool for collaboration
            collaboration_prompt: Collaboration instructions for the agent
            (other args same as base Agent)
        """
        # Enhance system prompt with collaboration instructions
        enhanced_prompt = self._create_enhanced_system_prompt(system_prompt, description, collaboration_prompt)

        super().__init__(
            name=name,
            description=description,
            system_prompt=enhanced_prompt,
            llm_provider=llm_provider,
            llm_model=llm_model,
            llm_config=llm_config,
            max_iterations=max_iterations,
            memory_enabled=memory_enabled,
            agent_id=agent_id
        )

        # Collaboration state
        self.progress_board = progress_board
        self.current_task = None
        self.task_progress = 0
        self.collaboration_prompt = collaboration_prompt
        self.team_members = []

        logger.info(f"Created UniversalAgent '{name}' with collaboration capabilities")

    def _create_enhanced_system_prompt(self, original_prompt: str, description: str, collaboration_prompt: str = "") -> str:
        """Create enhanced system prompt with collaboration instructions."""
        collaboration_instructions = f"""

COLLABORATION CAPABILITIES:
You are a collaborative agent with access to these universal capabilities:

COLLABORATION PROMPT:
{collaboration_prompt}

PROGRESS TRACKING:
- Use report_progress(task, percentage, details) to report your current task progress
- Post status updates with post_update() to keep team informed
- Track time estimates and actual time spent on tasks

PROJECT ANALYSIS:
- Analyze current project state and identify what needs to be done next
- Assess dependencies between tasks and evaluate overall project health
- Read and interpret collaboration prompts to understand your role

TEAM COORDINATION:
- Read updates from other agents with read_updates()
- Share insights and coordinate work with coordinate_with_team()
- Request help when needed with request_help()
- Respond to help requests from team members
- Follow collaboration instructions from the project configuration

CODE COLLABORATION:
- Share interface definitions early with share_interface()
- Share code snippets with share_code_snippet()
- Review each other's code and provide feedback
- Coordinate on shared dependencies

COMMUNICATION RULES:
- All communication happens through the progress board (no direct agent-to-agent messaging)
- Post meaningful status updates regularly
- Be responsive to help requests
- Share knowledge and collaborate actively
- Follow the collaboration prompt guidelines for your role

Always read the collaboration prompt at the start of any task to understand:
1. Your specific role and responsibilities
2. How to coordinate with other agents
3. The collaboration style to follow
4. Dependencies and sequencing requirements

Remember: You're part of a team working toward a common goal. Collaborate actively and help your teammates succeed.
"""

        return f"{original_prompt}\n{collaboration_instructions}"

    def set_progress_board(self, progress_board):
        """Set the progress board for collaboration."""
        self.progress_board = progress_board

    def set_team_members(self, team_members: List[str]):
        """Set list of team member agent names."""
        self.team_members = [member for member in team_members if member != self.name]

    async def report_progress(
        self,
        task: str,
        percentage: int,
        details: str,
        estimated_completion: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Report task progress to the team.

        Args:
            task: Task name
            percentage: Progress percentage (0-100)
            details: Progress details
            estimated_completion: Estimated completion time

        Returns:
            Progress report result
        """
        self.current_task = task
        self.task_progress = percentage

        if self.progress_board:
            return self.progress_board.report_progress(
                agent_name=self.name,
                task=task,
                percentage=percentage,
                details=details,
                estimated_completion=estimated_completion
            )
        else:
            logger.warning(f"Agent {self.name}: No progress board available for reporting")
            return {"success": False, "error": "No progress board available"}

    async def analyze_project_state(self) -> Dict[str, Any]:
        """
        Analyze current project state and collaboration context.

        Returns:
            Project analysis including collaboration prompt and team status
        """
        if not self.progress_board:
            return {"error": "No progress board available for analysis"}

        # Get project status and collaboration prompt
        project_status = self.progress_board.get_project_status()
        prompt_info = self.progress_board.get_collaboration_prompt()
        recent_activity = self.progress_board.get_recent_activity(hours=24)

        # Analyze team activity
        team_analysis = {
            "total_agents": project_status["total_agents"],
            "active_agents": len(project_status["active_agents"]),
            "recent_updates": len(recent_activity["recent_updates"]),
            "overall_progress": project_status["overall_progress"],
            "collaboration_prompt_available": prompt_info["has_prompt"]
        }

        # Get my current context
        my_status = {
            "current_task": self.current_task,
            "task_progress": self.task_progress,
            "role_from_prompt": None
        }

        # Parse role from collaboration prompt
        if prompt_info["has_prompt"]:
            collaboration_prompt = prompt_info["collaboration_prompt"]
            self.collaboration_prompt = collaboration_prompt
            my_status["role_from_prompt"] = self._parse_my_role(collaboration_prompt)

        return {
            "project_status": project_status,
            "team_analysis": team_analysis,
            "my_status": my_status,
            "collaboration_prompt": prompt_info["collaboration_prompt"],
            "recent_activity": recent_activity["agent_activity"],
            "needs_attention": self._identify_needs_attention(project_status, recent_activity)
        }

    def _parse_my_role(self, collaboration_prompt: str) -> Optional[str]:
        """Parse my role from the collaboration prompt."""
        if not collaboration_prompt:
            return None

        lines = collaboration_prompt.split('\n')
        for line in lines:
            if self.name.lower() in line.lower() or any(keyword in self.name.lower() for keyword in ["ui", "audio", "data"]):
                # Extract role description
                if ":" in line:
                    return line.split(":", 1)[1].strip()
                elif any(verb in line.lower() for verb in ["focuses", "handles", "manages", "responsible"]):
                    return line.strip()

        # Fallback: parse based on agent name
        if "ui" in self.name.lower():
            return "UI/UX and app navigation development"
        elif "audio" in self.name.lower():
            return "Audio playback and music features"
        elif "data" in self.name.lower():
            return "Data models and state management"
        else:
            return "General development support"

    def _identify_needs_attention(
        self,
        project_status: Dict[str, Any],
        recent_activity: Dict[str, Any]
    ) -> List[str]:
        """Identify items that need attention."""
        needs_attention = []

        # Check for stalled progress
        if project_status["overall_progress"] < 10:
            needs_attention.append("Project progress is very low - may need task breakdown")

        # Check for inactive agents
        active_agents = set(project_status["active_agents"])
        all_agents = recent_activity.get("agent_activity", {}).keys()
        if len(active_agents) < len(all_agents) * 0.5:
            needs_attention.append("Some agents appear inactive - may need coordination")

        # Check for help requests
        if any("help_request" in str(activity) for activity in recent_activity.get("recent_updates", [])):
            needs_attention.append("There are pending help requests")

        return needs_attention

    async def coordinate_with_team(
        self,
        message: str,
        coordination_type: str = "general",
        target_agents: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Coordinate with team members through progress board.

        Args:
            message: Coordination message
            coordination_type: Type of coordination
            target_agents: Specific agents to coordinate with

        Returns:
            Coordination result
        """
        if self.progress_board:
            return self.progress_board.coordinate_with_team(
                agent_name=self.name,
                message=message,
                coordination_type=coordination_type,
                target_agents=target_agents
            )
        else:
            logger.warning(f"Agent {self.name}: No progress board available for coordination")
            return {"success": False, "error": "No progress board available"}

    async def request_help(
        self,
        topic: str,
        details: str,
        target_agent: Optional[str] = None,
        priority: str = "normal"
    ) -> Dict[str, Any]:
        """
        Request help from team members.

        Args:
            topic: Help topic
            details: Detailed description
            target_agent: Specific agent to ask for help
            priority: Priority level

        Returns:
            Help request result
        """
        if self.progress_board:
            return self.progress_board.request_help(
                agent_name=self.name,
                topic=topic,
                details=details,
                target_agent=target_agent,
                priority=priority
            )
        else:
            logger.warning(f"Agent {self.name}: No progress board available for help request")
            return {"success": False, "error": "No progress board available"}

    async def respond_to_help(
        self,
        help_request_id: str,
        response: str,
        code_snippet: Optional[str] = None,
        additional_resources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Respond to a help request from another agent.

        Args:
            help_request_id: ID of the help request to respond to
            response: Response message
            code_snippet: Optional code snippet to help
            additional_resources: Optional list of additional resources

        Returns:
            Response result
        """
        if self.progress_board:
            return self.progress_board.respond_to_help(
                agent_name=self.name,
                request_id=int(help_request_id),
                response=response,
                code_provided=code_snippet is not None
            )
        else:
            logger.warning(f"Agent {self.name}: No progress board available for help response")
            return {"success": False, "error": "No progress board available"}

    async def read_collaboration_prompt(self) -> Dict[str, Any]:
        """
        Read and interpret the current collaboration prompt.

        Returns:
            Collaboration prompt and role interpretation
        """
        if not self.progress_board:
            return {"error": "No progress board available"}

        prompt_info = self.progress_board.get_collaboration_prompt()

        if prompt_info["has_prompt"]:
            collaboration_prompt = prompt_info["collaboration_prompt"]
            my_role = self._parse_my_role(collaboration_prompt)

            return {
                "collaboration_prompt": collaboration_prompt,
                "my_role": my_role,
                "project_name": prompt_info["project_name"],
                "instructions_available": True
            }
        else:
            return {
                "collaboration_prompt": None,
                "my_role": None,
                "project_name": prompt_info["project_name"],
                "instructions_available": False,
                "message": "No collaboration prompt set for this project"
            }

    async def share_code_interface(
        self,
        interface_name: str,
        methods: List[str],
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Share a code interface definition with the team.

        Args:
            interface_name: Name of the interface
            methods: List of method signatures
            description: Interface description

        Returns:
            Interface sharing result
        """
        if self.progress_board:
            return self.progress_board.share_interface(
                agent_name=self.name,
                interface_name=interface_name,
                methods=methods,
                description=description
            )
        else:
            logger.warning(f"Agent {self.name}: No progress board available for interface sharing")
            return {"success": False, "error": "No progress board available"}

    async def share_code_snippet(
        self,
        snippet: str,
        description: str,
        language: str = "dart",
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Share a code snippet with the team.

        Args:
            snippet: Code snippet
            description: Description of the code
            language: Programming language
            file_path: File path where code belongs

        Returns:
            Code sharing result
        """
        if self.progress_board:
            return self.progress_board.share_code_snippet(
                agent_name=self.name,
                snippet=snippet,
                description=description,
                language=language,
                file_path=file_path
            )
        else:
            logger.warning(f"Agent {self.name}: No progress board available for code sharing")
            return {"success": False, "error": "No progress board available"}

    async def get_team_updates(
        self,
        hours: int = 24,
        agent_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get recent updates from team members.

        Args:
            hours: Hours to look back
            agent_filter: Specific agent to get updates from

        Returns:
            Team updates
        """
        if self.progress_board:
            # Get recent activity
            activity = self.progress_board.get_recent_activity(hours=hours)

            # Filter by agent if specified
            if agent_filter:
                filtered_activity = {
                    agent_filter: activity["agent_activity"].get(agent_filter, [])
                }
                activity["agent_activity"] = filtered_activity

            return activity
        else:
            logger.warning(f"Agent {self.name}: No progress board available for team updates")
            return {"error": "No progress board available"}

    async def get_project_status(self) -> Dict[str, Any]:
        """Get current project status from progress board."""
        if self.progress_board:
            return self.progress_board.get_project_status()
        else:
            return {
                "overall_progress": 0,
                "active_agents": [],
                "total_agents": len(self.universal_agents),
                "recent_updates": []
            }


class CollaborativeSystem(System):
    """
    Enhanced system with collaboration prompt support and unified agent capabilities.

    Features:
    - ProgressBoard integration for centralized communication
    - Collaboration prompt management
    - Universal agent capabilities
    - Delegation strategy coordination
    """

    def __init__(
        self,
        collaboration_prompt: Optional[str] = None,
        workspace_dir: str = ".",
        config_path: Optional[str] = None,
        enable_logging: bool = True,
        verbose: bool = False
    ):
        """
        Initialize collaborative system.

        Args:
            collaboration_prompt: Initial collaboration instructions
            workspace_dir: Directory for progress board and project files
            config_path: Configuration file path
            enable_logging: Enable logging
            verbose: Verbose logging
        """
        super().__init__(config_path=config_path, enable_logging=enable_logging, verbose=verbose)

        # Create progress board
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(exist_ok=True)

        self.progress_board = create_progress_board_tool(
            board_file="progress_board.json",
            workspace_dir=str(self.workspace_dir)
        )

        # Register progress board as global tool
        self.register_tool(self.progress_board)

        # Set initial collaboration prompt
        self.collaboration_prompt = collaboration_prompt or ""
        if collaboration_prompt:
            self.set_collaboration_prompt(collaboration_prompt)

        # Initialize delegator (will be properly configured when needed)
        self.delegator = None

        # Track universal agents
        self.universal_agents: Dict[str, UniversalAgent] = {}

        logger.info(f"CollaborativeSystem initialized with workspace: {workspace_dir}")

    def set_collaboration_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Set the collaboration instructions for the project.

        Args:
            prompt: Collaboration prompt defining how agents should work together

        Returns:
            Success confirmation
        """
        return self.progress_board.set_collaboration_prompt(prompt)

    def get_collaboration_prompt(self) -> Dict[str, Any]:
        """Get the current collaboration prompt."""
        return self.progress_board.get_collaboration_prompt()

    def add_agent(self, agent: Union[Agent, UniversalAgent]) -> None:
        """
        Add an agent to the collaborative system.

        Args:
            agent: Agent to add (will be enhanced if not already UniversalAgent)
        """
        if isinstance(agent, UniversalAgent):
            universal_agent = agent
        else:
            # Convert regular agent to UniversalAgent
            universal_agent = UniversalAgent(
                name=agent.name,
                description=agent.description,
                system_prompt=agent.system_prompt,
                llm_provider=agent.llm_provider_name,
                llm_model=agent.llm_model,
                llm_config=agent.llm_config,
                max_iterations=agent.max_iterations,
                memory_enabled=agent.memory_enabled,
                agent_id=agent.id
            )

        # Set up collaboration tools
        universal_agent.set_progress_board(self.progress_board)

        # Register with system
        self.register_agent(universal_agent)
        self.universal_agents[universal_agent.name] = universal_agent

        # Update team member lists for all agents
        agent_names = list(self.universal_agents.keys())
        for agent_name, universal_agent_ref in self.universal_agents.items():
            universal_agent_ref.set_team_members(agent_names)

        logger.info(f"Added UniversalAgent '{universal_agent.name}' to collaborative system")

    def add_agents(self, agents: List[Union[Agent, UniversalAgent]]) -> None:
        """Add multiple agents to the system."""
        for agent in agents:
            self.add_agent(agent)

    async def execute_collaborative_task(
        self,
        task: str,
        delegation_strategy: Union[str, DelegationStrategy] = DelegationStrategy.COLLABORATIVE,
        lead_agent: Optional[str] = None,
        collaboration_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a collaborative task using specified delegation strategy.

        Args:
            task: Main task description
            delegation_strategy: How to delegate the task
            lead_agent: Lead agent for hierarchical delegation
            collaboration_prompt: Collaboration instructions (optional override)

        Returns:
            Task execution results
        """
        # Convert string to enum if needed
        if isinstance(delegation_strategy, str):
            delegation_strategy = DelegationStrategy(delegation_strategy.lower())

        # Set collaboration prompt if provided
        if collaboration_prompt:
            self.set_collaboration_prompt(collaboration_prompt)

        # Get agent list
        agent_names = list(self.universal_agents.keys())

        if not agent_names:
            raise ValueError("No agents available for collaborative task execution")

        logger.info(f"Starting collaborative task: {task[:100]}...")
        logger.info(f"Using {delegation_strategy} delegation with {len(agent_names)} agents")

        # Create delegator if not already created
        if self.delegator is None:
            current_prompt = self.get_collaboration_prompt().get("collaboration_prompt", "")
            self.delegator = SimpleDelegator(
                strategy=delegation_strategy,
                collaboration_prompt=current_prompt,
                progress_board=self.progress_board
            )

        # Delegate the task
        delegation_result = await self.delegator.delegate_task(
            main_task=task,
            agents=agent_names,
            strategy=delegation_strategy,
            lead_agent=lead_agent
        )

        # Post task start to progress board
        self.progress_board.post_update(
            agent_name="CollaborativeSystem",
            message=f"Collaborative task started: {task[:50]}...",
            update_type="task_start",
            tags=["task", delegation_strategy.value]
        )

        logger.info(f"Task delegation completed using {delegation_strategy} strategy")
        return {
            "task": task,
            "delegation_strategy": delegation_strategy.value,
            "delegation_result": delegation_result,
            "participating_agents": agent_names,
            "status": "delegated"
        }

    async def delegate_tasks_from_prompt(
        self,
        main_task: str,
        collaboration_prompt: str
    ) -> Dict[str, Any]:
        """
        Delegate tasks based on collaboration prompt instructions.

        Analyzes the collaboration prompt to understand:
        - Agent roles and responsibilities
        - Development phases and sequencing
        - Coordination requirements

        Args:
            main_task: Main task description
            collaboration_prompt: Collaboration instructions defining roles and phases

        Returns:
            Task delegation structure with phases and agent assignments
        """
        logger.info("Delegating tasks based on collaboration prompt")

        # Store the collaboration prompt
        self.set_collaboration_prompt(collaboration_prompt)

        # Parse collaboration prompt to extract structure
        prompt_analysis = await self._analyze_collaboration_prompt(collaboration_prompt)

        # Create delegation structure
        delegation = {
            "strategy": "prompt-based",
            "main_task": main_task,
            "collaboration_prompt": collaboration_prompt,
            "agent_roles": prompt_analysis.get("agent_roles", {}),
            "phases": prompt_analysis.get("phases", []),
            "assignments": {},
            "coordination_rules": prompt_analysis.get("coordination_rules", [])
        }

        # Assign tasks to agents based on their roles in the prompt
        for agent_name, agent in self.universal_agents.items():
            role_info = prompt_analysis["agent_roles"].get(agent_name, {})
            agent_tasks = self._generate_agent_tasks(agent_name, role_info, main_task)
            delegation["assignments"][agent_name] = agent_tasks

        # Post delegation information to progress board
        self.progress_board.post_update(
            agent_name="CollaborativeSystem",
            message=f"Task delegation completed based on collaboration prompt",
            task="task_delegation",
            progress=100,
            update_type="coordination",
            tags=["delegation", "prompt-based", f"phases:{len(delegation['phases'])}", f"agents:{len(delegation['assignments'])}"]
        )

        return delegation

    async def _analyze_collaboration_prompt(self, collaboration_prompt: str) -> Dict[str, Any]:
        """
        Analyze collaboration prompt to extract roles, phases, and rules.

        Args:
            collaboration_prompt: The collaboration instructions

        Returns:
            Structured analysis of the prompt
        """
        # Extract agent roles from prompt
        agent_roles = {}
        phases = []
        coordination_rules = []

        # Parse the prompt text to identify agent responsibilities
        lines = collaboration_prompt.strip().split('\n')
        current_section = None
        current_phase = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Look for agent definitions
            for agent_name in self.universal_agents.keys():
                if agent_name in line and ("focuses" in line or "handles" in line or "manages" in line or "responsible" in line):
                    # Extract role description
                    role_desc = line.split(agent_name)[-1].strip()
                    if role_desc.startswith(("focuses", "handles", "manages")):
                        agent_roles[agent_name] = {
                            "description": role_desc,
                            "responsibilities": [],
                            "primary_focus": self._extract_primary_focus(role_desc)
                        }

            # Look for development phases
            if "phase" in line.lower() or line.strip().endswith(":"):
                if any(keyword in line.lower() for keyword in ["setup", "development", "integration", "testing", "polish"]):
                    phase_info = {
                        "name": line.rstrip(":"),
                        "type": "sequential",  # Default
                        "agents": list(self.universal_agents.keys()),
                        "description": line
                    }
                    phases.append(phase_info)
                    current_phase = phase_info

            # Look for coordination rules
            if line.startswith(("-", "•", "*")) and any(keyword in line.lower() for keyword in ["share", "review", "coordinate", "help", "communicate"]):
                coordination_rules.append(line.lstrip("-•* "))

        # If no explicit phases found, create default phases based on agent roles
        if not phases:
            phases = self._create_default_phases(agent_roles)

        return {
            "agent_roles": agent_roles,
            "phases": phases,
            "coordination_rules": coordination_rules
        }

    def _extract_primary_focus(self, role_description: str) -> str:
        """Extract primary focus area from role description."""
        focus_keywords = {
            "ui": ["ui", "user interface", "design", "screens", "widgets"],
            "audio": ["audio", "music", "playback", "streaming", "sound"],
            "data": ["data", "models", "state", "storage", "database", "persistence"]
        }

        role_lower = role_description.lower()
        for focus, keywords in focus_keywords.items():
            if any(keyword in role_lower for keyword in keywords):
                return focus

        return "general"

    def _create_default_phases(self, agent_roles: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create default development phases based on agent roles."""
        phases = []

        # Phase 1: Architecture and Setup (Data first)
        data_agents = [name for name, role in agent_roles.items() if role.get("primary_focus") == "data"]
        if data_agents:
            phases.append({
                "name": "Phase 1: Data Architecture & Setup",
                "type": "sequential",
                "agents": data_agents,
                "description": "Setup data models, state management, and storage"
            })

        # Phase 2: Core Services (Audio/Backend)
        service_agents = [name for name, role in agent_roles.items() if role.get("primary_focus") == "audio"]
        if service_agents:
            phases.append({
                "name": "Phase 2: Core Services & Audio",
                "type": "sequential",
                "agents": service_agents,
                "description": "Implement core services and audio functionality"
            })

        # Phase 3: User Interface
        ui_agents = [name for name, role in agent_roles.items() if role.get("primary_focus") == "ui"]
        if ui_agents:
            phases.append({
                "name": "Phase 3: User Interface",
                "type": "sequential",
                "agents": ui_agents,
                "description": "Build user interface and navigation"
            })

        # Phase 4: Integration (All agents)
        phases.append({
            "name": "Phase 4: Integration & Testing",
            "type": "collaborative",
            "agents": list(agent_roles.keys()),
            "description": "Integrate components and test the complete application"
        })

        return phases

    def _generate_agent_tasks(self, agent_name: str, role_info: Dict[str, Any], main_task: str) -> List[str]:
        """Generate specific tasks for an agent based on their role."""
        primary_focus = role_info.get("primary_focus", "general")

        task_templates = {
            "ui": [
                "Implement Material Design 3 theme and styling",
                "Create main navigation and routing system",
                "Build home screen with playlist grid",
                "Design player screen with controls",
                "Create search screen with filtering",
                "Implement responsive layout components"
            ],
            "audio": [
                "Create core audio service for playback",
                "Implement streaming service for online music",
                "Build offline audio playback system",
                "Create audio player controls widget",
                "Implement playlist management audio logic",
                "Add audio state management and notifications"
            ],
            "data": [
                "Design and implement Track data model",
                "Create Playlist and User data models",
                "Setup state management with Provider/Riverpod",
                "Implement local storage with Hive/SQLite",
                "Create API integration layer",
                "Build user preferences and settings management"
            ]
        }

        return task_templates.get(primary_focus, [
            f"Contribute to {main_task} based on collaboration prompt",
            "Coordinate with team members",
            "Review and integrate with other components"
        ])

    async def execute_collaboration_phase(
        self,
        phase: Dict[str, Any],
        main_task: str
    ) -> Dict[str, Any]:
        """
        Execute a specific collaboration phase.

        Args:
            phase: Phase definition with name, type, agents, and description
            main_task: Main task context

        Returns:
            Phase execution results for each agent
        """
        phase_name = phase.get("name", "Unknown Phase")
        phase_type = phase.get("type", "sequential")
        phase_agents = phase.get("agents", [])
        phase_description = phase.get("description", "")

        logger.info(f"Executing collaboration phase: {phase_name}")

        # Post phase start to progress board
        self.progress_board.post_update(
            agent_name="CollaborativeSystem",
            message=f"Starting {phase_name}",
            task=phase_name.lower().replace(" ", "_"),
            progress=0,
            update_type="phase_start",
            tags=["collaboration", phase_type, f"agents:{len(phase_agents)}"]
        )

        results = {}

        # Execute based on phase type
        if phase_type == "sequential":
            # Execute agents one by one
            for agent_name in phase_agents:
                if agent_name in self.universal_agents:
                    agent = self.universal_agents[agent_name]
                    result = await self._execute_agent_phase_work(agent, phase, main_task)
                    results[agent_name] = result

        elif phase_type == "parallel":
            # Execute all agents simultaneously
            tasks = []
            for agent_name in phase_agents:
                if agent_name in self.universal_agents:
                    agent = self.universal_agents[agent_name]
                    tasks.append(self._execute_agent_phase_work(agent, phase, main_task))

            # Wait for all to complete
            if tasks:
                agent_results = await asyncio.gather(*tasks, return_exceptions=True)
                for i, agent_name in enumerate(phase_agents):
                    if i < len(agent_results):
                        results[agent_name] = agent_results[i]

        elif phase_type == "collaborative":
            # All agents work together with coordination
            results = await self._execute_collaborative_phase_work(phase_agents, phase, main_task)

        # Post phase completion
        self.progress_board.post_update(
            agent_name="CollaborativeSystem",
            message=f"Completed {phase_name}",
            task=phase_name.lower().replace(" ", "_"),
            progress=100,
            update_type="phase_complete",
            tags=["collaboration", "completed", f"deliverables:{sum(len(result.get('deliverables', [])) for result in results.values())}"]
        )

        return results

    async def _execute_agent_phase_work(
        self,
        agent: UniversalAgent,
        phase: Dict[str, Any],
        main_task: str
    ) -> Dict[str, Any]:
        """
        Execute an agent's work for a specific phase.

        Args:
            agent: Agent to execute
            phase: Phase definition
            main_task: Main task context

        Returns:
            Agent's work result
        """
        # This would contain the actual agent execution logic
        # For now, return a simulation of the agent's work

        phase_name = phase.get("name", "Unknown Phase")
        agent_focus = getattr(agent, "primary_focus", "general")

        # Simulate agent work based on their focus and the phase
        deliverables = []

        if "data" in phase_name.lower() and agent_focus == "data":
            deliverables = ["Track.dart", "Playlist.dart", "UserPreferences.dart", "AppState.dart"]
        elif "audio" in phase_name.lower() and agent_focus == "audio":
            deliverables = ["AudioService.dart", "StreamingService.dart", "PlayerControls.dart"]
        elif "ui" in phase_name.lower() and agent_focus == "ui":
            deliverables = ["HomeScreen.dart", "PlayerScreen.dart", "SearchScreen.dart", "AppTheme.dart"]
        elif "integration" in phase_name.lower():
            deliverables = ["Integration tests", "Code reviews", "Bug fixes"]

        # Report progress
        await agent.report_progress(
            task=phase_name,
            percentage=100,
            details=f"Completed {len(deliverables)} deliverables for {phase_name}"
        )

        return {
            "status": "completed",
            "deliverables": deliverables,
            "agent": agent.name,
            "phase": phase_name
        }

    async def _execute_collaborative_phase_work(
        self,
        agent_names: List[str],
        phase: Dict[str, Any],
        main_task: str
    ) -> Dict[str, Any]:
        """Execute collaborative work where all agents work together."""
        results = {}

        # All agents coordinate and work together
        for agent_name in agent_names:
            if agent_name in self.universal_agents:
                agent = self.universal_agents[agent_name]
                result = await self._execute_agent_phase_work(agent, phase, main_task)
                results[agent_name] = result

        return results

    async def compile_deliverables(self) -> Dict[str, Any]:
        """
        Compile final deliverables from all agents and create actual Flutter project files.

        Returns:
            Compiled project deliverables
        """
        # Get all updates that contain code or deliverables
        updates_result = self.progress_board.read_updates(limit=1000)
        all_updates = updates_result.get("updates", [])

        # Organize by type
        deliverables = {
            "code_snippets": [],
            "interfaces": [],
            "documentation": [],
            "progress_reports": [],
            "project_structure": {},
            "files_created": []
        }

        # Extract code snippets
        for update in all_updates:
            if update.get("code_snippet"):
                deliverables["code_snippets"].append({
                    "agent": update.get("agent_name"),
                    "file_path": update.get("file_path"),
                    "code": update.get("code_snippet"),
                    "description": update.get("message"),
                    "language": update.get("language", "dart"),
                    "timestamp": update.get("timestamp")
                })

        # Get shared interfaces
        board_data = self.progress_board._load_board()
        deliverables["interfaces"] = list(board_data.get("interfaces", {}).values())

        # Get progress reports
        deliverables["progress_reports"] = board_data.get("progress_reports", [])

        # Generate project structure for Flutter app and CREATE ACTUAL FILES
        if any("flutter" in tag for update in all_updates for tag in update.get("tags", [])):
            deliverables["project_structure"] = self._generate_flutter_structure(deliverables)
            # Actually create the Flutter project files
            created_files = await self._create_flutter_project_files(deliverables["code_snippets"])
            deliverables["files_created"] = created_files

        return deliverables

    async def _create_flutter_project_files(self, code_snippets: List[Dict[str, Any]]) -> List[str]:
        """
        Create actual Flutter project files from the generated code snippets.

        Args:
            code_snippets: List of code snippets with file paths and content

        Returns:
            List of created file paths
        """
        created_files = []

        # Create Flutter project structure
        flutter_project_dir = self.workspace_dir / "flutter_music_app"
        flutter_project_dir.mkdir(exist_ok=True)

        # Create lib directory structure
        lib_dir = flutter_project_dir / "lib"
        lib_dir.mkdir(exist_ok=True)

        # Create subdirectories
        subdirs = ["models", "services", "screens", "widgets", "providers", "utils"]
        for subdir in subdirs:
            (lib_dir / subdir).mkdir(exist_ok=True)

        # Process each code snippet and create files
        for snippet in code_snippets:
            file_path = snippet.get("file_path")
            code_content = snippet.get("code")

            if not file_path or not code_content:
                continue

            # Determine full file path
            if file_path.startswith("lib/"):
                full_path = flutter_project_dir / file_path
            elif file_path == "pubspec.yaml":
                full_path = flutter_project_dir / file_path
            else:
                # Default to lib directory
                full_path = lib_dir / file_path

            # Ensure directory exists
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Write the file
            try:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(code_content)

                created_files.append(str(full_path))
                logger.info(f"Created Flutter file: {full_path}")

                # Also log to progress board
                self.progress_board.post_update(
                    agent_name="CollaborativeSystem",
                    message=f"Created file: {file_path}",
                    update_type="file_created",
                    file_path=str(full_path),
                    tags=["file_creation", "flutter"]
                )

            except Exception as e:
                logger.error(f"Error creating file {full_path}: {e}")

        # Create additional Flutter project files
        await self._create_additional_flutter_files(flutter_project_dir)

        return created_files

    async def _create_additional_flutter_files(self, project_dir: Path):
        """Create additional Flutter project files like README, .gitignore, etc."""

        # Create README.md
        readme_content = """# Flutter Music Streaming App

A beautiful music streaming application built with Flutter, generated by AI agents using MultiAgenticSwarm.

## Features

- 🎵 Audio playback with full controls
- 📱 Modern Material Design 3 UI
- 🎧 Playlist management
- 🔍 Search functionality
- ⚡ Offline mode support
- 🎨 Beautiful, responsive design

## Generated Components

This app was collaboratively built by three AI agents:

- **Flutter_UI_Agent**: Created all UI screens, navigation, and Material Design theme
- **Flutter_Audio_Agent**: Built audio services, streaming, and playback controls
- **Flutter_Data_Agent**: Designed data models, state management, and storage

## Getting Started

1. Ensure you have Flutter installed
2. Run `flutter pub get` to install dependencies
3. Run `flutter run` to start the app

## Architecture

- **State Management**: Provider pattern
- **Audio**: just_audio plugin
- **Storage**: Hive for local data
- **UI**: Material Design 3
- **Navigation**: GoRouter

## AI-Generated Code

All code in this project was generated by AI agents making real LLM calls to Anthropic Claude.
The agents collaborated through a centralized progress board to coordinate development.
"""

        try:
            with open(project_dir / "README.md", 'w', encoding='utf-8') as f:
                f.write(readme_content)
        except Exception as e:
            logger.error(f"Error creating README.md: {e}")

        # Create .gitignore
        gitignore_content = """# Flutter/Dart specific
.dart_tool/
.flutter-plugins
.flutter-plugins-dependencies
.packages
.pub-cache/
.pub/
build/
flutter_*.png

# Android
android/app/debug
android/app/profile
android/app/release

# iOS
ios/Runner.app.dSYM/
ios/Flutter/flutter_export_environment.sh

# Web
web/

# IDE
.vscode/
.idea/
*.iml
*.ipr
*.iws

# OS
.DS_Store
Thumbs.db

# Local storage
*.db
*.hive
*.box
"""

        try:
            with open(project_dir / ".gitignore", 'w', encoding='utf-8') as f:
                f.write(gitignore_content)
        except Exception as e:
            logger.error(f"Error creating .gitignore: {e}")

    def _generate_flutter_structure(self, deliverables: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Flutter project structure from deliverables."""
        structure = {
            "flutter_music_app/": {
                "lib/": {
                    "main.dart": "App entry point",
                    "screens/": {
                        "home_screen.dart": "Main music browser",
                        "player_screen.dart": "Now playing screen",
                        "playlist_screen.dart": "Playlist management",
                        "search_screen.dart": "Search interface"
                    },
                    "widgets/": {
                        "player_controls.dart": "Play/pause/skip controls",
                        "track_list_tile.dart": "Track display widget",
                        "mini_player.dart": "Bottom mini player"
                    },
                    "services/": {
                        "audio_service.dart": "Audio playback logic",
                        "streaming_service.dart": "Music streaming",
                        "offline_service.dart": "Offline playback"
                    },
                    "models/": {
                        "track.dart": "Track data model",
                        "playlist.dart": "Playlist model",
                        "user_preferences.dart": "User settings"
                    },
                    "providers/": {
                        "audio_provider.dart": "Audio state management",
                        "playlist_provider.dart": "Playlist state",
                        "user_provider.dart": "User data state"
                    },
                    "utils/": {
                        "constants.dart": "App constants",
                        "theme.dart": "Material Design 3 theme"
                    }
                },
                "pubspec.yaml": "Dependencies and project config",
                "README.md": "Project documentation"
            }
        }

        # Add file counts based on deliverables
        code_count = len(deliverables.get("code_snippets", []))
        interface_count = len(deliverables.get("interfaces", []))

        structure["summary"] = {
            "total_files": self._count_files_in_structure(structure["flutter_music_app/"]),
            "code_snippets_shared": code_count,
            "interfaces_defined": interface_count,
            "agents_contributed": len(set(
                snippet["agent"] for snippet in deliverables.get("code_snippets", [])
            ))
        }

        return structure

    def _count_files_in_structure(self, structure: Dict[str, Any]) -> int:
        """Count files in project structure."""
        count = 0
        for key, value in structure.items():
            if isinstance(value, dict):
                count += self._count_files_in_structure(value)
            else:
                count += 1
        return count

    async def create_flutter_project(self, project_name: str = "flutter_music_app") -> str:
        """
        Create and initialize a Flutter project structure.

        Args:
            project_name: Name of the Flutter project

        Returns:
            Path to the created Flutter project
        """
        project_path = self.workspace_dir / project_name

        logger.info(f"Creating Flutter project at {project_path}")

        # Create basic Flutter project structure
        await self._initialize_flutter_project(project_path)

        return str(project_path)

    async def _initialize_flutter_project(self, project_path: Path):
        """Initialize a basic Flutter project structure."""
        # Create directories
        lib_dir = project_path / "lib"
        lib_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        subdirs = ["models", "services", "screens", "widgets", "providers", "utils"]
        for subdir in subdirs:
            (lib_dir / subdir).mkdir(exist_ok=True)

        # Create basic pubspec.yaml
        pubspec_content = f"""name: {project_path.name}
description: A Flutter music streaming app built by AI agents.

publish_to: 'none'

version: 1.0.0+1

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
  provider: ^6.0.5
  just_audio: ^0.9.34
  cached_network_image: ^3.2.3
  hive: ^2.2.3
  hive_flutter: ^1.1.0
  path_provider: ^2.0.15
  http: ^1.1.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^2.0.0
  hive_generator: ^2.0.0
  build_runner: ^2.4.6

flutter:
  uses-material-design: true
"""

        try:
            with open(project_path / "pubspec.yaml", 'w') as f:
                f.write(pubspec_content)
            logger.info("Created pubspec.yaml")
        except Exception as e:
            logger.error(f"Error creating pubspec.yaml: {e}")

    async def write_code_to_files(self, progress_board_data: Dict[str, Any]) -> List[str]:
        """
        Write code snippets from progress board to actual Flutter files.

        Args:
            progress_board_data: Progress board data containing code snippets

        Returns:
            List of created file paths
        """
        created_files = []

        # Get code updates from progress board
        updates = progress_board_data.get("updates", [])
        code_updates = [u for u in updates if u.get("code_snippet")]

        logger.info(f"Found {len(code_updates)} code snippets to write to files")

        # Map messages to likely file paths
        file_mappings = {
            "Track data model": "lib/models/track.dart",
            "Playlist data model": "lib/models/playlist.dart",
            "User data model": "lib/models/user.dart",
            "UserPreferences data model": "lib/models/user_preferences.dart",
            "Provider-based state management": "lib/providers/app_providers.dart",
            "AudioProvider state management": "lib/providers/audio_provider.dart",
            "PlaylistProvider state management": "lib/providers/playlist_provider.dart",
            "data services": "lib/services/data_services.dart",
            "local storage system": "lib/services/storage_service.dart",
            "core audio service": "lib/services/audio_service.dart",
            "streaming service": "lib/services/streaming_service.dart",
            "player controls widget": "lib/widgets/player_controls.dart",
            "Material Design 3 theme": "lib/utils/theme.dart",
            "navigation system": "lib/utils/app_router.dart",
            "HomeScreen screen": "lib/screens/home_screen.dart",
            "PlayerScreen screen": "lib/screens/player_screen.dart",
            "SearchScreen screen": "lib/screens/search_screen.dart",
            "PlaylistScreen screen": "lib/screens/playlist_screen.dart",
            "Main application entry point": "lib/main.dart",
            "Complete pubspec.yaml": "pubspec.yaml"
        }

        project_dir = self.workspace_dir / "flutter_music_app"
        processed_files = set()

        def _validate_and_resolve_file_path(raw_path):
            """Validate and normalise file paths, enforce extensions, and prevent unsafe writes."""
            from pathlib import Path
            valid_exts = {".dart", ".yaml", ".json", ".md"}
            path = Path(raw_path)

            # Prevent absolute or traversal
            if path.is_absolute() or ".." in path.parts:
                raise ValueError(f"Unsafe path: {raw_path}")

            # Ensure path is inside project_dir
            full_path = (project_dir / path).resolve()
            if project_dir not in full_path.parents and project_dir != full_path.parent:
                raise ValueError(f"Path outside project: {raw_path}")

            # Add/adjust extension
            if full_path.suffix.lower() not in valid_exts:
                if "pubspec" in full_path.name.lower():
                    full_path = full_path.with_suffix(".yaml")
                elif "lib" in full_path.parts:
                    full_path = full_path.with_suffix(".dart")
                else:
                    full_path = full_path.with_suffix(".dart")

            return full_path

        for update in code_updates:
            message = update.get('message', '')
            code_snippet = update.get('code_snippet', '')

            if not code_snippet or not message:
                continue

            # Find matching file path
            file_path = None
            for key, path in file_mappings.items():
                if key.lower() in message.lower():
                    try:
                        file_path = _validate_and_resolve_file_path(path)
                    except ValueError as e:
                        logger.error(str(e))
                        continue
                    break

            if not file_path:
                # Try to extract from file_path field if available
                if update.get('file_path'):
                    try:
                        file_path = _validate_and_resolve_file_path(update['file_path'].replace('lib/', ''))
                    except ValueError as e:
                        logger.error(str(e))
                        continue
                else:
                    logger.warning(f"Could not map message to file: {message}")
                    continue

            # Skip if we already processed this file
            if str(file_path) in processed_files:
                continue

            try:
                # Create directory if needed
                file_path.parent.mkdir(parents=True, exist_ok=True)

                # Atomic write
                tmp_path = file_path.with_suffix(file_path.suffix + ".tmp")
                with open(tmp_path, 'w', encoding='utf-8') as f:
                    f.write(code_snippet)
                tmp_path.replace(file_path)

                created_files.append(str(file_path))
                processed_files.add(str(file_path))
                logger.info(f"Created file: {file_path}")

            except Exception as e:
                logger.error(f"Error writing to {file_path}: {e}")

        return created_files


    async def execute_flutter_development(
        self,
        task: str,
        delegation_strategy: str = "collaborative"
    ) -> Dict[str, Any]:
        """
        Execute collaborative Flutter development task.

        Args:
            task: Main development task description
            delegation_strategy: Strategy for task delegation

        Returns:
            Development results with created files
        """
        logger.info(f"Starting Flutter development with {len(self.agents)} agents")

        # Create Flutter project structure
        project_path = await self.create_flutter_project()
        logger.info(f"Flutter project created at: {project_path}")

        # Execute collaborative task
        results = await self.execute_collaborative_task(task, delegation_strategy)

        # Write generated code to actual Flutter files
        progress_data = self.progress_board.get_board_data()
        created_files = await self.write_code_to_files(progress_data)

        # Update results with file creation info
        results["flutter_project_path"] = project_path
        results["created_files"] = created_files
        results["total_files_created"] = len(created_files)

        logger.info(f"Flutter development completed. Created {len(created_files)} files.")

        return results
