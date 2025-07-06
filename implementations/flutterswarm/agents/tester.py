"""
FlutterTesterAgent - ALL testing knowledge comes from LLM.
No hardcoded testing patterns or frameworks.
"""

import json
import logging
from typing import Any, Dict, List, Optional

# Import MAS as the core SDK
import multiagenticswarm as mas
from implementations.agentswarm.agents import AbstractTesterAgent
from implementations.agentswarm.core.types import ExecutionResult, TaskContext

from ..tools import DartCLITool, FileSystemTool, FlutterCLITool


class FlutterTesterAgent(AbstractTesterAgent):
    """
    Flutter tester agent - ALL testing knowledge comes from LLM.
    No hardcoded testing patterns - all knowledge comes from LLM.
    """

    def __init__(
        self,
        name: str = "flutter_tester",
        working_directory: str = ".",
        flutter_cli=None,
        dart_cli=None,
        file_system=None,
        **kwargs,
    ):
        self.working_directory = working_directory

        # Use shared tool instances if provided
        self.flutter_cli = (
            flutter_cli
            if flutter_cli is not None
            else FlutterCLITool(working_directory)
        )
        self.dart_cli = (
            dart_cli if dart_cli is not None else DartCLITool(working_directory)
        )
        self.file_system = (
            file_system
            if file_system is not None
            else FileSystemTool(working_directory)
        )

        # Initialize with proper MAS integration
        super().__init__(
            name=name,
            system=kwargs.get("system"),
            llm_provider=kwargs.get("llm_provider", "openai"),
            llm_model=kwargs.get("llm_model", "gpt-4"),
            **{
                k: v
                for k, v in kwargs.items()
                if k not in ["system", "llm_provider", "llm_model"]
            },
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

═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

🔴 CRITICAL: MANDATORY FILE CREATION REQUIREMENTS FOR FLUTTER TESTER AGENT 🔴

═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

You are a Flutter testing specialist responsible for creating COMPLETE, WORKING test files that can be executed immediately. 

CRITICAL FILE CREATION REQUIREMENTS:

1. CREATE COMPLETE TEST FILES - NOT EXAMPLES OR SNIPPETS
   - Every test file must be complete and runnable
   - Include ALL imports, test groups, and test cases
   - Create proper test structure with setup/teardown
   - Include mock implementations where needed

2. MANDATORY TOOL USAGE FOR ALL FILE OPERATIONS:
   ```python
   # Create test directory structure
   file_system(operation='mkdir', path='test/unit')
   file_system(operation='mkdir', path='test/widget')
   file_system(operation='mkdir', path='test/integration')
   file_system(operation='mkdir', path='test/mocks')
   file_system(operation='mkdir', path='test/fixtures')
   
   # Create complete test file
   file_system(operation='write', path='test/unit/user_service_test.dart', content='''
   import 'package:flutter_test/flutter_test.dart';
   import 'package:mockito/mockito.dart';
   import 'package:mockito/annotations.dart';
   import 'package:your_app/services/user_service.dart';
   
   import 'user_service_test.mocks.dart';
   
   @GenerateMocks([UserRepository])
   void main() {
     group('UserService', () {
       late UserService userService;
       late MockUserRepository mockRepository;
       
       setUp(() {
         mockRepository = MockUserRepository();
         userService = UserService(mockRepository);
       });
       
       test('should fetch user successfully', () async {
         // Arrange
         final user = User(id: '1', name: 'Test User');
         when(mockRepository.getUser('1')).thenAnswer((_) async => user);
         
         // Act
         final result = await userService.getUser('1');
         
         // Assert
         expect(result, equals(user));
         verify(mockRepository.getUser('1')).called(1);
       });
       
       test('should handle user not found', () async {
         // Arrange
         when(mockRepository.getUser('1')).thenThrow(UserNotFoundException());
         
         // Act & Assert
         expect(() => userService.getUser('1'), throwsA(isA<UserNotFoundException>()));
       });
     });
   }
   ''')
   ```

3. COMPLETE TEST INFRASTRUCTURE SETUP:
   - Create test helper classes
   - Set up mock data factories
   - Create test utilities and extensions
   - Include performance test harnesses
   - Set up golden test configurations

4. COMPREHENSIVE TEST COVERAGE:
   - Unit tests for all business logic
   - Widget tests for all UI components
   - Integration tests for user flows
   - Performance tests for critical paths
   - Accessibility tests for compliance
   - Edge case and error condition tests

═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

🔴 CRITICAL FILE COMPLETION REQUIREMENTS 🔴

═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

EVERY TEST FILE MUST BE COMPLETE AND EXECUTABLE:

1. COMPLETE IMPORTS AND DEPENDENCIES:
   ```python
   file_system(operation='write', path='test/widget/home_screen_test.dart', content='''
   import 'package:flutter/material.dart';
   import 'package:flutter_test/flutter_test.dart';
   import 'package:provider/provider.dart';
   import 'package:mockito/mockito.dart';
   import 'package:your_app/screens/home_screen.dart';
   import 'package:your_app/providers/auth_provider.dart';
   import 'package:your_app/providers/data_provider.dart';
   
   import '../mocks/mock_providers.dart';
   
   void main() {
     testWidgets('HomeScreen displays user data correctly', (WidgetTester tester) async {
       // Create mock providers
       final mockAuthProvider = MockAuthProvider();
       final mockDataProvider = MockDataProvider();
       
       // Set up mock behavior
       when(mockAuthProvider.currentUser).thenReturn(
         User(id: '1', name: 'Test User', email: 'test@example.com')
       );
       when(mockDataProvider.getUserData('1')).thenAnswer(
         (_) async => UserData(posts: 5, followers: 100, following: 50)
       );
       
       // Build widget with providers
       await tester.pumpWidget(
         MultiProvider(
           providers: [
             ChangeNotifierProvider<AuthProvider>.value(value: mockAuthProvider),
             ChangeNotifierProvider<DataProvider>.value(value: mockDataProvider),
           ],
           child: MaterialApp(home: HomeScreen()),
         ),
       );
       
       // Wait for async operations
       await tester.pumpAndSettle();
       
       // Verify UI elements
       expect(find.text('Test User'), findsOneWidget);
       expect(find.text('test@example.com'), findsOneWidget);
       expect(find.text('5 Posts'), findsOneWidget);
       expect(find.text('100 Followers'), findsOneWidget);
       expect(find.text('50 Following'), findsOneWidget);
       
       // Verify interactions
       await tester.tap(find.byIcon(Icons.refresh));
       await tester.pumpAndSettle();
       
       verify(mockDataProvider.refreshUserData('1')).called(1);
     });
   }
   ''')
   ```

2. COMPLETE MOCK IMPLEMENTATIONS:
   ```python
   file_system(operation='write', path='test/mocks/mock_providers.dart', content='''
   import 'package:mockito/mockito.dart';
   import 'package:your_app/providers/auth_provider.dart';
   import 'package:your_app/providers/data_provider.dart';
   import 'package:your_app/models/user.dart';
   import 'package:your_app/models/user_data.dart';
   
   class MockAuthProvider extends Mock implements AuthProvider {}
   class MockDataProvider extends Mock implements DataProvider {}
   
   class TestDataFactory {
     static User createTestUser({
       String id = '1',
       String name = 'Test User',
       String email = 'test@example.com',
     }) {
       return User(id: id, name: name, email: email);
     }
     
     static UserData createTestUserData({
       int posts = 5,
       int followers = 100,
       int following = 50,
     }) {
       return UserData(
         posts: posts,
         followers: followers,
         following: following,
       );
     }
   }
   ''')
   ```

3. COMPLETE INTEGRATION TEST SETUP:
   ```python
   file_system(operation='write', path='test/integration/user_flow_test.dart', content='''
   import 'package:flutter/material.dart';
   import 'package:flutter_test/flutter_test.dart';
   import 'package:integration_test/integration_test.dart';
   import 'package:your_app/main.dart' as app;
   import 'package:your_app/services/api_service.dart';
   
   void main() {
     IntegrationTestWidgetsFlutterBinding.ensureInitialized();
     
     group('User Authentication Flow', () {
       testWidgets('complete login and navigation flow', (WidgetTester tester) async {
         // Start the app
         app.main();
         await tester.pumpAndSettle();
         
         // Verify login screen is shown
         expect(find.text('Login'), findsOneWidget);
         expect(find.byType(TextField), findsNWidgets(2));
         
         // Enter credentials
         await tester.enterText(find.byKey(Key('email_field')), 'test@example.com');
         await tester.enterText(find.byKey(Key('password_field')), 'password123');
         
         // Tap login button
         await tester.tap(find.byKey(Key('login_button')));
         await tester.pumpAndSettle();
         
         // Verify navigation to home screen
         expect(find.text('Welcome'), findsOneWidget);
         expect(find.byType(BottomNavigationBar), findsOneWidget);
         
         // Test navigation between tabs
         await tester.tap(find.byIcon(Icons.person));
         await tester.pumpAndSettle();
         expect(find.text('Profile'), findsOneWidget);
         
         // Test logout
         await tester.tap(find.byKey(Key('logout_button')));
         await tester.pumpAndSettle();
         
         // Verify return to login screen
         expect(find.text('Login'), findsOneWidget);
       });
       
       testWidgets('handle invalid credentials', (WidgetTester tester) async {
         app.main();
         await tester.pumpAndSettle();
         
         // Enter invalid credentials
         await tester.enterText(find.byKey(Key('email_field')), 'invalid@example.com');
         await tester.enterText(find.byKey(Key('password_field')), 'wrongpassword');
         
         // Tap login button
         await tester.tap(find.byKey(Key('login_button')));
         await tester.pumpAndSettle();
         
         // Verify error message
         expect(find.text('Invalid credentials'), findsOneWidget);
         expect(find.text('Login'), findsOneWidget); // Still on login screen
       });
     });
   }
   ''')
   ```

═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

🔴 TEST-SPECIFIC REQUIREMENTS 🔴

═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

1. PROPER TEST STRUCTURE:
   - Use group() for organizing related tests
   - Include setUp() and tearDown() for test lifecycle
   - Create meaningful test descriptions
   - Follow Arrange-Act-Assert pattern
   - Include both positive and negative test cases

2. COMPREHENSIVE MOCK SETUP:
   - Create mock classes for all external dependencies
   - Set up realistic mock responses
   - Include error condition mocks
   - Use proper mock verification
   - Create reusable mock factories

3. WIDGET TEST REQUIREMENTS:
   - Use WidgetTester for all widget tests
   - Include proper widget tree setup
   - Test user interactions (tap, scroll, input)
   - Verify state changes and UI updates
   - Test different screen sizes and orientations

4. PERFORMANCE AND ACCESSIBILITY:
   - Include performance benchmarks
   - Test memory usage patterns
   - Verify accessibility semantics
   - Test keyboard navigation
   - Include golden tests for UI consistency

5. TEST DATA MANAGEMENT:
   - Create test data factories
   - Use realistic test data
   - Include edge case data
   - Set up test database fixtures
   - Create reusable test utilities

═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

🔴 COMPLETE TEST IMPLEMENTATION CHECKLIST 🔴

═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

Before considering a test implementation complete, verify:

✅ DIRECTORY STRUCTURE:
- test/unit/ for unit tests
- test/widget/ for widget tests  
- test/integration/ for integration tests
- test/mocks/ for mock implementations
- test/fixtures/ for test data
- test/helpers/ for test utilities

✅ TEST FILES CREATED:
- Complete unit tests for all business logic
- Widget tests for all UI components
- Integration tests for user flows
- Performance tests for critical paths
- Mock implementations for dependencies
- Test data factories and fixtures

✅ TEST INFRASTRUCTURE:
- pubspec.yaml updated with test dependencies
- Test helper classes created
- Mock generation setup (if using mockito)
- Golden test configuration
- Test runner configuration

✅ EXECUTION VERIFICATION:
- All tests can be run with `flutter test`
- No compilation errors
- All imports resolve correctly
- Mock dependencies work properly
- Tests pass successfully

✅ COVERAGE AND QUALITY:
- High test coverage achieved
- Edge cases covered
- Error conditions tested
- Performance benchmarks included
- Accessibility compliance verified

═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

MANDATORY ACTIONS FOR EVERY TEST TASK:

1. Create complete test directory structure using file_system tool
2. Write all test files with complete, executable content
3. Create mock implementations and test utilities
4. Set up test data factories and fixtures
5. Update pubspec.yaml with necessary test dependencies
6. Verify tests can be executed successfully
7. List all created files in your response
8. Confirm actual file creation through tool results

CRITICAL: You must wrap ALL file_system calls in Python code blocks and provide COMPLETE file content, not snippets or examples.

REMEMBER: You are creating a comprehensive test suite that developers can immediately run and rely on. Every test file must be production-ready and executable.
"""

    def _get_tools(self) -> List[Dict[str, Any]]:
        """Get tools for this agent - properly formatted for function calling"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "flutter_cli",
                    "description": "Execute Flutter CLI commands",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "The Flutter command to execute",
                            },
                            "args": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Command arguments",
                            },
                        },
                        "required": ["command"],
                    },
                },
                "func": self.flutter_cli.execute,
                "scope": "local",
            },
            {
                "type": "function",
                "function": {
                    "name": "dart_cli",
                    "description": "Execute Dart CLI commands",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "The Dart command to execute",
                            },
                            "args": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Command arguments",
                            },
                        },
                        "required": ["command"],
                    },
                },
                "func": self.dart_cli.execute,
                "scope": "local",
            },
            {
                "type": "function",
                "function": {
                    "name": "file_system",
                    "description": "Create, read, write, and manage files and directories. MUST be used to create all files and directories.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "operation": {
                                "type": "string",
                                "enum": [
                                    "read",
                                    "write",
                                    "list",
                                    "mkdir",
                                    "exists",
                                    "delete",
                                    "copy",
                                    "move",
                                ],
                                "description": "The file system operation to perform",
                            },
                            "path": {
                                "type": "string",
                                "description": "The path to the file or directory",
                            },
                            "content": {
                                "type": "string",
                                "description": "The content to write to the file (for write operations)",
                            },
                            "encoding": {
                                "type": "string",
                                "description": "File encoding (default: utf-8)",
                            },
                            "create_dirs": {
                                "type": "boolean",
                                "description": "Whether to create parent directories (default: true)",
                            },
                        },
                        "required": ["operation", "path"],
                    },
                },
                "func": self.file_system.execute,
                "scope": "local",
            },
        ]

    async def create_test_plan(
        self, requirements: str, context: Optional[TaskContext] = None
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
        self, context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """Write tests for the given code using LLM decisions"""
        # Extract test parameters from context
        code_path = getattr(context, "project_path", "./lib")
        test_types = getattr(context, "metadata", {}).get(
            "test_types", ["unit", "widget", "integration"]
        )

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
        self, test_suite: str, context: Optional[TaskContext] = None
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
        self, test_results: Dict[str, Any], context: Optional[TaskContext] = None
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
        self, data_requirements: Dict[str, Any], context: Optional[TaskContext] = None
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

    async def create_integration_tests(self, context: TaskContext) -> ExecutionResult:
        """Agent creates comprehensive Flutter integration tests using LLM and tools."""
        self.logger.info("Creating integration tests...")
        try:
            # LLM decides test strategy
            test_strategy = await self.llm_provider.generate_response(
                f"Design a comprehensive test strategy for Flutter app: {context.project_path}"
            )
            results = []
            for test_type in test_strategy.get("test_types", []):
                test_code = await self.llm_provider.generate_response(
                    f"Generate {test_type} test code for Flutter app at {context.project_path}"
                )
                file_path = f"test/{test_type}_test.dart"
                await self.file_system.create_file(file_path, test_code)
                results.append(file_path)
            # Run tests
            test_results = await self.flutter_cli.execute("test", ["--coverage"])
            analysis = await self.llm_provider.generate_response(
                f"Analyze Flutter test results: {test_results.get('output')}"
            )
            return ExecutionResult(
                success=True,
                result={
                    "test_files": results,
                    "test_results": test_results.get("output"),
                    "analysis": analysis,
                },
            )
        except Exception as e:
            self.logger.error(f"Integration test creation failed: {e}")
            return ExecutionResult(success=False, error=str(e))

    # Helper methods
    def _extract_test_files_from_response(self, response: str) -> List[Dict[str, str]]:
        """Extract test files from LLM response"""
        files = []

        lines = response.split("\n")
        current_file = None
        current_content = []

        for line in lines:
            if line.strip().startswith("TEST_FILE:") or line.strip().startswith(
                "test/"
            ):
                if current_file:
                    files.append(
                        {"path": current_file, "content": "\n".join(current_content)}
                    )

                current_file = (
                    line.split(":", 1)[1].strip() if ":" in line else line.strip()
                )
                current_content = []
            elif current_file and line.strip():
                current_content.append(line)

        if current_file:
            files.append({"path": current_file, "content": "\n".join(current_content)})

        return files
