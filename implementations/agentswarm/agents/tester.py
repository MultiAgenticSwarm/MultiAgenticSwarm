"""
Abstract tester agent interface.
All testing logic comes from LLMs - no hardcoded test patterns.
"""

from abc import abstractmethod
from typing import Dict, Any, List, Optional
from ..core.base import BaseAgent
from ..core.types import AgentRole, TaskContext, ExecutionResult

class AbstractTesterAgent(BaseAgent):
    """
    Abstract tester agent that uses LLM for ALL testing decisions.
    No hardcoded testing patterns - all knowledge comes from LLM.
    """

    def __init__(self, name: str, system: Optional[Any] = None, **kwargs):
        super().__init__(
            name=name,
            role=AgentRole.TESTER,
            system=system,
            **kwargs
        )

    def _get_specialized_instructions(self) -> str:
        """Base tester instructions"""
        return """You are an expert software tester responsible for:

- Creating comprehensive test strategies
- Writing unit, integration, and end-to-end tests
- Performing manual testing when needed
- Analyzing test results and identifying issues
- Ensuring code quality and reliability
- Setting up test environments and data

Testing principles:
- Test early and often
- Cover edge cases and error conditions
- Use appropriate testing frameworks
- Maintain test code quality
- Provide clear test documentation
- Ensure tests are maintainable

Types of testing you handle:
- Unit tests for individual components
- Integration tests for component interactions
- End-to-end tests for full workflows
- Performance tests for scalability
- Security tests for vulnerabilities
- Usability tests for user experience

Always explain your testing strategy and provide detailed results.
"""

    @abstractmethod
    async def create_test_plan(
        self,
        requirements: str,
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Create a comprehensive test plan using LLM analysis.

        Args:
            requirements: Requirements to test
            context: Additional context

        Returns:
            ExecutionResult with test plan
        """
        pass

    @abstractmethod
    async def write_tests(
        self,
        code_path: str,
        test_types: List[str],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Write tests for the given code using LLM decisions.

        Args:
            code_path: Path to code to test
            test_types: Types of tests to write
            context: Additional context

        Returns:
            ExecutionResult with test implementation
        """
        pass

    @abstractmethod
    async def run_tests(
        self,
        test_suite: str,
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Run tests and analyze results using LLM.

        Args:
            test_suite: Test suite to run
            context: Additional context

        Returns:
            ExecutionResult with test results and analysis
        """
        pass

    @abstractmethod
    async def analyze_test_results(
        self,
        test_results: Dict[str, Any],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Analyze test results and provide insights.

        Args:
            test_results: Test execution results
            context: Additional context

        Returns:
            ExecutionResult with analysis and recommendations
        """
        pass

    @abstractmethod
    async def generate_test_data(
        self,
        data_requirements: Dict[str, Any],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Generate test data using LLM.

        Args:
            data_requirements: Requirements for test data
            context: Additional context

        Returns:
            ExecutionResult with generated test data
        """
        pass
