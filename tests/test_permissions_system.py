"""
Comprehensive tests for the dynamic tool permissions system.

Tests cover:
- Dynamic permission updates
- Conditional permissions
- Role-based access
- Usage quotas
- Audit trail functionality
"""

import pytest
import time
from multiagenticswarm.core.tool_matrix import ToolMatrix
from multiagenticswarm.core.tool_conditions import ToolConditions
from multiagenticswarm.core.tool_executor import ToolExecutor
from multiagenticswarm.core.system import System


class TestToolMatrix:
    """Test the core permission matrix functionality."""
    
    def test_agent_registration(self):
        """Test registering agents with default and custom permissions."""
        matrix = ToolMatrix()
        
        # Register with defaults
        matrix.register_agent("agent1")
        assert "agent1" in matrix.permissions
        assert matrix.permissions["agent1"]["Logger"] == "always"
        assert matrix.permissions["agent1"]["Database"] == "never"
        
        # Register with custom permissions
        matrix.register_agent("agent2", {"Database": "always", "Custom": "never"})
        assert matrix.permissions["agent2"]["Database"] == "always"
        assert matrix.permissions["agent2"]["Custom"] == "never"
    
    def test_static_permissions(self):
        """Test always and never permissions."""
        matrix = ToolMatrix()
        matrix.register_agent("agent1", {
            "ToolA": "always",
            "ToolB": "never"
        })
        
        assert matrix.check_permission("agent1", "ToolA") == True
        assert matrix.check_permission("agent1", "ToolB") == False
    
    def test_conditional_permissions(self):
        """Test conditional permissions based on context."""
        matrix = ToolMatrix()
        matrix.register_agent("agent1", {
            "FileSystem": "conditional:design_phase"
        })
        
        # Design phase context - should allow
        context_design = {"current_phase": "design"}
        assert matrix.check_permission("agent1", "FileSystem", context_design) == True
        
        # Implementation phase - should deny
        context_impl = {"current_phase": "implementation"}
        assert matrix.check_permission("agent1", "FileSystem", context_impl) == False
        
        # No context - should deny
        assert matrix.check_permission("agent1", "FileSystem") == False
    
    def test_quota_permissions(self):
        """Test usage quotas with automatic reset."""
        matrix = ToolMatrix()
        matrix.register_agent("agent1", {
            "EmailSender": "quota:3/day"
        })
        
        # First 3 uses should succeed
        assert matrix.check_permission("agent1", "EmailSender") == True
        matrix.use_quota("agent1", "EmailSender")
        
        assert matrix.check_permission("agent1", "EmailSender") == True
        matrix.use_quota("agent1", "EmailSender")
        
        assert matrix.check_permission("agent1", "EmailSender") == True
        matrix.use_quota("agent1", "EmailSender")
        
        # 4th use should fail
        assert matrix.check_permission("agent1", "EmailSender") == False
    
    def test_quota_reset(self):
        """Test that quotas reset after time period."""
        matrix = ToolMatrix()
        matrix.register_agent("agent1", {
            "Tool": "quota:2/hour"
        })
        
        # Use quota twice
        matrix.check_permission("agent1", "Tool")
        matrix.use_quota("agent1", "Tool")
        matrix.check_permission("agent1", "Tool")
        matrix.use_quota("agent1", "Tool")
        
        # Should be exhausted
        assert matrix.check_permission("agent1", "Tool") == False
        
        # Manually reset the time
        matrix.quotas["agent1"]["Tool"]["reset_time"] = time.time() - 3601
        
        # Should allow again after reset
        assert matrix.check_permission("agent1", "Tool") == True
    
    def test_runtime_permission_update(self):
        """Test updating permissions at runtime."""
        matrix = ToolMatrix()
        matrix.register_agent("agent1", {"Database": "never"})
        
        # Initially denied
        assert matrix.check_permission("agent1", "Database") == False
        
        # Update to allow
        matrix.update_permission("agent1", "Database", "always")
        
        # Now allowed
        assert matrix.check_permission("agent1", "Database") == True
    
    def test_audit_trail(self):
        """Test that permission checks are logged to audit trail."""
        matrix = ToolMatrix()
        matrix.register_agent("agent1", {"ToolA": "always", "ToolB": "never"})
        
        # Make some permission checks
        matrix.check_permission("agent1", "ToolA")
        matrix.check_permission("agent1", "ToolB")
        matrix.check_permission("unknown_agent", "ToolA")
        
        # Get audit trail
        audit = matrix.get_audit_trail()
        
        assert len(audit) >= 3
        assert any(e["agent_id"] == "agent1" and e["tool_name"] == "ToolA" and e["result"] == "allowed" for e in audit)
        assert any(e["agent_id"] == "agent1" and e["tool_name"] == "ToolB" and e["result"] == "denied" for e in audit)
        assert any(e["agent_id"] == "unknown_agent" and e["result"] == "denied" for e in audit)
    
    def test_audit_trail_filtering(self):
        """Test filtering audit trail by agent."""
        matrix = ToolMatrix()
        matrix.register_agent("agent1", {"ToolA": "always"})
        matrix.register_agent("agent2", {"ToolB": "always"})
        
        matrix.check_permission("agent1", "ToolA")
        matrix.check_permission("agent2", "ToolB")
        matrix.check_permission("agent1", "ToolA")
        
        # Get audit for specific agent
        audit_agent1 = matrix.get_audit_trail(agent_id="agent1")
        
        assert all(e["agent_id"] == "agent1" for e in audit_agent1)
        assert len(audit_agent1) == 2


