"""
Agent manifest definitions for capability tracking and metadata management.

This module provides data structures for describing agent capabilities,
requirements, and operational metadata in the agent registry system.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Any
import time

# Type definitions for agent status and health
AgentStatus = Literal["active", "inactive", "error", "maintenance"]
HealthStatus = Literal["healthy", "degraded", "unhealthy", "unknown"]


@dataclass
class AgentCapability:
    """
    Represents a specific capability that an agent can perform.
    
    Capabilities are used for agent discovery and task matching in the registry.
    """
    name: str
    description: str
    category: str = "functional"  # "functional", "technical", "collaboration"
    confidence: float = 1.0  # 0.0 to 1.0, how well the agent handles this capability
    
    def __post_init__(self):
        """Validate capability parameters."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")


@dataclass
class AgentMetrics:
    """
    Performance and operational metrics for an agent.
    
    Used for health monitoring and agent selection optimization.
    """
    total_executions: int = 0
    successful_executions: int = 0
    average_execution_time: float = 0.0
    last_execution_time: float = 0.0
    error_count: int = 0
    last_error_time: float = 0.0
    created_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_executions == 0:
            return 0.0
        return self.successful_executions / self.total_executions
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate as percentage."""
        if self.total_executions == 0:
            return 0.0
        return self.error_count / self.total_executions
    
    @property 
    def failed_executions(self) -> int:
        """Get number of failed executions (alias for error_count)."""
        return self.error_count
    
    def record_execution(self, success: bool, execution_time: float) -> None:
        """Record an execution result and update metrics."""
        self.total_executions += 1
        self.last_execution_time = execution_time
        self.last_updated = time.time()
        
        if success:
            self.successful_executions += 1
        else:
            self.error_count += 1
            self.last_error_time = time.time()
        
        # Update rolling average execution time
        if self.total_executions == 1:
            self.average_execution_time = execution_time
        else:
            # Simple exponential moving average
            alpha = 0.1  # Weight for new values
            self.average_execution_time = (
                alpha * execution_time + 
                (1 - alpha) * self.average_execution_time
            )


@dataclass
class AgentManifest:
    """
    Complete manifest describing an agent's capabilities, requirements, and status.
    
    This is the core metadata structure used by the agent registry for
    agent discovery, health monitoring, and lifecycle management.
    """
    agent_id: str
    name: str
    agent_class: str
    version: str
    capabilities: List[str]  # Simple string capabilities for easy matching
    requirements: List[str] = field(default_factory=list)  # Required tools/dependencies
    status: AgentStatus = "active"
    health: HealthStatus = "healthy"
    metrics: AgentMetrics = field(default_factory=AgentMetrics)
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional custom metadata
    
    # Workflow configuration reference
    workflow_type: str = "default"
    workflow_config: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate manifest parameters."""
        if not self.agent_id:
            raise ValueError("Agent ID cannot be empty")
        if not self.name:
            raise ValueError("Agent name cannot be empty")
        if not isinstance(self.capabilities, list):
            raise ValueError("Capabilities must be a list")
    
    def has_capability(self, capability: str) -> bool:
        """Check if agent has a specific capability."""
        return capability in self.capabilities
    
    def has_all_capabilities(self, capabilities: List[str]) -> bool:
        """Check if agent has all specified capabilities."""
        return all(self.has_capability(cap) for cap in capabilities)
    
    def has_any_capability(self, capabilities: List[str]) -> bool:
        """Check if agent has any of the specified capabilities."""
        return any(self.has_capability(cap) for cap in capabilities)
    
    def matches_requirements(self, available_tools: List[str]) -> bool:
        """Check if all agent requirements are available."""
        if not self.requirements:
            return True
        return all(req in available_tools for req in self.requirements)
    
    def update_status(self, status: AgentStatus, health: HealthStatus = None) -> None:
        """Update agent status and optionally health."""
        self.status = status
        if health is not None:
            self.health = health
        self.metrics.last_updated = time.time()
    
    def add_capability(self, capability: str) -> None:
        """Add a new capability to the agent."""
        if capability not in self.capabilities:
            self.capabilities.append(capability)
            self.metrics.last_updated = time.time()
    
    def remove_capability(self, capability: str) -> None:
        """Remove a capability from the agent."""
        if capability in self.capabilities:
            self.capabilities.remove(capability)
            self.metrics.last_updated = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert manifest to dictionary representation."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "agent_class": self.agent_class,
            "version": self.version,
            "capabilities": self.capabilities.copy(),
            "requirements": self.requirements.copy(),
            "status": self.status,
            "health": self.health,
            "metrics": {
                "total_executions": self.metrics.total_executions,
                "successful_executions": self.metrics.successful_executions,
                "success_rate": self.metrics.success_rate,
                "average_execution_time": self.metrics.average_execution_time,
                "error_rate": self.metrics.error_rate,
                "created_at": self.metrics.created_at,
                "last_updated": self.metrics.last_updated
            },
            "metadata": self.metadata.copy(),
            "workflow_type": self.workflow_type,
            "workflow_config": self.workflow_config.copy()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentManifest":
        """Create manifest from dictionary representation."""
        metrics_data = data.get("metrics", {})
        metrics = AgentMetrics(
            total_executions=metrics_data.get("total_executions", 0),
            successful_executions=metrics_data.get("successful_executions", 0),
            average_execution_time=metrics_data.get("average_execution_time", 0.0),
            error_count=metrics_data.get("error_count", 0),
            created_at=metrics_data.get("created_at", time.time()),
            last_updated=metrics_data.get("last_updated", time.time())
        )
        
        return cls(
            agent_id=data["agent_id"],
            name=data["name"],
            agent_class=data["agent_class"],
            version=data["version"],
            capabilities=data["capabilities"],
            requirements=data.get("requirements", []),
            status=data.get("status", "active"),
            health=data.get("health", "healthy"),
            metrics=metrics,
            metadata=data.get("metadata", {}),
            workflow_type=data.get("workflow_type", "default"),
            workflow_config=data.get("workflow_config", {})
        )


# Utility functions for common capability patterns
def create_ui_capabilities() -> List[str]:
    """Standard capabilities for UI-focused agents."""
    return ["ui_design", "frontend", "responsive", "user_interface"]


def create_backend_capabilities() -> List[str]:
    """Standard capabilities for backend-focused agents."""
    return ["backend", "api", "database", "server_logic"]


def create_fullstack_capabilities() -> List[str]:
    """Standard capabilities for full-stack agents."""
    return create_ui_capabilities() + create_backend_capabilities()


def create_testing_capabilities() -> List[str]:
    """Standard capabilities for testing-focused agents."""
    return ["testing", "quality_assurance", "test_automation", "validation"]


def create_devops_capabilities() -> List[str]:
    """Standard capabilities for DevOps-focused agents."""
    return ["deployment", "ci_cd", "infrastructure", "monitoring"]
