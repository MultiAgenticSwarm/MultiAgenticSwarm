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
from multiagenticswarm.core.agent import Agent

class FlutterTesterAgent(AbstractTesterAgent, Agent):
    """
    Flutter tester agent - ALL testing knowledge comes from LLM.
    No hardcoded testing patterns - all knowledge comes from LLM.
    """

    def __init__(self, name: str = "flutter_tester", working_directory: str = ".", **kwargs):
        self.working_directory = working_directory
        super().__init__(name=name, **kwargs)

        # Initialize tools
        self.flutter_cli = FlutterCLITool(working_directory)
        self.dart_cli = DartCLITool(working_directory)
        self.file_system = FileSystemTool(working_directory)

        self.logger = logging.getLogger(f"flutterswarm.{name}")

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

    def _get_tools(self) -> List[Any]:
        """Get tools for testing"""
        return [
            mas.Tool(
                name="flutter_cli",
                description="Execute Flutter CLI commands",
                function=self.flutter_cli.execute
            ),
            mas.Tool(
                name="dart_cli",
                description="Execute Dart CLI commands",
                function=self.dart_cli.execute
            ),
            mas.Tool(
                name="file_system",
                description="File system operations",
                function=self.file_system._execute_wrapper
            )
        ]

    async def create_test_plan(
        self,
        requirements: str,
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Create a comprehensive test plan using LLM analysis.
        """

        # Get current project structure
        project_structure = await self.file_system.list_directory(
            path=self.working_directory,
            recursive=True
        )

        # Read existing test files
        test_files = []
        for file in project_structure.get('files', []):
            if 'test' in file and file.endswith('.dart'):
                test_content = await self.file_system.read_file(file)
                if test_content.get('success'):
                    test_files.append({
                        'path': file,
                        'content': test_content['content']
                    })

        test_plan_prompt = f"""
Create a comprehensive test plan for these requirements:
{requirements}

Current project context:
- Project structure: {project_structure.get('files', []) if project_structure.get('success') else 'New project'}
- Existing tests: {test_files if test_files else 'None'}
- Project context: {context.__dict__ if context else 'None'}

Create a detailed test plan:

1. TEST_ANALYSIS: Analyze requirements and identify testing needs
2. TEST_STRATEGY: Define overall testing approach and methodology
3. TEST_CATEGORIES: Break down into unit, widget, and integration tests
4. TEST_SCENARIOS: Define specific test scenarios and cases
5. TEST_DATA: Plan test data requirements
6. TEST_ENVIRONMENT: Define test environment setup
7. COVERAGE_GOALS: Set test coverage targets
8. AUTOMATION_STRATEGY: Plan test automation approach
9. RISK_ASSESSMENT: Identify testing risks and mitigation
10. EXECUTION_PLAN: Plan test execution and reporting

For each test category, provide:
- Specific test cases to implement
- Testing techniques to use
- Mock requirements
- Expected outcomes
- Priority levels

Consider:
- Widget testing for UI components
- Unit testing for business logic
- Integration testing for full flows
- Performance testing requirements
- Accessibility testing needs
- Error handling scenarios
- Edge cases and boundary conditions

Base all decisions on Flutter testing best practices and your expertise.
"""

        return await self.execute(test_plan_prompt, context)

    async def write_tests(
        self,
        code_path: str,
        test_types: List[str],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Write tests for the given code using LLM decisions.
        """

        # Read the code to test
        code_content = await self.file_system.read_file(code_path)

        if not code_content.get('success'):
            return ExecutionResult(
                success=False,
                agent_name=self.name,
                task_id=f"write_tests_{len(self.execution_history)}",
                error_message=f"Could not read code file: {code_path}"
            )

        write_tests_prompt = f"""
Write comprehensive tests for this Flutter code:

Code file: {code_path}
Code content:
{code_content['content']}

Test types to implement: {test_types}
Project context: {context.__dict__ if context else 'None'}

Create:
1. TEST_ANALYSIS: Analyze the code and identify testing requirements
2. TEST_DESIGN: Design test structure and organization
3. UNIT_TESTS: Write unit tests for business logic
4. WIDGET_TESTS: Write widget tests for UI components
5. INTEGRATION_TESTS: Write integration tests for full flows
6. MOCK_SETUP: Create necessary mocks and test doubles
7. TEST_DATA: Define test data and fixtures
8. ASSERTIONS: Implement comprehensive assertions

For each test:
- Clear test descriptions
- Proper setup and teardown
- Comprehensive assertions
- Edge case coverage
- Error condition testing
- Performance considerations

Use Flutter testing best practices:
- follow test naming conventions
- Use appropriate testing utilities
- Implement proper test organization
- Include both positive and negative tests
- Test widget interactions and state changes
- Mock external dependencies appropriately

Generate complete, runnable test files.
"""

        test_result = await self.execute(write_tests_prompt, context)

        if not test_result.success:
            return test_result

        # Extract test files from response
        test_files = self._extract_test_files_from_response(test_result.output)

        created_files = []

        # Create test files
        for test_file in test_files:
            result = await self.file_system.write_file(
                path=test_file['path'],
                content=test_file['content'],
                create_dirs=True
            )

            if result.get('success'):
                created_files.append(test_file['path'])
                self.logger.info(f"Created test file: {test_file['path']}")

        return ExecutionResult(
            success=True,
            agent_name=self.name,
            task_id=f"write_tests_{len(self.execution_history)}",
            output={
                'test_analysis': test_result.output,
                'created_files': created_files,
                'test_files': test_files
            },
            created_files=created_files,
            next_steps=[
                "Review generated tests",
                "Run tests to verify they pass",
                "Check test coverage",
                "Add additional edge case tests if needed"
            ]
        )

    async def run_tests(
        self,
        test_suite: str,
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Run tests and analyze results using LLM.
        """

        # Run the tests
        test_result = await self.flutter_cli.test(test_file=test_suite if test_suite != "all" else None, coverage=True)

        if not test_result.get('success'):
            return ExecutionResult(
                success=False,
                agent_name=self.name,
                task_id=f"run_tests_{len(self.execution_history)}",
                error_message=f"Test execution failed: {test_result.get('stderr', 'Unknown error')}"
            )

        # Analyze test results with LLM
        analysis_prompt = f"""
Analyze these Flutter test results:

Test suite: {test_suite}
Test output:
{test_result.get('stdout', '')}

Error output:
{test_result.get('stderr', '')}

Project context: {context.__dict__ if context else 'None'}

Provide:
1. RESULTS_SUMMARY: Summarize test results
2. PASSED_TESTS: List of tests that passed
3. FAILED_TESTS: List of tests that failed with reasons
4. COVERAGE_ANALYSIS: Analyze test coverage
5. PERFORMANCE_INSIGHTS: Identify performance issues
6. RECOMMENDATIONS: Recommend improvements
7. NEXT_STEPS: Suggest next actions

Consider:
- Test success/failure rates
- Test execution time
- Code coverage metrics
- Common failure patterns
- Performance bottlenecks
- Test reliability issues

Provide actionable insights and recommendations.
"""

        analysis_result = await self.execute(analysis_prompt, context)

        return ExecutionResult(
            success=True,
            agent_name=self.name,
            task_id=f"run_tests_{len(self.execution_history)}",
            output={
                'test_results': test_result,
                'analysis': analysis_result.output if analysis_result.success else "Analysis failed",
                'test_suite': test_suite
            },
            next_steps=[
                "Review test results and analysis",
                "Fix any failing tests",
                "Improve test coverage if needed",
                "Address performance issues identified"
            ]
        )

    async def analyze_test_results(
        self,
        test_results: Dict[str, Any],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Analyze test results and provide insights.
        """

        analysis_prompt = f"""
Analyze these comprehensive test results:
{test_results}

Project context: {context.__dict__ if context else 'None'}

Provide detailed analysis:
1. OVERALL_HEALTH: Overall test suite health assessment
2. FAILURE_ANALYSIS: Detailed analysis of test failures
3. COVERAGE_ANALYSIS: Code coverage analysis and gaps
4. PERFORMANCE_ANALYSIS: Test performance insights
5. RELIABILITY_ANALYSIS: Test reliability and flakiness
6. TRENDS: Identify trends in test results
7. RECOMMENDATIONS: Specific recommendations for improvement
8. ACTION_ITEMS: Prioritized action items

Consider:
- Test failure patterns and root causes
- Code coverage gaps and missing tests
- Test execution performance
- Test maintenance requirements
- Risk assessment based on test results

Provide actionable insights for improving test quality and coverage.
"""

        return await self.execute(analysis_prompt, context)

    async def generate_test_data(
        self,
        data_requirements: Dict[str, Any],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Generate test data using LLM.
        """

        test_data_prompt = f"""
Generate comprehensive test data for these requirements:
{data_requirements}

Project context: {context.__dict__ if context else 'None'}

Create:
1. DATA_ANALYSIS: Analyze data requirements
2. DATA_STRATEGY: Plan test data approach
3. TEST_DATA_MODELS: Define data models and structures
4. SAMPLE_DATA: Generate sample test data
5. DATA_BUILDERS: Create test data builders and factories
6. FIXTURES: Create test fixtures and datasets
7. DATA_VALIDATION: Validate test data quality

Generate:
- Mock data for different scenarios
- Edge case data for boundary testing
- Invalid data for error testing
- Performance test data for load testing
- Realistic data for integration testing

Ensure test data is:
- Comprehensive and covers all scenarios
- Realistic and representative
- Easy to maintain and update
- Efficient for test execution
- Secure and privacy-compliant

Provide complete test data implementation.
"""

        return await self.execute(test_data_prompt, context)

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
