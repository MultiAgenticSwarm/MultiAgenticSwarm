"""
Collaboration tools for multi-agent systems.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from ..core.tool import Tool
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ProgressBoard(Tool):
    """
    Centralized communication board for multi-agent collaboration.

    All agent communication happens through this shared progress file.
    Supports collaboration prompts and structured progress tracking.
    """

    def __init__(self, board_file: str = "progress_board.json", workspace_dir: str = "."):
        """
        Initialize the progress board.

        Args:
            board_file: Name of the progress board file
            workspace_dir: Directory to store the progress board
        """
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(exist_ok=True)
        self.board_file = self.workspace_dir / board_file

        self.collaboration_prompt = None
        self._ensure_board_exists()

        # Initialize the tool with multiple functions
        super().__init__(
            name="ProgressBoard",
            description="Centralized communication board for agent collaboration"
        )

        # Add sub-functions as tool methods
        self._register_functions()

    def _register_functions(self):
        """Register all board functions as callable methods."""
        self.functions = {
            "post_update": self.post_update,
            "read_updates": self.read_updates,
            "get_project_status": self.get_project_status,
            "share_interface": self.share_interface,
            "request_help": self.request_help,
            "respond_to_help": self.respond_to_help,
            "set_collaboration_prompt": self.set_collaboration_prompt,
            "get_collaboration_prompt": self.get_collaboration_prompt,
            "report_progress": self.report_progress,
            "coordinate_with_team": self.coordinate_with_team,
            "share_code_snippet": self.share_code_snippet,
            "get_recent_activity": self.get_recent_activity
        }

    def _ensure_board_exists(self):
        """Ensure the progress board file exists with initial structure."""
        if not self.board_file.exists():
            initial_board = {
                "project": {
                    "name": "New Project",
                    "created_at": datetime.now().isoformat(),
                    "collaboration_prompt": None
                },
                "agents": {},
                "updates": [],
                "interfaces": {},
                "help_requests": [],
                "progress_reports": [],
                "last_updated": datetime.now().isoformat()
            }
            self._save_board(initial_board)

    def _load_board(self) -> Dict[str, Any]:
        """Load the current progress board state."""
        try:
            with open(self.board_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading progress board: {e}")
            return self._get_default_board()

    def _save_board(self, board_data: Dict[str, Any]):
        """Save the progress board state."""
        try:
            board_data["last_updated"] = datetime.now().isoformat()
            with open(self.board_file, 'w', encoding='utf-8') as f:
                json.dump(board_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving progress board: {e}")

    def _get_default_board(self) -> Dict[str, Any]:
        """Get default board structure."""
        return {
            "project": {"name": "Default Project", "collaboration_prompt": None},
            "agents": {},
            "updates": [],
            "interfaces": {},
            "help_requests": [],
            "progress_reports": [],
            "last_updated": datetime.now().isoformat()
        }

    def set_collaboration_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Store the collaboration instructions for the project.

        Args:
            prompt: Collaboration prompt defining how agents should work together

        Returns:
            Success confirmation
        """
        board = self._load_board()
        board["project"]["collaboration_prompt"] = prompt
        self._save_board(board)

        logger.info("Collaboration prompt updated")
        return {
            "success": True,
            "message": "Collaboration prompt set successfully",
            "prompt_length": len(prompt)
        }

    def get_collaboration_prompt(self) -> Dict[str, Any]:
        """
        Retrieve the current collaboration prompt.

        Returns:
            Collaboration prompt and related info
        """
        board = self._load_board()
        prompt = board["project"].get("collaboration_prompt")

        return {
            "collaboration_prompt": prompt,
            "has_prompt": prompt is not None,
            "project_name": board["project"].get("name", "Unknown")
        }

    def post_update(
        self,
        agent_name: str,
        message: str,
        task: Optional[str] = None,
        progress: Optional[int] = None,
        update_type: str = "status_update",
        code_snippet: Optional[str] = None,
        file_path: Optional[str] = None,
        language: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Post an update to the progress board.

        Args:
            agent_name: Name of the agent posting the update
            message: Status message or information
            task: Current task being worked on
            progress: Progress percentage (0-100)
            update_type: Type of update (status_update, coordination, interface_sharing, etc.)
            code_snippet: Code snippet to share
            file_path: File path for the code snippet
            language: Programming language of the code
            tags: Tags for categorization

        Returns:
            Confirmation of update posting
        """
        board = self._load_board()

        # Initialize agent if not exists
        if agent_name not in board["agents"]:
            board["agents"][agent_name] = {
                "name": agent_name,
                "first_seen": datetime.now().isoformat(),
                "last_active": datetime.now().isoformat(),
                "total_updates": 0,
                "current_task": None,
                "progress": 0
            }

        # Create update entry
        update = {
            "id": len(board["updates"]) + 1,
            "agent": agent_name,
            "agent_name": agent_name,  # For compatibility
            "timestamp": datetime.now().isoformat(),
            "type": update_type,
            "message": message,
            "task": task,
            "progress": progress,
            "code_snippet": code_snippet,
            "file_path": file_path,
            "language": language,
            "tags": tags or []
        }

        # Add to updates
        board["updates"].append(update)

        # Update agent info
        agent_info = board["agents"][agent_name]
        agent_info["last_active"] = datetime.now().isoformat()
        agent_info["total_updates"] += 1
        if task:
            agent_info["current_task"] = task
        if progress is not None:
            agent_info["progress"] = progress

        self._save_board(board)

        logger.info(f"Posted update from {agent_name}: {message[:50]}...")
        return {
            "success": True,
            "update_id": update["id"],
            "timestamp": update["timestamp"]
        }

    def read_updates(
        self,
        since_timestamp: Optional[str] = None,
        agent_filter: Optional[str] = None,
        type_filter: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Read updates from the progress board.

        Args:
            since_timestamp: Only return updates after this timestamp
            agent_filter: Only return updates from this agent
            type_filter: Only return updates of this type
            limit: Maximum number of updates to return

        Returns:
            List of matching updates
        """
        board = self._load_board()
        updates = board["updates"]

        # Apply filters
        if since_timestamp:
            updates = [u for u in updates if u["timestamp"] > since_timestamp]

        if agent_filter:
            updates = [u for u in updates if u["agent"] == agent_filter]

        if type_filter:
            updates = [u for u in updates if u["type"] == type_filter]

        # Apply limit (get most recent)
        updates = updates[-limit:] if len(updates) > limit else updates

        return {
            "updates": updates,
            "total_count": len(updates),
            "board_last_updated": board["last_updated"]
        }

    def get_project_status(self) -> Dict[str, Any]:
        """
        Get overall project status and summary.

        Returns:
            Project status summary
        """
        board = self._load_board()

        # Calculate overall progress
        agent_progresses = []
        for agent_info in board["agents"].values():
            if agent_info.get("progress", 0) > 0:
                agent_progresses.append(agent_info["progress"])

        overall_progress = sum(agent_progresses) / len(agent_progresses) if agent_progresses else 0

        # Get recent activity
        recent_updates = board["updates"][-10:] if board["updates"] else []

        # Count update types
        update_counts = {}
        for update in board["updates"]:
            update_type = update.get("type", "unknown")
            update_counts[update_type] = update_counts.get(update_type, 0) + 1

        return {
            "project_name": board["project"].get("name", "Unknown"),
            "overall_progress": round(overall_progress, 1),
            "total_agents": len(board["agents"]),
            "total_updates": len(board["updates"]),
            "recent_updates": recent_updates,
            "update_counts": update_counts,
            "active_agents": [
                name for name, info in board["agents"].items()
                if info.get("current_task") is not None
            ],
            "collaboration_prompt_set": board["project"].get("collaboration_prompt") is not None
        }

    def share_interface(
        self,
        agent_name: str,
        interface_name: str,
        methods: List[str],
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Share an API interface definition with other agents.

        Args:
            agent_name: Agent sharing the interface
            interface_name: Name of the interface
            methods: List of method signatures
            description: Interface description

        Returns:
            Confirmation of interface sharing
        """
        board = self._load_board()

        interface_def = {
            "name": interface_name,
            "methods": methods,
            "description": description,
            "shared_by": agent_name,
            "shared_at": datetime.now().isoformat()
        }

        board["interfaces"][interface_name] = interface_def

        # Also post as an update
        self.post_update(
            agent_name=agent_name,
            message=f"Shared interface definition: {interface_name}",
            update_type="interface_sharing",
            tags=["interface", "api"]
        )

        self._save_board(board)

        logger.info(f"Interface '{interface_name}' shared by {agent_name}")
        return {
            "success": True,
            "interface_name": interface_name,
            "methods_count": len(methods)
        }

    def request_help(
        self,
        agent_name: str,
        topic: str,
        details: str,
        target_agent: Optional[str] = None,
        priority: str = "normal"
    ) -> Dict[str, Any]:
        """
        Request help from other agents.

        Args:
            agent_name: Agent requesting help
            topic: Help topic/subject
            details: Detailed description of what help is needed
            target_agent: Specific agent to request help from (optional)
            priority: Priority level (low, normal, high, urgent)

        Returns:
            Help request confirmation
        """
        board = self._load_board()

        help_request = {
            "id": len(board["help_requests"]) + 1,
            "requesting_agent": agent_name,
            "topic": topic,
            "details": details,
            "target_agent": target_agent,
            "priority": priority,
            "status": "open",
            "created_at": datetime.now().isoformat(),
            "responses": []
        }

        board["help_requests"].append(help_request)

        # Post as update
        target_msg = f" from {target_agent}" if target_agent else ""
        self.post_update(
            agent_name=agent_name,
            message=f"Requesting help{target_msg}: {topic}",
            update_type="help_request",
            tags=["help", priority]
        )

        self._save_board(board)

        logger.info(f"Help request posted by {agent_name}: {topic}")
        return {
            "success": True,
            "request_id": help_request["id"],
            "status": "posted"
        }

    def respond_to_help(
        self,
        agent_name: str,
        request_id: int,
        response: str,
        code_provided: bool = False
    ) -> Dict[str, Any]:
        """
        Respond to a help request.

        Args:
            agent_name: Agent providing help
            request_id: ID of the help request
            response: Help response/solution
            code_provided: Whether code was provided in response

        Returns:
            Response confirmation
        """
        board = self._load_board()

        # Find the help request
        help_request = None
        for req in board["help_requests"]:
            if req["id"] == request_id:
                help_request = req
                break

        if not help_request:
            return {"success": False, "error": "Help request not found"}

        # Add response
        response_entry = {
            "responding_agent": agent_name,
            "response": response,
            "code_provided": code_provided,
            "timestamp": datetime.now().isoformat()
        }

        help_request["responses"].append(response_entry)

        # Post as update
        requesting_agent = help_request["requesting_agent"]
        self.post_update(
            agent_name=agent_name,
            message=f"Provided help to {requesting_agent}: {help_request['topic']}",
            update_type="help_response",
            tags=["help", "collaboration"]
        )

        self._save_board(board)

        logger.info(f"Help response provided by {agent_name} for request #{request_id}")
        return {
            "success": True,
            "request_id": request_id,
            "response_count": len(help_request["responses"])
        }

    def report_progress(
        self,
        agent_name: str,
        task: str,
        percentage: int,
        details: str,
        estimated_completion: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Report task progress.

        Args:
            agent_name: Agent reporting progress
            task: Task name
            percentage: Progress percentage (0-100)
            details: Progress details
            estimated_completion: Estimated completion time

        Returns:
            Progress report confirmation
        """
        board = self._load_board()

        progress_report = {
            "agent": agent_name,
            "task": task,
            "percentage": percentage,
            "details": details,
            "estimated_completion": estimated_completion,
            "timestamp": datetime.now().isoformat()
        }

        board["progress_reports"].append(progress_report)

        # Post as update
        self.post_update(
            agent_name=agent_name,
            message=f"Progress on {task}: {percentage}% - {details}",
            task=task,
            progress=percentage,
            update_type="progress_report",
            tags=["progress"]
        )

        self._save_board(board)

        logger.info(f"Progress reported by {agent_name}: {task} at {percentage}%")
        return {
            "success": True,
            "current_progress": percentage,
            "task": task
        }

    def coordinate_with_team(
        self,
        agent_name: str,
        message: str,
        coordination_type: str = "general",
        target_agents: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Post coordination message to team.

        Args:
            agent_name: Agent posting coordination message
            message: Coordination message
            coordination_type: Type of coordination (general, dependency, conflict, etc.)
            target_agents: Specific agents to coordinate with

        Returns:
            Coordination message confirmation
        """
        target_info = f" (to: {', '.join(target_agents)})" if target_agents else ""

        return self.post_update(
            agent_name=agent_name,
            message=f"[COORDINATION{target_info}] {message}",
            update_type="coordination",
            tags=["coordination", coordination_type]
        )

    def share_code_snippet(
        self,
        agent_name: str,
        snippet: str,
        description: str,
        language: str = "dart",
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Share a code snippet with the team.

        Args:
            agent_name: Agent sharing code
            snippet: Code snippet
            description: Description of the code
            language: Programming language
            file_path: File path where code belongs

        Returns:
            Code sharing confirmation
        """
        return self.post_update(
            agent_name=agent_name,
            message=f"Shared {language} code: {description}",
            update_type="code_sharing",
            code_snippet=snippet,
            file_path=file_path,
            language=language,
            tags=["code", language, file_path] if file_path else ["code", language]
        )

    def get_recent_activity(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get recent activity summary.

        Args:
            hours: Number of hours to look back

        Returns:
            Recent activity summary
        """
        board = self._load_board()

        # Calculate cutoff time
        from datetime import datetime, timedelta
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()

        # Filter recent updates
        recent_updates = [
            u for u in board["updates"]
            if u["timestamp"] > cutoff
        ]

        # Group by agent
        agent_activity = {}
        for update in recent_updates:
            agent = update["agent"]
            if agent not in agent_activity:
                agent_activity[agent] = []
            agent_activity[agent].append(update)

        return {
            "timeframe_hours": hours,
            "total_updates": len(recent_updates),
            "active_agents": len(agent_activity),
            "agent_activity": agent_activity,
            "recent_updates": recent_updates[-10:]  # Last 10 updates
        }


def create_progress_board_tool(board_file: str = "progress_board.json", workspace_dir: str = ".") -> ProgressBoard:
    """
    Create a ProgressBoard tool instance.

    Args:
        board_file: Name of the progress board file
        workspace_dir: Directory to store the progress board

    Returns:
        ProgressBoard tool instance
    """
    progress_board = ProgressBoard(board_file, workspace_dir)
    progress_board.set_global()  # Make it available to all agents

    logger.info(f"Created ProgressBoard tool: {board_file}")
    return progress_board
