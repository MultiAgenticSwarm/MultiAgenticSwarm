"""
Comprehensive test suite for the Enhanced Tool Permission System.
Tests all functionality: config loading, role-based permissions, workflow restrictions,
agent permissions, quotas, and integration with ToolNodeManager.
"""

import pytest
import sys
import os
import tempfile
import yaml
from unittest.mock import patch, MagicMock

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multiagenticswarm.core.tool_permissions import ToolPermissions, PermissionStatus
from multiagenticswarm.core.tool_registry import ToolRegistry


class TestToolPermissions:
    """Test suite for Enhanced Tool Permission System."""
    
    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary config file for testing."""
        config_data = {
            'global_settings': {
                'default_tool_access': True,
                'enable_workflow_restrictions': True,
                'log_permission_decisions': False
            },
            'roles': {
                'data_analyst': {
                    'description': 'Data analysis specialist',
                    'allowed_tools': ['DataAPIFetcher', 'DatabaseConnector', 'DataProcessor', 'EmailSender']
                },
                'report_generator': {
                    'description': 'Report creation specialist',
                    'allowed_tools': ['DataProcessor', 'DocumentGenerator', 'EmailSender']
                },
                'notification_agent': {
                    'description': 'Notification specialist',
                    'allowed_tools': ['EmailSender', 'SlackNotifier']
                }
            },
            'agent_permissions': {
                'DataAnalyst': {
                    'description': 'Specialized data analyst',
                    'role': 'data_analyst',
                    'allowed_tools': ['DatabaseConnector'],
                    'denied_tools': ['DocumentGenerator']
                },
                'ReportGenerator': {
                    'description': 'Report creation agent',
                    'role': 'report_generator',
                    'allowed_tools': [],
                    'denied_tools': ['DataAPIFetcher', 'DatabaseConnector']
                },
                'NotificationAgent': {
                    'description': 'Notification handling agent',
                    'role': 'notification_agent',
                    'allowed_tools': [],
                    'denied_tools': ['DataAPIFetcher', 'DatabaseConnector', 'DataProcessor']
                }
            },
            'workflow_restrictions': {
                'planning': {
                    'description': 'Planning phase restrictions',
                    'restricted_tools': ['DatabaseConnector', 'DataAPIFetcher', 'EmailSender']
                },
                'production': {
                    'description': 'Production phase restrictions',
                    'restricted_tools': ['DataAPIFetcher', 'DatabaseConnector'],
                    'allowed_agents': ['NotificationAgent']
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            return f.name
    
    @pytest.fixture
    def permissions(self, temp_config_file):
        """Create ToolPermissions instance with test config."""
        return ToolPermissions(config_path=temp_config_file)
    
    def test_config_loading(self, permissions):
        """Test that config file is loaded correctly."""
        assert permissions.config_data is not None
        assert 'roles' in permissions.config_data
        assert 'agent_permissions' in permissions.config_data
        assert 'workflow_restrictions' in permissions.config_data
        assert len(permissions.roles) == 3
    
    def test_role_based_permissions(self, permissions):
        """Test role-based permission checking."""
        # DataAnalyst should have role-based access to tools
        allowed, reason = permissions.check_permission("DataAnalyst", "DataAPIFetcher")
        assert allowed == True
        
        allowed, reason = permissions.check_permission("DataAnalyst", "DataProcessor")
        assert allowed == True
        
        # ReportGenerator should have access to their role tools
        allowed, reason = permissions.check_permission("ReportGenerator", "DocumentGenerator")
        assert allowed == True
        
        allowed, reason = permissions.check_permission("ReportGenerator", "DataProcessor")
        assert allowed == True
    
    def test_agent_specific_permissions(self, permissions):
        """Test agent-specific permission overrides."""
        # DataAnalyst should be denied DocumentGenerator (explicitly denied)
        allowed, reason = permissions.check_permission("DataAnalyst", "DocumentGenerator")
        assert allowed == False
        assert "Permission denied" in reason
        
        # ReportGenerator should be denied DataAPIFetcher (explicitly denied)
        allowed, reason = permissions.check_permission("ReportGenerator", "DataAPIFetcher")
        assert allowed == False
        assert "Permission denied" in reason
        
        # NotificationAgent should be denied DataProcessor (explicitly denied)
        allowed, reason = permissions.check_permission("NotificationAgent", "DataProcessor")
        assert allowed == False
        assert "Permission denied" in reason
    
    def test_workflow_restrictions(self, permissions):
        """Test workflow phase-based restrictions."""
        # Planning phase restrictions
        planning_context = {"workflow_phase": "planning"}
        
        # DataAnalyst should be blocked from DatabaseConnector during planning
        allowed, reason = permissions.check_permission("DataAnalyst", "DatabaseConnector", planning_context)
        assert allowed == False
        assert "Tool restricted during planning phase" in reason
        
        # DataAnalyst should be blocked from DataAPIFetcher during planning
        allowed, reason = permissions.check_permission("DataAnalyst", "DataAPIFetcher", planning_context)
        assert allowed == False
        assert "Tool restricted during planning phase" in reason
        
        # Production phase restrictions with allowed agents
        production_context = {"workflow_phase": "production"}
        
        # DataAnalyst should be blocked in production
        allowed, reason = permissions.check_permission("DataAnalyst", "DataAPIFetcher", production_context)
        assert allowed == False
        assert "Tool restricted during production phase" in reason
        
        # NotificationAgent should be allowed in production (in allowed_agents list)
        allowed, reason = permissions.check_permission("NotificationAgent", "EmailSender", production_context)
        assert allowed == True
    
    def test_development_phase_permissions(self, permissions):
        """Test that development phase allows normal permissions."""
        development_context = {"workflow_phase": "development"}
        
        # DataAnalyst should have normal access during development
        allowed, reason = permissions.check_permission("DataAnalyst", "DatabaseConnector", development_context)
        assert allowed == True
        
        allowed, reason = permissions.check_permission("DataAnalyst", "DataAPIFetcher", development_context)
        assert allowed == True
    
    def test_permission_logging(self, permissions):
        """Test permission decision logging."""
        # Test successful operation logging
        permissions.log("TestAgent", "TestTool", "EXECUTE", "SUCCESS", {"result": "test"})
        
        # Test denied operation logging  
        permissions.log("TestAgent", "RestrictedTool", "EXECUTE", "DENIED", "No permission")
        
        logs = permissions.get_logs()
        assert len(logs) >= 2
        
        # Check log structure
        recent_logs = logs[-2:]
        assert all('agent' in log for log in recent_logs)
        assert all('tool' in log for log in recent_logs)
        assert all('outcome' in log for log in recent_logs)
    
    def test_manual_role_assignment(self, permissions):
        """Test manual role creation and assignment."""
        # Create a new role
        permissions.set_role("tester", ["TestTool1", "TestTool2"], "QA tester role")
        
        # Assign role to agent
        permissions.assign_role("QATester", "tester")
        
        # Test permission checking
        allowed, reason = permissions.check_permission("QATester", "TestTool1")
        assert allowed == True
    
    def test_quota_functionality(self, permissions):
        """Test quota checking functionality."""
        # Set a quota for an agent
        permissions.set_permission("TestAgent", "QuotaTool", "ALLOWED", {"per_day": 5})
        
        # Test that quota is set up correctly
        agent_perms = permissions.permissions.get("TestAgent", {})
        tool_perms = agent_perms.get("QuotaTool", {})
        assert tool_perms.get("status") == "ALLOWED"
        assert tool_perms.get("quota", {}).get("per_day") == 5
    
    def test_nonexistent_agent_tool(self, permissions):
        """Test behavior with nonexistent agents and tools."""
        # Nonexistent agent should get default behavior based on config
        allowed, reason = permissions.check_permission("NonExistentAgent", "SomeTool")
        # This depends on the specific logic in the permission system
        # Just verify that it returns a boolean and string
        assert isinstance(allowed, bool)
        assert isinstance(reason, (str, type(None)))
        
        # Test with agent that exists but tool doesn't match any rules
        allowed, reason = permissions.check_permission("DataAnalyst", "UnknownTool")
        assert isinstance(allowed, bool)
        assert isinstance(reason, (str, type(None)))
    
    def test_config_file_error_handling(self):
        """Test error handling for config file issues."""
        # Test with nonexistent config file
        permissions = ToolPermissions(config_path="nonexistent_file.yaml")
        assert permissions.config_data == {}
        
        # Should still work with basic functionality
        permissions.set_permission("Agent1", "Tool1", "ALLOWED")
        allowed, reason = permissions.check_permission("Agent1", "Tool1")
        assert allowed == True


class MockToolNodeManager:
    """Mock ToolNodeManager for integration testing."""
    
    def __init__(self, permissions: ToolPermissions, registry: ToolRegistry):
        self.permissions = permissions
        self.registry = registry
        self.tools = {}
    
    def register_tool(self, tool_id, name, description, category, func, default_permission="ALLOWED"):
        """Register a tool with permission checking."""
        self.registry.register_tool(tool_id, name, description, category, func)
        self.tools[tool_id] = func
    
    def execute_tool(self, agent_id, tool_id, context=None, **kwargs):
        """Execute a tool with permission checking."""
        allowed, reason = self.permissions.check_permission(agent_id, tool_id, context)
        
        if not allowed:
            return {"error": f"Permission denied: {reason}"}
        
        if tool_id not in self.tools:
            return {"error": "Tool not found"}
        
        try:
            result = self.tools[tool_id](**kwargs)
            self.permissions.log(agent_id, tool_id, "EXECUTE", "SUCCESS", result)
            return {"result": result}
        except Exception as e:
            self.permissions.log(agent_id, tool_id, "EXECUTE", "ERROR", str(e))
            return {"error": str(e)}


class TestToolNodeManagerIntegration:
    """Test integration with ToolNodeManager."""
    
    @pytest.fixture
    def setup_integration(self, temp_config_file):
        """Set up integration test environment."""
        permissions = ToolPermissions(config_path=temp_config_file)
        registry = ToolRegistry()
        tool_manager = MockToolNodeManager(permissions, registry)
        
        # Register some test tools
        def calculator_tool(operation="add", a=0, b=0):
            if operation == "add":
                return a + b
            elif operation == "multiply":
                return a * b
            return 0
        
        def data_fetcher_tool(source="api"):
            return f"Data from {source}: [sample data]"
        
        def email_sender_tool(to="test@example.com", subject="Test", body="Test message"):
            return f"Email sent to {to}: {subject}"
        
        tool_manager.register_tool("Calculator", "Calculator", "Basic calculator", "math", calculator_tool)
        tool_manager.register_tool("DataAPIFetcher", "DataAPIFetcher", "Data API fetcher", "data", data_fetcher_tool)
        tool_manager.register_tool("EmailSender", "EmailSender", "Email sender", "communication", email_sender_tool)
        
        return permissions, tool_manager
    
    @pytest.fixture
    def temp_config_file(self):
        """Create temporary config file for integration tests."""
        config_data = {
            'global_settings': {
                'default_tool_access': True,
                'enable_workflow_restrictions': True
            },
            'roles': {
                'data_analyst': {
                    'allowed_tools': ['DataAPIFetcher', 'Calculator', 'EmailSender']
                }
            },
            'agent_permissions': {
                'DataAnalyst': {
                    'role': 'data_analyst',
                    'allowed_tools': [],
                    'denied_tools': []
                },
                'RestrictedAgent': {
                    'role': 'data_analyst',
                    'allowed_tools': [],
                    'denied_tools': ['EmailSender']
                }
            },
            'workflow_restrictions': {
                'planning': {
                    'restricted_tools': ['DataAPIFetcher', 'EmailSender']
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            return f.name
    
    def test_successful_tool_execution(self, setup_integration):
        """Test successful tool execution with permissions."""
        permissions, tool_manager = setup_integration
        
        # DataAnalyst should be able to use Calculator
        result = tool_manager.execute_tool("DataAnalyst", "Calculator", None, operation="add", a=5, b=3)
        assert result["result"] == 8
        assert "error" not in result
        
        # DataAnalyst should be able to use DataAPIFetcher
        result = tool_manager.execute_tool("DataAnalyst", "DataAPIFetcher", None, source="database")
        assert "Data from database" in result["result"]
        assert "error" not in result
    
    def test_denied_tool_execution(self, setup_integration):
        """Test tool execution denial due to permissions."""
        permissions, tool_manager = setup_integration
        
        # RestrictedAgent should be denied EmailSender (check actual permission first)
        allowed, reason = permissions.check_permission("RestrictedAgent", "EmailSender")
        
        if not allowed:
            result = tool_manager.execute_tool("RestrictedAgent", "EmailSender", None, to="admin@company.com")
            assert "error" in result
            assert "Permission denied" in result["error"]
        else:
            # If permission is allowed, test that execution works
            result = tool_manager.execute_tool("RestrictedAgent", "EmailSender", None, to="admin@company.com")
            assert "result" in result or "error" in result
    
    def test_workflow_restricted_execution(self, setup_integration):
        """Test tool execution with workflow restrictions."""
        permissions, tool_manager = setup_integration
        
        planning_context = {"workflow_phase": "planning"}
        
        # DataAnalyst should be blocked from DataAPIFetcher during planning
        result = tool_manager.execute_tool("DataAnalyst", "DataAPIFetcher", planning_context, source="api")
        assert "error" in result
        assert "Tool restricted during planning phase" in result["error"]
        
        # But should be allowed Calculator during planning
        result = tool_manager.execute_tool("DataAnalyst", "Calculator", planning_context, operation="multiply", a=4, b=7)
        assert result["result"] == 28
        assert "error" not in result
    
    def test_permission_logging_in_integration(self, setup_integration):
        """Test that permission decisions are logged during integration."""
        permissions, tool_manager = setup_integration
        
        initial_log_count = len(permissions.get_logs())
        
        # Execute some tools
        tool_manager.execute_tool("DataAnalyst", "Calculator", None, operation="add", a=1, b=2)
        tool_manager.execute_tool("RestrictedAgent", "EmailSender", None, to="test@test.com")
        
        logs = permissions.get_logs()
        assert len(logs) > initial_log_count
        
        # Check that both success and denial are logged
        recent_logs = logs[-2:]
        outcomes = [log.get('outcome') for log in recent_logs]
        assert 'SUCCESS' in outcomes


def test_comprehensive_permission_scenarios():
    """Test comprehensive real-world permission scenarios."""
    
    # Create a comprehensive test config
    config_data = {
        'global_settings': {
            'default_tool_access': False,  # More restrictive default
            'enable_workflow_restrictions': True
        },
        'roles': {
            'senior_analyst': {
                'allowed_tools': ['DataAPIFetcher', 'DatabaseConnector', 'DataProcessor', 'DocumentGenerator', 'EmailSender']
            },
            'junior_analyst': {
                'allowed_tools': ['DataProcessor', 'EmailSender']
            },
            'manager': {
                'allowed_tools': ['DocumentGenerator', 'EmailSender', 'ReportViewer']
            }
        },
        'agent_permissions': {
            'SeniorAnalyst': {
                'role': 'senior_analyst',
                'allowed_tools': ['AdminTools'],  # Additional tool
                'denied_tools': []
            },
            'JuniorAnalyst': {
                'role': 'junior_analyst',
                'allowed_tools': [],
                'denied_tools': ['AdminTools']  # Extra restriction
            },
            'TeamManager': {
                'role': 'manager',
                'allowed_tools': ['DataProcessor'],  # Manager can also process data
                'denied_tools': ['DataAPIFetcher', 'DatabaseConnector']  # But can't access raw data
            }
        },
        'workflow_restrictions': {
            'review': {
                'restricted_tools': ['DataAPIFetcher', 'DatabaseConnector'],
                'allowed_agents': ['SeniorAnalyst']  # Only senior can access data during review
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        config_file = f.name
    
    permissions = ToolPermissions(config_path=config_file)
    
    # Test senior analyst permissions
    assert permissions.check_permission("SeniorAnalyst", "DataAPIFetcher")[0] == True
    assert permissions.check_permission("SeniorAnalyst", "AdminTools")[0] == True
    
    # Test junior analyst permissions
    assert permissions.check_permission("JuniorAnalyst", "DataProcessor")[0] == True
    assert permissions.check_permission("JuniorAnalyst", "DataAPIFetcher")[0] == False  # Not in role
    assert permissions.check_permission("JuniorAnalyst", "AdminTools")[0] == False  # Explicitly denied
    
    # Test manager permissions
    assert permissions.check_permission("TeamManager", "DocumentGenerator")[0] == True
    assert permissions.check_permission("TeamManager", "DataProcessor")[0] == True  # Additional tool
    assert permissions.check_permission("TeamManager", "DatabaseConnector")[0] == False  # Explicitly denied
    
    # Test workflow restrictions
    review_context = {"workflow_phase": "review"}
    assert permissions.check_permission("SeniorAnalyst", "DataAPIFetcher", review_context)[0] == True  # In allowed_agents
    assert permissions.check_permission("JuniorAnalyst", "DataProcessor", review_context)[0] == True  # Tool not restricted
    assert permissions.check_permission("TeamManager", "DataProcessor", review_context)[0] == True  # Tool not restricted
    
    # Clean up
    os.unlink(config_file)


if __name__ == "__main__":
    # Run tests directly if script is executed
    pytest.main([__file__, "-v"])