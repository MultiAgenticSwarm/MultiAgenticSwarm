"""
Shared test fixtures and configuration for multiagenticswarm test suite.
"""

import pytest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from multiagenticswarm.core.base_tool import BaseTool, ToolCallRequest, ToolCallResponse


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture  
def mock_llm_provider():
    """Mock LLM provider for testing."""
    provider = Mock()
    
    async def mock_execute(messages, **kwargs):
        return Mock(content="Test response", tool_calls=[])
    
    provider.execute = AsyncMock(side_effect=mock_execute)
    provider.extract_tool_calls.return_value = []
    return provider


@pytest.fixture
def mock_get_llm_provider(mock_llm_provider):
    """Mock the get_llm_provider function."""
    with patch('multiagenticswarm.core.agent.get_llm_provider') as mock:
        mock.return_value = mock_llm_provider
        yield mock


class MockTool(BaseTool):
    """Mock tool for testing purposes."""
    
    def __init__(self, name: str, description: str = "Mock tool", should_fail: bool = False, delay: float = 0):
        super().__init__(name, description) 
        self.should_fail = should_fail
        self.delay = delay
        self.call_count = 0
        
    def _execute_impl(self, request: ToolCallRequest) -> ToolCallResponse:
        """Execute the mock tool."""
        import time
        if self.delay > 0:
            time.sleep(self.delay)
            
        self.call_count += 1
        
        if self.should_fail:
            return ToolCallResponse(
                id=request.id,
                name=request.name,
                result=None,
                success=False,
                error="Mock tool failure",
                execution_time=0.001
            )
        
        return ToolCallResponse(
            id=request.id,
            name=request.name,
            result=f"Mock result from {self.name}",
            success=True,
            error=None,
            execution_time=0.001
        )


class ExceptionTool(BaseTool):
    """Tool that raises exceptions for testing."""
    
    def __init__(self, name: str, description: str = "Exception tool"):
        super().__init__(name, description)
        
    def _execute_impl(self, request: ToolCallRequest) -> ToolCallResponse:
        """Always raises an exception."""
        raise RuntimeError("Test exception")


@pytest.fixture
def mock_tool():
    """Create a mock tool for testing."""
    return MockTool("test_tool")


@pytest.fixture
def exception_tool():
    """Create an exception tool for testing."""
    return ExceptionTool("exception_tool")


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        "agents": [
            {
                "name": "TestAgent",
                "description": "Test agent",
                "llm_provider": "openai",
                "llm_model": "gpt-3.5-turbo"
            }
        ],
        "tools": [
            {
                "name": "TestTool",
                "description": "Test tool",
                "scope": "global"
            }
        ],
        "tasks": [
            {
                "name": "TestTask", 
                "description": "Test task",
                "steps": []
            }
        ]
    }


@pytest.fixture(autouse=True)
def mock_api_keys():
    """Mock API keys for testing."""
    with patch.dict(os.environ, {
        'OPENAI_API_KEY': 'test-openai-key',
        'ANTHROPIC_API_KEY': 'test-anthropic-key',
        'AWS_ACCESS_KEY_ID': 'test-aws-key',
        'AWS_SECRET_ACCESS_KEY': 'test-aws-secret'
    }):
        yield


@pytest.fixture
def mock_file_system(temp_dir):
    """Mock file system operations."""
    config_file = Path(temp_dir) / "test_config.yaml"
    config_file.write_text("""
agents:
  - name: TestAgent
    description: Test agent
    llm_provider: openai
    llm_model: gpt-3.5-turbo
    
tools:
  - name: TestTool
    description: Test tool
    scope: global
    
tasks:
  - name: TestTask
    description: Test task
    steps: []
""")
    
    return {
        "config_file": str(config_file),
        "temp_dir": temp_dir
    }


# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)


@pytest.fixture(scope="session")
def event_loop_policy():
    """Set the event loop policy for the test session."""
    import asyncio
    return asyncio.DefaultEventLoopPolicy()


# Mock logging to prevent log file creation during tests
@pytest.fixture(autouse=True)
def mock_logging():
    """Mock logging setup to prevent file creation during tests."""
    with patch('multiagenticswarm.utils.logger.setup_comprehensive_logging'):
        with patch('multiagenticswarm.utils.logger.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_logger.info = Mock()
            mock_logger.debug = Mock()
            mock_logger.warning = Mock()
            mock_logger.error = Mock()
            mock_logger.critical = Mock()
            mock_get_logger.return_value = mock_logger
            yield mock_logger