class TestToolConditions:
    """Test conditional permission evaluation."""
    
    def test_development_mode_condition(self):
        """Test development_mode condition."""
        conditions = ToolConditions()
        
        assert conditions.evaluate_condition("development_mode", {"mode": "development"}) == True
        assert conditions.evaluate_condition("development_mode", {"mode": "production"}) == False
    
    def test_design_phase_condition(self):
        """Test design_phase condition."""
        conditions = ToolConditions()
        
        assert conditions.evaluate_condition("design_phase", {"current_phase": "design"}) == True
        assert conditions.evaluate_condition("design_phase", {"current_phase": "testing"}) == False
    
    def test_data_safe_condition(self):
        """Test data_safe condition."""
        conditions = ToolConditions()
        
        assert conditions.evaluate_condition("data_safe", {"data_sensitive": False}) == True
        assert conditions.evaluate_condition("data_safe", {"data_sensitive": True}) == False
        assert conditions.evaluate_condition("data_safe", {}) == False  # Default to sensitive
    
    def test_user_approved_condition(self):
        """Test user_approved condition."""
        conditions = ToolConditions()
        
        assert conditions.evaluate_condition("user_approved", {"user_approval": True}) == True
        assert conditions.evaluate_condition("user_approved", {"user_approval": False}) == False


class TestToolExecutor:
    """Test the tool executor integration."""
    
    def test_executor_initialization(self):
        """Test that executor initializes with permission matrix."""
        executor = ToolExecutor()
        
        assert executor.permission_matrix is not None
        assert executor.conditions is not None
        assert executor.context == {}
    
    def test_context_management(self):
        """Test setting and updating execution context."""
        executor = ToolExecutor()
        
        executor.set_context({"phase": "design"})
        assert executor.context["phase"] == "design"
        
        executor.set_context({"mode": "dev"})
        assert executor.context["phase"] == "design"
        assert executor.context["mode"] == "dev"
    
    def test_permission_methods(self):
        """Test executor permission management methods."""
        executor = ToolExecutor()
        
        # Register agent
        executor.register_agent("test_agent", {"Tool1": "always"})
        
        # Get permissions
        perms = executor.get_agent_permissions("test_agent")
        assert perms["Tool1"] == "always"
        
        # Update permission
        executor.update_permission("test_agent", "Tool1", "never")
        perms = executor.get_agent_permissions("test_agent")
        assert perms["Tool1"] == "never"
    
    def test_audit_trail_access(self):
        """Test accessing audit trail through executor."""
        executor = ToolExecutor()
        executor.register_agent("agent1", {"Tool1": "always"})
        
        # Generate some audit entries
        executor.permission_matrix.check_permission("agent1", "Tool1")
        
        # Get audit trail
        audit = executor.get_audit_trail()
        assert len(audit) > 0


