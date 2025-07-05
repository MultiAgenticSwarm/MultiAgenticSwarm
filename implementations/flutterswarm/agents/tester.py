"""
FlutterTesterAgent - ALL testing knowledge comes from LLM.
No hardcoded testing patterns or frameworks.
"""

from typing import Dict, Any, List, Optional
import logging

from implementations.agentswarm.agents import AbstractTesterAgent
from implementations.agentswarm.core.types import TaskContext, ExecutionResult
from ..tools import FlutterCLITool, DartCLITool, FileSystemTool

# Import MAS as the core SDK
import multiagenticswarm as mas

class FlutterTesterAgent(AbstractTesterAgent):
    """
    Flutter tester agent - ALL testing knowledge comes from LLM.
    No hardcoded testing patterns - all knowledge comes from LLM.
    """

    def __init__(self, name: str = "flutter_tester", working_directory: str = ".", **kwargs):
        self.working_directory = working_directory

        # Initialize tools first
        self.flutter_cli = FlutterCLITool(working_directory)
        self.dart_cli = DartCLITool(working_directory)
        self.file_system = FileSystemTool(working_directory)

        # Initialize with proper MAS integration
        super().__init__(
            name=name,
            system=kwargs.get('system'),
            llm_provider=kwargs.get('llm_provider', 'openai'),
            llm_model=kwargs.get('llm_model', 'gpt-4'),
            **{k: v for k, v in kwargs.items() if k not in ['system', 'llm_provider', 'llm_model']}
        )

        self.logger = mas.get_logger(f"flutterswarm.{name}")
        self.logger.info(f"Initialized FlutterTesterAgent: {name}")

    def _get_specialized_instructions(self) -> str:
        """Flutter testing specific instructions"""
        return """You are an expert Flutter tester with comprehensive knowledge of:

FLUTTER TESTING FRAMEWORK:
- flutter_test package and testing utilities
- Widget testing with WidgetTester
- Unit testing for business logic
- Integration testing for full app flows
- Golden tests for UI consistency
- Performance testing and profiling

TESTING PATTERNS:
- Test-driven development (TDD)
- Behavior-driven development (BDD)
- Arrange-Act-Assert pattern
- Given-When-Then scenarios
- Mock objects and test doubles
- Test fixtures and setup/teardown

WIDGET TESTING:
- Widget tree testing and verification
- User interaction simulation (tap, scroll, input)
- Widget finding and matching
- State verification and assertion
- Animation testing
- Platform-specific widget testing

UNIT TESTING:
- Business logic testing
- Model and data class testing
- Service and repository testing
- Utility function testing
- State management testing
- Error handling testing

INTEGRATION TESTING:
- Full app flow testing
- Navigation testing
- API integration testing
- Database integration testing
- Platform integration testing
- End-to-end scenarios

MOCKING AND TESTING UTILITIES:
- Mockito for mocking dependencies
- HTTP mocking for API tests
- Database mocking for data tests
- Platform channel mocking
- SharedPreferences mocking
- Custom mock implementations

TEST ORGANIZATION:
- Test file structure and naming
- Test grouping and organization
- Test data management
- Test environment setup
- Continuous integration setup
- Test reporting and coverage

PERFORMANCE TESTING:
- Widget performance testing
- Memory usage testing
- CPU usage profiling
- Network performance testing
- Animation performance testing
- App startup time testing

ACCESSIBILITY TESTING:
- Semantic testing for screen readers
- Focus management testing
- Keyboard navigation testing
- Color contrast testing
- Text scaling testing
- Platform accessibility testing

IMPORTANT INSTRUCTIONS:
1. Use your comprehensive testing knowledge to create thorough test suites
2. Follow Flutter testing best practices and conventions
3. Write clear, maintainable, and reliable tests
4. Ensure good test coverage across all code paths
5. Include both positive and negative test cases
6. Test edge cases and error conditions
7. Use appropriate testing patterns and frameworks
8. Optimize tests for speed and reliability

When creating tests:
- Analyze code to identify testable components
- Design comprehensive test scenarios
- Choose appropriate testing techniques
- Implement robust test assertions
- Include setup and teardown procedures
- Consider test data requirements
- Plan for test maintenance and updates

You have access to Flutter CLI, Dart CLI, and file system tools.
Use these to implement and run your tests.
"""

    def _get_tools(self) -> List[Dict[str, Any]]:
        """Get tools for this agent"""
        return [
            {
                "name": "flutter_cli",
                "func": self.flutter_cli.execute,
                "description": "Execute Flutter CLI commands",
                "scope": "local"
            },
            {
                "name": "dart_cli",
                "func": self.dart_cli.execute,
                "description": "Execute Dart CLI commands",
                "scope": "local"
            },
            {
                "name": "file_system",
                "func": self.file_system.execute,
                "description": "Execute file system operations (read, write, list, mkdir, etc.)",
                "scope": "local"
            }
        ]

    async def create_test_plan(
        self,
        requirements: str,
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """Create a comprehensive test plan using LLM analysis"""
        task = f"""
        Create a comprehensive test plan for Flutter application with these requirements:
        {requirements}

        Include:
        1. Unit tests for business logic
        2. Widget tests for UI components
        3. Integration tests for full flows
        4. Performance tests
        5. Accessibility tests
        6. Platform-specific tests

        For each test category, specify:
        - Test scenarios
        - Test data needed
        - Expected outcomes
        - Test priority
        - Implementation approach
        """

        return await self.execute(task, context)

    async def write_tests(
        self,
        code_path: str,
        test_types: List[str],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """Write tests for the given code using LLM decisions"""
        task = f"""
        Write comprehensive Flutter tests for the code at: {code_path}

        Test types to implement: {test_types}

        For each test type:
        1. Analyze the code structure
        2. Identify test scenarios
        3. Create test files with proper organization
        4. Write clear, maintainable test code
        5. Include edge cases and error scenarios
        6. Use appropriate Flutter testing patterns

        Follow Flutter testing best practices:
        - Use flutter_test package
        - Implement proper test fixtures
        - Use meaningful test descriptions
        - Include setup and teardown when needed
        - Mock external dependencies
        """

        return await self.execute(task, context)

    async def run_tests(
        self,
        test_suite: str,
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """Run tests and analyze results using LLM"""
        task = f"""
        Run Flutter tests for: {test_suite}

        1. Execute the test suite using flutter test
        2. Analyze test results
        3. Identify failures and their causes
        4. Provide debugging suggestions
        5. Generate test coverage report
        6. Recommend improvements

        Return:
        - Test execution summary
        - Detailed failure analysis
        - Coverage metrics
        - Performance insights
        - Next steps for fixes
        """

        return await self.execute(task, context)

    async def analyze_test_results(
        self,
        test_results: Dict[str, Any],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """Analyze test results and provide insights"""
        task = f"""
        Analyze Flutter test results: {test_results}

        Provide:
        1. Overall test health assessment
        2. Failure pattern analysis
        3. Performance bottleneck identification
        4. Coverage gap analysis
        5. Flaky test detection
        6. Recommendations for improvement

        Focus on:
        - Test stability and reliability
        - Performance implications
        - Code coverage gaps
        - Test maintenance needs
        - CI/CD pipeline impact
        """

        return await self.execute(task, context)

    async def generate_test_data(
        self,
        data_requirements: Dict[str, Any],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """Generate test data using LLM"""
        task = f"""
        Generate test data for Flutter application: {data_requirements}

        Create:
        1. Realistic test fixtures
        2. Mock API responses
        3. Sample user inputs
        4. Edge case data
        5. Performance test data
        6. Error condition data

        Ensure data is:
        - Comprehensive and realistic
        - Covers all test scenarios
        - Maintains data consistency
        - Includes edge cases
        - Properly structured for Flutter tests
        """

        return await self.execute(task, context)

    # Helper methods
    def _extract_test_files_from_response(self, response: str) -> List[Dict[str, str]]:
        """Extract test files from LLM response"""
        files = []

        lines = response.split('\n')
        current_file = None
        current_content = []

        for line in lines:
            if line.strip().startswith('TEST_FILE:') or line.strip().startswith('test/'):
                if current_file:
                    files.append({
                        'path': current_file,
                        'content': '\n'.join(current_content)
                    })

                current_file = line.split(':', 1)[1].strip() if ':' in line else line.strip()
                current_content = []
            elif current_file and line.strip():
                current_content.append(line)

        if current_file:
            files.append({
                'path': current_file,
                'content': '\n'.join(current_content)
            })

        return files
