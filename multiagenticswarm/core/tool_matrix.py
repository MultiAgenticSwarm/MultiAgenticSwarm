"""Tool permission matrix for controlling agent access to tools."""

import time
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..utils.logger import get_logger
from .tool_conditions import get_conditions

logger = get_logger(__name__)


class ToolMatrix:
    """
    Permission matrix for tool access control.
    
    Features:
    - Static permissions (always/never)
    - Conditional permissions based on context
    - Usage quotas with time-based reset
    - Audit trail for permission checks
    """
    
    def __init__(self, conditions: Optional["ToolConditions"] = None):
        """Initialize the permission matrix.

        Args:
            conditions: Optional conditions evaluator instance for testing or
                custom behavior. If not provided, the shared singleton is used.
        """
        self.permissions: Dict[str, Dict[str, str]] = {}
        self.quotas: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self.audit_trail: List[Dict[str, Any]] = []
        self.conditions = conditions if conditions is not None else get_conditions()
        logger.info("Tool permission matrix initialized")
    
    def register_agent(self, agent_id: str, custom_permissions: Optional[Dict[str, str]] = None):
        """Register an agent with default or custom permissions."""
        if agent_id in self.permissions:
            logger.warning(f"Agent {agent_id} already registered")
            return
        
        default_permissions = {
            "Logger": "always",
            "Memory": "always",
            "Database": "never",
            "FileSystem": "never",
            "EmailSender": "never",
            "CodeWriter": "never"
        }
        
        if custom_permissions:
            default_permissions.update(custom_permissions)
        
        self.permissions[agent_id] = default_permissions
        self.quotas[agent_id] = {}
        logger.info(f"Agent {agent_id} registered with {len(default_permissions)} permissions")
    
    def check_permission(self, agent_id: str, tool_name: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Check if an agent has permission to use a tool.
        
        Args:
            agent_id: Agent identifier
            tool_name: Tool to check access for
            context: Runtime context for conditional checks
            
        Returns:
            True if permission granted, False otherwise
        """
        if agent_id not in self.permissions:
            self._log_audit(agent_id, tool_name, "denied", "agent_not_registered")
            return False
        
        permission = self.permissions[agent_id].get(tool_name, "never")
        result = self._evaluate_permission(agent_id, tool_name, permission, context)
        
        reason = "allowed" if result else "denied"
        self._log_audit(agent_id, tool_name, reason, permission)
        
        return result
    
    def _evaluate_permission(self, agent_id: str, tool_name: str, permission: str, context: Optional[Dict[str, Any]]) -> bool:
        """Evaluate permission string and return access decision."""
        if permission == "always":
            return True
        elif permission == "never":
            return False
        elif permission.startswith("conditional:"):
            condition = permission.replace("conditional:", "")
            if self.conditions:
                return self.conditions.evaluate_condition(condition, context or {})
            return False
        elif permission.startswith("quota:"):
            return self._check_quota(agent_id, tool_name, permission)
        else:
            return False
    
    def _check_quota(self, agent_id: str, tool_name: str, permission: str) -> bool:
        """Validate quota-based permission."""
        try:
            quota_part = permission.replace("quota:", "")
            limit_str, period = quota_part.split("/")
            limit = int(limit_str)
        except ValueError:
            return False
        
        if tool_name not in self.quotas[agent_id]:
            self.quotas[agent_id][tool_name] = {
                "used": 0,
                "limit": limit,
                "period": period,
                "reset_time": time.time()
            }
        
        quota = self.quotas[agent_id][tool_name]
        
        if self._should_reset_quota(quota):
            quota["used"] = 0
            quota["reset_time"] = time.time()
        
        return quota["used"] < quota["limit"]
    
    def _should_reset_quota(self, quota: Dict[str, Any]) -> bool:
        """Determine if quota should reset based on time period."""
        now = time.time()
        period = quota["period"]
        reset_time = quota["reset_time"]
        
        if period == "hour":
            return now - reset_time >= 3600
        elif period == "day":
            return now - reset_time >= 86400
        else:
            return False
    
    def use_quota(self, agent_id: str, tool_name: str) -> bool:
        """Increment quota usage after successful tool execution."""
        if agent_id in self.quotas and tool_name in self.quotas[agent_id]:
            quota = self.quotas[agent_id][tool_name]
            if quota["used"] < quota["limit"]:
                quota["used"] += 1
                return True
        return False
    
    def update_permission(self, agent_id: str, tool_name: str, permission: str):
        """Update permission for an agent-tool combination at runtime."""
        if agent_id not in self.permissions:
            self.register_agent(agent_id)
        
        self.permissions[agent_id][tool_name] = permission
        logger.info(f"Updated {agent_id} permission for {tool_name}: {permission}")
    
    def get_agent_permissions(self, agent_id: str) -> Dict[str, str]:
        """Retrieve all permissions for an agent."""
        return self.permissions.get(agent_id, {}).copy()
    
    def load_from_config(self, config: Dict[str, Any]):
        """Load permissions from configuration dictionary."""
        tool_permissions = config.get("tool_permissions", {})
        
        for agent_id, permissions in tool_permissions.items():
            self.register_agent(agent_id, permissions)
        
        logger.info(f"Loaded permissions for {len(tool_permissions)} agents from config")
    
    def _log_audit(self, agent_id: str, tool_name: str, result: str, reason: str):
        """Record permission check to audit trail."""
        self.audit_trail.append({
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "tool_name": tool_name,
            "result": result,
            "reason": reason
        })
        
        if len(self.audit_trail) > 1000:
            self.audit_trail = self.audit_trail[-1000:]
    
    def get_audit_trail(self, agent_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve audit trail entries.
        
        Args:
            agent_id: Optional filter by agent
            limit: Maximum entries to return (most recent first)
        
        Returns:
            List of audit entries
        """
        entries = self.audit_trail
        
        if agent_id:
            entries = [e for e in entries if e["agent_id"] == agent_id]
        
        return list(reversed(entries[-limit:]))