class TestSystemIntegration:
    """Test the full system integration."""
    
    def test_system_loads_permissions_from_config(self):
        """Test that system loads permissions from YAML config on startup."""
        # Create system without config file
        system = System(enable_logging=False)
        
        # Manually load config
        config = {
            "tool_permissions": {
                "ui_agent": {
                    "CodeWriter": "always",
                    "Database": "never"
                }
            }
        }
        system.tool_executor.load_permissions_from_config(config)
        
        # Verify permissions loaded
        perms = system.get_agent_permissions("ui_agent")
        assert perms["CodeWriter"] == "always"
        assert perms["Database"] == "never"
    
    def test_system_runtime_updates(self):
        """Test updating permissions at runtime through system."""
        system = System(enable_logging=False)
        system.tool_executor.register_agent("agent1", {"Tool1": "never"})
        
        # Update through system
        system.update_tool_permission("agent1", "Tool1", "always")
        
        # Verify update
        perms = system.get_agent_permissions("agent1")
        assert perms["Tool1"] == "always"
    
    def test_system_context_management(self):
        """Test managing execution context through system."""
        system = System(enable_logging=False)
        
        # Set context
        system.set_execution_context({"current_phase": "design", "mode": "dev"})
        
        # Verify context is set
        assert system.tool_executor.context["current_phase"] == "design"
        assert system.tool_executor.context["mode"] == "dev"
    
    def test_system_audit_trail(self):
        """Test accessing audit trail through system."""
        system = System(enable_logging=False)
        system.tool_executor.register_agent("agent1", {"Tool1": "always"})
        
        # Generate audit entries
        system.tool_executor.permission_matrix.check_permission("agent1", "Tool1")
        
        # Get audit trail
        audit = system.get_permission_audit_trail()
        assert len(audit) > 0
        assert audit[0]["agent_id"] == "agent1"


class TestRoleBasedAccess:
    """Test role-based access patterns."""
    
    def test_different_roles_different_permissions(self):
        """Test that different agent roles have different permissions."""
        matrix = ToolMatrix()
        
        # Define roles
        matrix.register_agent("viewer", {
            "ReadData": "always",
            "WriteData": "never",
            "DeleteData": "never"
        })
        
        matrix.register_agent("editor", {
            "ReadData": "always",
            "WriteData": "always",
            "DeleteData": "never"
        })
        
        matrix.register_agent("admin", {
            "ReadData": "always",
            "WriteData": "always",
            "DeleteData": "always"
        })
        
        # Verify role permissions
        assert matrix.check_permission("viewer", "ReadData") == True
        assert matrix.check_permission("viewer", "WriteData") == False
        assert matrix.check_permission("viewer", "DeleteData") == False
        
        assert matrix.check_permission("editor", "ReadData") == True
        assert matrix.check_permission("editor", "WriteData") == True
        assert matrix.check_permission("editor", "DeleteData") == False
        
        assert matrix.check_permission("admin", "ReadData") == True
        assert matrix.check_permission("admin", "WriteData") == True
        assert matrix.check_permission("admin", "DeleteData") == True


class TestComplexScenarios:
    """Test complex real-world scenarios."""
    
    def test_mixed_permission_types(self):
        """Test agent with mix of permission types."""
        conditions = ToolConditions()
        matrix = ToolMatrix(conditions=conditions)
        
        matrix.register_agent("complex_agent", {
            "Logger": "always",
            "Database": "never",
            "FileSystem": "conditional:design_phase",
            "EmailSender": "quota:5/day"
        })
        
        # Static permissions work
        assert matrix.check_permission("complex_agent", "Logger") == True
        assert matrix.check_permission("complex_agent", "Database") == False
        
        # Conditional permissions work
        assert matrix.check_permission("complex_agent", "FileSystem", {"current_phase": "design"}) == True
        assert matrix.check_permission("complex_agent", "FileSystem", {"current_phase": "test"}) == False
        
        # Quota permissions work
        assert matrix.check_permission("complex_agent", "EmailSender") == True
    
    def test_permission_changes_during_execution(self):
        """Test changing permissions mid-execution."""
        matrix = ToolMatrix()
        matrix.register_agent("agent1", {"Tool1": "never"})
        
        # Initially denied
        assert matrix.check_permission("agent1", "Tool1") == False
        
        # Grant access
        matrix.update_permission("agent1", "Tool1", "quota:3/day")
        
        # Now allowed with quota
        assert matrix.check_permission("agent1", "Tool1") == True
        matrix.use_quota("agent1", "Tool1")
        
        # Change to always
        matrix.update_permission("agent1", "Tool1", "always")
        
        # Now unlimited
        assert matrix.check_permission("agent1", "Tool1") == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
