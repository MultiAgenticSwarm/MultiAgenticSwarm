import time
import yaml
import os
from typing import Dict, List, Any, Optional
from enum import Enum
from pathlib import Path


class PermissionStatus(Enum):
    """Permission status types."""
    ALLOWED = "ALLOWED"
    DENIED = "DENIED" 
    CONDITIONAL = "CONDITIONAL"
    ROLE_BASED = "ROLE_BASED"
    TIME_RESTRICTED = "TIME_RESTRICTED"


class ToolPermissions:
    def __init__(self, config_path: Optional[str] = None):
        # {agent_id: {tool_id: {"status": str,
        #                       "quota": {"per_day": int, "calls": int, "last_reset": float}}}}
        self.permissions = {}
        self.logs = []
        self.roles = {}  # Role-based permissions
        self.config_path = config_path or self._find_config_file()
        self.config_data = {}
        
        # Load configuration if available
        self._load_config()
    
    def _find_config_file(self) -> Optional[str]:
        """Find permission config file in standard locations."""
        possible_paths = [
            "config/tool_permissions.yaml",
            "config/permissions.yaml",
            "../config/tool_permissions.yaml"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None
    
    def _load_config(self):
        """Load permissions from config file."""
        if not self.config_path or not os.path.exists(self.config_path):
            return
            
        try:
            with open(self.config_path, 'r') as file:
                self.config_data = yaml.safe_load(file) or {}
                
            # Load role definitions
            self.roles = self.config_data.get("roles", {})
            
            # Apply config-based permissions
            self._apply_config_permissions()
            
        except Exception as e:
            print(f"Warning: Could not load permission config: {e}")
    
    def _apply_config_permissions(self):
        """Apply permissions from config file."""
        agent_permissions = self.config_data.get("agent_permissions", {})
        
        for agent_id, agent_config in agent_permissions.items():
            # Apply direct tool permissions
            allowed_tools = agent_config.get("allowed_tools", [])
            denied_tools = agent_config.get("denied_tools", [])
            
            for tool_id in allowed_tools:
                self.set_permission(agent_id, tool_id, PermissionStatus.ALLOWED.value)
            
            for tool_id in denied_tools:
                self.set_permission(agent_id, tool_id, PermissionStatus.DENIED.value)
            
            # Apply role-based permissions
            role = agent_config.get("role")
            if role and role in self.roles:
                role_tools = self.roles[role].get("allowed_tools", [])
                for tool_id in role_tools:
                    self.set_permission(agent_id, tool_id, PermissionStatus.ROLE_BASED.value)

    def set_permission(self, agent_id, tool_id, status="ALLOWED", quota=None):
        if isinstance(quota, int):
            quota = {"per_day": quota}

        self.permissions.setdefault(agent_id, {})[tool_id] = {
            "status": status,
            "quota": {
                "per_day": quota.get("per_day"),
                "calls": 0,
                "last_reset": time.time(),
            }
            if quota
            else None,
        }

    def check_permission(self, agent_id, tool_id, context=None):
        """
        Enhanced permission checking with multiple strategies.
        
        Args:
            agent_id: Agent requesting permission
            tool_id: Tool being requested  
            context: Optional context for conditional permissions
            
        Returns:
            (allowed: bool, reason: str)
        """
        # Check workflow restrictions FIRST (they override everything)
        if context and self.config_data:
            current_phase = context.get("workflow_phase")
            if current_phase:
                restrictions = self.config_data.get("workflow_restrictions", {})
                phase_restrictions = restrictions.get(current_phase, {})
                
                if tool_id in phase_restrictions.get("restricted_tools", []):
                    # Check if only specific agents are allowed during this phase
                    allowed_agents = phase_restrictions.get("allowed_agents", [])
                    if allowed_agents and agent_id not in allowed_agents:
                        return False, f"Tool restricted during {current_phase} phase"
                    elif not allowed_agents:  # Tool is restricted for everyone
                        return False, f"Tool restricted during {current_phase} phase"
        
        # Check explicit permissions
        record = self.permissions.get(agent_id, {}).get(tool_id)
        if record:
            return self._check_explicit_permission(record, context)
        
        # Check config-based permissions
        if self.config_data:
            config_result = self._check_config_permission(agent_id, tool_id, context)
            if config_result[0] is not None:  # If config has a decision
                return config_result
        
        # Check role-based permissions
        role_result = self._check_role_permission(agent_id, tool_id)
        if role_result[0] is not None:
            return role_result
        
        # Default behavior
        return False, "No permission entry"
    
    def _check_explicit_permission(self, record, context):
        """Check explicitly set permission."""
        status = record["status"]
        
        # === Step 1: Status-based check ===
        if status == PermissionStatus.DENIED.value:
            return False, "Permission denied"

        if status == PermissionStatus.CONDITIONAL.value:
            if not (context and context.get("approved", False)):
                return False, "Condition not satisfied"
        
        # === Step 2: Quota-based check ===
        quota = record.get("quota")
        if quota:
            quota_check = self._check_quota(quota)
            if not quota_check[0]:
                return quota_check
        
        return True, None
    
    def _check_config_permission(self, agent_id, tool_id, context):
        """Check config-based permissions."""
        agent_permissions = self.config_data.get("agent_permissions", {})
        
        if agent_id not in agent_permissions:
            return None, None  # No config for this agent
        
        agent_config = agent_permissions[agent_id]
        
        # Check denied tools first (explicit deny)
        if tool_id in agent_config.get("denied_tools", []):
            return False, "Tool denied by configuration"
        
        # Check allowed tools
        if tool_id in agent_config.get("allowed_tools", []):
            return True, None
        
        return None, None  # No explicit config decision
    
    def _check_role_permission(self, agent_id, tool_id):
        """Check role-based permissions."""
        agent_permissions = self.config_data.get("agent_permissions", {})
        agent_config = agent_permissions.get(agent_id, {})
        role = agent_config.get("role")
        
        if not role or role not in self.roles:
            return None, None
        
        role_config = self.roles[role]
        if tool_id in role_config.get("allowed_tools", []):
            return True, "Role-based permission"
        
        return None, None
    
    def _check_quota(self, quota):
        """Check quota limits."""
        now = time.time()
        
        # Reset quota every 24h
        if now - quota["last_reset"] > 86400:
            quota["calls"] = 0
            quota["last_reset"] = now

        if quota["per_day"] is not None and quota["calls"] >= quota["per_day"]:
            return False, "Daily quota exceeded"

        quota["calls"] += 1
        return True, None

    def set_role(self, role_name: str, allowed_tools: List[str], description: str = ""):
        """Define a new role with allowed tools."""
        self.roles[role_name] = {
            "allowed_tools": allowed_tools,
            "description": description
        }
    
    def assign_role(self, agent_id: str, role_name: str):
        """Assign a role to an agent."""
        if role_name not in self.roles:
            raise ValueError(f"Role '{role_name}' not defined")
        
        # Set role-based permissions for all tools in the role
        role_tools = self.roles[role_name]["allowed_tools"]
        for tool_id in role_tools:
            self.set_permission(agent_id, tool_id, PermissionStatus.ROLE_BASED.value)
    
    def get_agent_permissions(self, agent_id: str) -> Dict[str, Any]:
        """Get all permissions for an agent."""
        agent_perms = self.permissions.get(agent_id, {})
        
        # Add config-based permissions
        config_perms = {}
        if self.config_data:
            agent_config = self.config_data.get("agent_permissions", {}).get(agent_id, {})
            config_perms = {
                "allowed_tools": agent_config.get("allowed_tools", []),
                "denied_tools": agent_config.get("denied_tools", []),
                "role": agent_config.get("role")
            }
        
        return {
            "explicit_permissions": agent_perms,
            "config_permissions": config_perms,
            "effective_tools": self._get_effective_tools(agent_id)
        }
    
    def _get_effective_tools(self, agent_id: str) -> List[str]:
        """Get list of tools agent can actually use."""
        # This would require tool registry integration
        # For now, return tools with explicit permissions
        return list(self.permissions.get(agent_id, {}).keys())
    
    def reload_config(self):
        """Reload configuration from file."""
        self._load_config()

    def log(self, agent_id, tool_id, action, outcome, details=None):
        entry = {
            "agent": agent_id,
            "tool": tool_id,
            "action": action,
            "outcome": outcome,
            "details": details,
            "timestamp": time.time(),
        }
        self.logs.append(entry)

    def get_logs(self):
        return self.logs
