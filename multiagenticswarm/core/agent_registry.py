"""
Agent registry for centralized agent management and capability-based discovery.

This module provides a registry system for managing agents with their capabilities,
enabling dynamic agent discovery, health monitoring, and hot-swapping capabilities.
"""

import uuid
import time
from typing import Dict, List, Optional, Any, Callable, Set, TYPE_CHECKING
from threading import Lock
import json
from pathlib import Path

from .agent_manifest import AgentManifest, AgentMetrics, AgentStatus, HealthStatus
from ..utils.logger import get_logger

# Forward reference to avoid circular import
if TYPE_CHECKING:
    from .agent import Agent

logger = get_logger(__name__)


class AgentRegistry:
    """
    Centralized registry for agent management and discovery.
    
    The registry provides capability-based agent discovery, health monitoring,
    and hot-swapping functionality while maintaining agent lifecycle management.
    """
    
    _instance: Optional["AgentRegistry"] = None
    _lock = Lock()
    
    def __init__(self):
        """Initialize empty registry."""
        self._agents: Dict[str, "Agent"] = {}
        self._manifests: Dict[str, AgentManifest] = {}
        self._capability_index: Dict[str, Set[str]] = {}  # capability -> set of agent_ids
        self._lock = Lock()
        
        logger.debug("Agent registry initialized")
    
    @classmethod
    def get_instance(cls) -> "AgentRegistry":
        """Get singleton registry instance (thread-safe)."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance (mainly for testing)."""
        with cls._lock:
            cls._instance = None
    
    def register_agent(
        self, 
        agent: "Agent", 
        capabilities: List[str], 
        requirements: List[str] = None,
        version: str = "1.0.0",
        custom_id: str = None
    ) -> str:
        """
        Register an agent with the registry.
        
        Args:
            agent: The agent instance to register
            capabilities: List of capabilities this agent provides
            requirements: List of required tools/dependencies
            version: Agent version (default: "1.0.0")
            custom_id: Custom agent ID (if None, auto-generated)
            
        Returns:
            The assigned agent ID
            
        Raises:
            ValueError: If agent or capabilities are invalid
        """
        if agent is None:
            raise ValueError("Agent cannot be None")
        if not capabilities:
            raise ValueError("Agent must have at least one capability")
        
        # Generate or validate agent ID
        with self._lock:
            if custom_id:
                agent_id = custom_id
                if agent_id in self._agents:
                    raise ValueError(f"Agent ID '{agent_id}' already exists")
            else:
                agent_id = f"{agent.name}_{uuid.uuid4().hex[:8]}"
            # Create manifest
            manifest = AgentManifest(
                agent_id=agent_id,
                name=agent.name,
                agent_class=agent.__class__.__name__,
                version=version,
                capabilities=capabilities.copy(),
                requirements=requirements.copy() if requirements else [],
                workflow_type=getattr(agent, 'workflow_config', {}).get('workflow_type', 'default'),
                workflow_config=getattr(agent, 'workflow_config', {}).to_dict() if hasattr(getattr(agent, 'workflow_config', {}), 'to_dict') else {}
            )
            
            # Store agent and manifest
            self._agents[agent_id] = agent
            self._manifests[agent_id] = manifest
            
            # Update capability index
            for capability in capabilities:
                if capability not in self._capability_index:
                    self._capability_index[capability] = set()
                self._capability_index[capability].add(agent_id)
            
            # Set registry ID on agent for reference
            agent.registry_id = agent_id
            
            logger.info(f"Registered agent '{agent.name}' with ID '{agent_id}' and capabilities: {capabilities}")
            
            return agent_id
    
    def get_agent(self, agent_id: str) -> Optional["Agent"]:
        """
        Retrieve an agent by ID.
        
        Args:
            agent_id: The agent ID to retrieve
            
        Returns:
            The agent instance if found and active, None otherwise
        """
        if agent_id not in self._agents:
            return None
        
        manifest = self._manifests[agent_id]
        if manifest.status != "active":
            logger.warning(f"Agent '{agent_id}' is not active (status: {manifest.status})")
            return None
        
        return self._agents[agent_id]
    
    def get_manifest(self, agent_id: str) -> Optional[AgentManifest]:
        """
        Get agent manifest by ID.
        
        Args:
            agent_id: The agent ID
            
        Returns:
            The agent manifest if found, None otherwise
        """
        return self._manifests.get(agent_id)
    
    def find_agents_by_capability(self, capability: str, include_inactive: bool = False) -> List[str]:
        """
        Find all agent IDs that have a specific capability.
        
        Args:
            capability: The capability to search for
            include_inactive: Whether to include inactive agents
            
        Returns:
            List of agent IDs with the capability
        """
        with self._lock:
            if capability not in self._capability_index:
                return []
            # Take a snapshot of agent_ids and manifests under lock
            agent_ids = list(self._capability_index[capability])
            manifests = {agent_id: self._manifests.get(agent_id) for agent_id in agent_ids}
        
        if not include_inactive:
            # Filter out inactive agents
            agent_ids = [
                agent_id for agent_id in agent_ids
                if manifests.get(agent_id) is not None and manifests[agent_id].status == "active"
            ]
        
        return agent_ids
    
    def find_agents_by_capabilities(
        self, 
        capabilities: List[str], 
        match_all: bool = True,
        include_inactive: bool = False
    ) -> List[str]:
        """
        Find agents that match capability requirements.
        
        Args:
            capabilities: List of capabilities to match
            match_all: If True, agent must have ALL capabilities. If False, ANY capability
            include_inactive: Whether to include inactive agents
            
        Returns:
            List of matching agent IDs
        """
        if not capabilities:
            return []
        
        matching_agents = set()
        
        if match_all:
            # Agent must have ALL capabilities
            for i, capability in enumerate(capabilities):
                agents_with_cap = set(self.find_agents_by_capability(capability, include_inactive))
                if i == 0:
                    matching_agents = agents_with_cap
                else:
                    matching_agents &= agents_with_cap
        else:
            # Agent must have ANY capability
            for capability in capabilities:
                agents_with_cap = set(self.find_agents_by_capability(capability, include_inactive))
                matching_agents |= agents_with_cap
        
        return list(matching_agents)
    
    def get_agent_for_task(
        self, 
        required_capabilities: List[str], 
        preferred_capabilities: List[str] = None,
        available_tools: List[str] = None
    ) -> Optional["Agent"]:
        """
        Smart agent selection for a task based on capabilities and requirements.
        
        Args:
            required_capabilities: Must-have capabilities
            preferred_capabilities: Nice-to-have capabilities (for scoring)
            available_tools: Available tools (to check requirements)
            
        Returns:
            Best matching agent or None if no suitable agent found
        """
        if not required_capabilities:
            return None
        
        # Find agents with all required capabilities
        candidate_ids = self.find_agents_by_capabilities(required_capabilities, match_all=True)
        
        if not candidate_ids:
            logger.warning(f"No agents found with required capabilities: {required_capabilities}")
            return None
        
        # Filter by tool requirements if specified
        if available_tools is not None:
            candidate_ids = [
                agent_id for agent_id in candidate_ids
                if self._manifests[agent_id].matches_requirements(available_tools)
            ]
        
        if not candidate_ids:
            logger.warning(f"No agents found that match tool requirements: {available_tools}")
            return None
        
        # Score candidates based on preferred capabilities and metrics
        best_agent_id = None
        best_score = -1
        
        for agent_id in candidate_ids:
            manifest = self._manifests[agent_id]
            score = 0
            
            # Score based on preferred capabilities
            if preferred_capabilities:
                preferred_matches = sum(
                    1 for cap in preferred_capabilities
                    if manifest.has_capability(cap)
                )
                score += preferred_matches * 2
            
            # Score based on success rate (higher is better)
            score += manifest.metrics.success_rate * 10
            
            # Penalize based on error rate (lower is better)
            score -= manifest.metrics.error_rate * 5
            
            # Prefer faster agents (lower execution time is better)
            if manifest.metrics.average_execution_time > 0:
                score += max(0, 5 - manifest.metrics.average_execution_time)
            
            if score > best_score:
                best_score = score
                best_agent_id = agent_id
        
        if best_agent_id:
            logger.info(f"Selected agent '{best_agent_id}' for task (score: {best_score:.2f})")
            return self.get_agent(best_agent_id)
        
        return None
    
    def update_agent_status(self, agent_id: str, status: AgentStatus, health: HealthStatus = None) -> bool:
        """
        Update agent status and health.
        
        Args:
            agent_id: The agent ID
            status: New status
            health: New health status (optional)
            
        Returns:
            True if updated successfully, False otherwise
        """
        if agent_id not in self._manifests:
            return False
        
        with self._lock:
            manifest = self._manifests[agent_id]
            manifest.update_status(status, health)
            
            logger.info(f"Updated agent '{agent_id}' status to '{status}'" + 
                       (f" (health: {health})" if health else ""))
            
            return True
    
    def record_agent_execution(self, agent_id: str, success: bool, execution_time: float) -> bool:
        """
        Record an execution result for metrics tracking.
        
        Args:
            agent_id: The agent ID
            success: Whether the execution was successful
            execution_time: Execution time in seconds
            
        Returns:
            True if recorded successfully, False otherwise
        """
        if agent_id not in self._manifests:
            return False
        
        with self._lock:
            manifest = self._manifests[agent_id]
            manifest.metrics.record_execution(success, execution_time)
            
            logger.debug(f"Recorded execution for agent '{agent_id}': "
                        f"success={success}, time={execution_time:.2f}s")
            
            return True
    
    def remove_agent(self, agent_id: str) -> bool:
        """
        Remove an agent from the registry.
        
        Args:
            agent_id: The agent ID to remove
            
        Returns:
            True if removed successfully, False if not found
        """
        if agent_id not in self._agents:
            return False
        
        with self._lock:
            # Remove from capability index
            manifest = self._manifests[agent_id]
            for capability in manifest.capabilities:
                if capability in self._capability_index:
                    self._capability_index[capability].discard(agent_id)
                    if not self._capability_index[capability]:
                        del self._capability_index[capability]
            
            # Remove agent and manifest
            del self._agents[agent_id]
            del self._manifests[agent_id]
            
            logger.info(f"Removed agent '{agent_id}' from registry")
            
            return True
    
    def list_agents(self, status_filter: AgentStatus = None) -> List[str]:
        """
        List all registered agent IDs, optionally filtered by status.
        
        Args:
            status_filter: Only return agents with this status (None for all)
            
        Returns:
            List of agent IDs
        """
        if status_filter is None:
            return list(self._agents.keys())
        
        return [
            agent_id for agent_id, manifest in self._manifests.items()
            if manifest.status == status_filter
        ]
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """
        Get registry statistics and health overview.
        
        Returns:
            Dictionary with registry statistics
        """
        total_agents = len(self._agents)
        active_agents = len([m for m in self._manifests.values() if m.status == "active"])
        total_capabilities = len(self._capability_index)
        
        # Calculate average metrics
        if self._manifests:
            avg_success_rate = sum(m.metrics.success_rate for m in self._manifests.values()) / len(self._manifests)
            avg_execution_time = sum(m.metrics.average_execution_time for m in self._manifests.values()) / len(self._manifests)
        else:
            avg_success_rate = 0.0
            avg_execution_time = 0.0
        
        return {
            "total_agents": total_agents,
            "active_agents": active_agents,
            "inactive_agents": total_agents - active_agents,
            "total_capabilities": total_capabilities,
            "capabilities": list(self._capability_index.keys()),
            "average_success_rate": avg_success_rate,
            "average_execution_time": avg_execution_time
        }
    
    def export_registry(self, file_path: str = None) -> Dict[str, Any]:
        """
        Export registry to dictionary format (and optionally save to file).
        
        Args:
            file_path: Optional file path to save registry
            
        Returns:
            Registry data as dictionary
        """
        registry_data = {
            "agents": {
                agent_id: manifest.to_dict()
                for agent_id, manifest in self._manifests.items()
            },
            "capability_index": {
                capability: list(agent_ids)
                for capability, agent_ids in self._capability_index.items()
            },
            "exported_at": time.time()
        }
        
        if file_path:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w') as f:
                json.dump(registry_data, f, indent=2)
            logger.info(f"Registry exported to {file_path}")
        
        return registry_data
    
    def clear_registry(self) -> None:
        """Clear all agents from the registry (mainly for testing)."""
        with self._lock:
            self._agents.clear()
            self._manifests.clear()
            self._capability_index.clear()
            logger.info("Registry cleared")


# Global convenience functions
def get_registry() -> AgentRegistry:
    """Get the global agent registry instance."""
    return AgentRegistry.get_instance()


def register_agent(agent: "Agent", capabilities: List[str], **kwargs) -> str:
    """Convenience function to register an agent globally."""
    return get_registry().register_agent(agent, capabilities, **kwargs)


def find_agent_for_task(required_capabilities: List[str], **kwargs) -> Optional["Agent"]:
    """Convenience function to find an agent for a task."""
    return get_registry().get_agent_for_task(required_capabilities, **kwargs)
