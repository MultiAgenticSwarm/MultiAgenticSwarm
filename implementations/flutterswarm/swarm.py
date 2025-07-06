"""
FlutterSwarm - Orchestrates LLM-powered Flutter development.
Uses MultiAgenticSwarm SDK for all infrastructure.
"""

import logging
from typing import Any, Dict, List, Optional, Union

# Import MultiAgenticSwarm as the core SDK
import multiagenticswarm as mas

# Import AgentSwarm base classes
from implementations.agentswarm.core import BaseSwarm, ExecutionResult, TaskContext
from multiagenticswarm.core.task import TaskStep

# Import FlutterSwarm components
from .agents import (
    FlutterArchitectAgent,
    FlutterDeveloperAgent,
    FlutterTesterAgent,
    FlutterUIDesignerAgent,
)
from .tools import DartCLITool, FileSystemTool, FlutterCLITool


class FlutterSwarm(BaseSwarm):
    """
    Flutter development swarm powered by MultiAgenticSwarm.
    ALL Flutter knowledge comes from LLMs - zero hardcoded logic.

    This swarm orchestrates Flutter development using:
    - FlutterArchitectAgent: Designs system architecture
    - FlutterDeveloperAgent: Implements features using LLM knowledge
    - FlutterUIDesignerAgent: Creates beautiful UI designs
    - FlutterTesterAgent: Creates comprehensive tests

    All agents use LLMs for Flutter-specific knowledge and decisions.
    """

    def __init__(
        self,
        project_path: str = ".",
        system: Optional[Any] = None,
        llm_provider: str = "openai",
        llm_model: str = "gpt-4",
        temperature: float = 0.7,
        **kwargs,
    ):
        # Initialize using BaseSwarm (which inherits from MAS System)
        super().__init__(
            name="FlutterSwarm",
            project_path=project_path,
            system=system,
            llm_provider=llm_provider,
            llm_model=llm_model,
            **kwargs,
        )

        self.logger = mas.get_logger("flutterswarm")
        self.logger.info(f"Initialized FlutterSwarm at {project_path}")
        self._setup_tools()
        self._setup_agents()
        self._setup_workflows()  # Ensure workflows are registered
        self._validate_tools()

        # Note: Flutter SDK and project initialization should be handled by the calling script
        # to avoid blocking asyncio.run() calls in the constructor which would fail when
        # running within an existing event loop

    def _setup_tools(self):
        """Setup CLI wrapper tools - just interfaces, no Flutter logic"""

        # Import the tool factory functions
        from .tools.dart_cli import DartCLITool, create_dart_cli_tool
        from .tools.file_system import FileSystemTool, create_file_system_tool
        from .tools.flutter_cli import FlutterCLITool, create_flutter_cli_tool

        # Create actual tool instances for agent use
        self.flutter_cli_instance = FlutterCLITool(self.project_path)
        self.dart_cli_instance = DartCLITool(self.project_path)
        self.file_system_instance = FileSystemTool(self.project_path)

        # Create MAS Tools using the factory functions for system registration
        self.flutter_cli = create_flutter_cli_tool(self.project_path)
        self.dart_cli = create_dart_cli_tool(self.project_path)
        self.file_system = create_file_system_tool(self.project_path)

        # Set tool sharing levels
        self.flutter_cli.set_global()  # Available to all agents
        self.dart_cli.set_global()  # Available to all agents
        self.file_system.set_global()  # Available to all agents

        # Register tools with MAS system
        self.register_tool(self.flutter_cli)
        self.register_tool(self.dart_cli)
        self.register_tool(self.file_system)

        self.logger.info("Registered Flutter development tools")

    def _setup_agents(self):
        """Setup domain-specific agents with MAS integration"""

        # Create domain-specific agents with proper MAS integration and shared tools
        self.architect = FlutterArchitectAgent(
            name="flutter_architect",
            working_directory=self.project_path,
            llm_provider=self.llm_provider,
            llm_model=self.llm_model,
            flutter_cli=self.flutter_cli_instance,
            dart_cli=self.dart_cli_instance,
            file_system=self.file_system_instance,
        )

        self.developer = FlutterDeveloperAgent(
            name="flutter_developer",
            working_directory=self.project_path,
            llm_provider=self.llm_provider,
            llm_model=self.llm_model,
            flutter_cli=self.flutter_cli_instance,
            dart_cli=self.dart_cli_instance,
            file_system=self.file_system_instance,
        )

        self.ui_designer = FlutterUIDesignerAgent(
            name="flutter_ui_designer",
            working_directory=self.project_path,
            llm_provider=self.llm_provider,
            llm_model=self.llm_model,
            flutter_cli=self.flutter_cli_instance,
            dart_cli=self.dart_cli_instance,
            file_system=self.file_system_instance,
        )

        self.tester = FlutterTesterAgent(
            name="flutter_tester",
            working_directory=self.project_path,
            llm_provider=self.llm_provider,
            llm_model=self.llm_model,
            flutter_cli=self.flutter_cli_instance,
            dart_cli=self.dart_cli_instance,
            file_system=self.file_system_instance,
        )

        # Add all agents to the swarm (using BaseSwarm.add_agent)
        self.add_agent(self.architect)
        self.add_agent(self.developer)
        self.add_agent(self.ui_designer)
        self.add_agent(self.tester)

        self.logger.info("Initialized Flutter development agents")

    def _setup_workflows(self):
        """Setup Flutter development workflows using MAS Task system"""

        # Create app development workflow with explicit file creation instructions
        app_creation_task = mas.Task(
            name="create_flutter_app",
            description="Complete Flutter app creation workflow with file creation",
            steps=[
                TaskStep(
                    agent="architect",
                    tool="design_architecture",
                    input_data="app_requirements - MANDATORY: Use file_system tool to create architecture documentation files. Create directory structure and write all architectural decisions to files.",
                    context={"file_creation_mandatory": True},
                ),
                TaskStep(
                    agent="developer",
                    tool="setup_project_structure",
                    input_data="architecture_design - MANDATORY: Use file_system tool to create all project directories and base files. Write complete file contents, not just examples.",
                    context={"file_creation_mandatory": True},
                ),
                TaskStep(
                    agent="ui_designer",
                    tool="design_ui",
                    input_data="project_structure - MANDATORY: Use file_system tool to create all UI-related files. Write complete Widget implementations to files.",
                    context={"file_creation_mandatory": True},
                ),
                TaskStep(
                    agent="developer",
                    tool="implement_feature",
                    input_data="ui_design - MANDATORY: Use file_system tool to create all feature implementation files. Write complete Dart code to files.",
                    context={"file_creation_mandatory": True},
                ),
                TaskStep(
                    agent="tester",
                    tool="write_tests",
                    input_data="implemented_features - MANDATORY: Use file_system tool to create all test files. Write complete test implementations to files.",
                    context={"file_creation_mandatory": True},
                ),
                TaskStep(
                    agent="developer",
                    tool="implement_feature",
                    input_data="test_suite - MANDATORY: Use file_system tool to finalize all implementation files. Ensure all features are properly implemented.",
                    context={"file_creation_mandatory": True},
                ),
            ],
        )

        # Feature implementation workflow with file creation
        feature_implementation_task = mas.Task(
            name="implement_flutter_feature",
            description="Implement a new Flutter feature with file creation",
            steps=[
                TaskStep(
                    agent="architect",
                    tool="analyze_requirements",
                    input_data="feature_description - MANDATORY: Use file_system tool to create feature analysis documentation files.",
                    context={"file_creation_mandatory": True},
                ),
                TaskStep(
                    agent="ui_designer",
                    tool="design_ui",
                    input_data="feature_analysis - MANDATORY: Use file_system tool to create UI files for the feature. Write complete Widget code to files.",
                    context={"file_creation_mandatory": True},
                ),
                TaskStep(
                    agent="developer",
                    tool="implement_feature",
                    input_data="feature_ui_design - MANDATORY: Use file_system tool to create feature implementation files. Write complete Dart code to files.",
                    context={"file_creation_mandatory": True},
                ),
                TaskStep(
                    agent="tester",
                    tool="write_tests",
                    input_data="feature_implementation - MANDATORY: Use file_system tool to create test files for the feature. Write complete test code to files.",
                    context={"file_creation_mandatory": True},
                ),
            ],
        )

        # Register workflows with MAS system
        self.register_task(app_creation_task)
        self.register_task(feature_implementation_task)

        self.logger.info(
            "Registered Flutter development workflows with file creation instructions"
        )

    def _validate_tools(self):
        """Validate that all required tools are registered and healthy."""
        required_tools = ["flutter_cli", "dart_cli", "file_system"]
        for tool_name in required_tools:
            tool = getattr(self, tool_name, None)
            if tool is None:
                self.logger.error(
                    f"Critical tool {tool_name} not registered in FlutterSwarm."
                )
                raise RuntimeError(f"Critical tool {tool_name} not registered.")
            # Note: Health checks should be performed asynchronously by the calling code
            # to avoid blocking the constructor with asyncio.run()
        self.logger.info("All required tools validated and registered.")

    async def validate_environment(self) -> bool:
        """
        Validate that the Flutter environment is properly set up.
        This should be called after initialization to ensure everything is ready.
        """
        try:
            # Check Flutter SDK installation
            if not await self.check_flutter_installed():
                self.logger.error(
                    "Flutter SDK not installed. Please install Flutter to continue."
                )
                return False

            # Validate project initialization
            if not await self.initialize_project():
                self.logger.error("Failed to initialize Flutter project.")
                return False

            # Validate tool health
            for tool_name in ["flutter_cli", "dart_cli", "file_system"]:
                tool = getattr(self, tool_name, None)
                if tool and hasattr(tool, "health_check"):
                    health = await tool.health_check()
                    if not health.get("healthy", False):
                        self.logger.error(
                            f"Tool {tool_name} failed health check: {health.get('error')}"
                        )
                        return False

            self.logger.info("Flutter environment validation completed successfully.")
            return True

        except Exception as e:
            self.logger.error(f"Environment validation failed: {str(e)}")
            return False

    async def _gather_context(self, app_description: str, **kwargs) -> Dict[str, Any]:
        """Gather comprehensive context for Flutter app creation."""
        context = {
            "app_description": app_description,
            "project_path": self.project_path,
            "platform_targets": kwargs.get("platform_targets", ["ios", "android"]),
            "dependencies": kwargs.get("dependencies", []),
            "previous_operations": getattr(self, "execution_history", []),
        }
        # Gather Flutter SDK version
        if hasattr(self, "flutter_cli"):
            version_info = await self.flutter_cli.execute("--version")
            context["flutter_version"] = version_info.get("output", "unknown")
        # Gather available devices
        if hasattr(self, "flutter_cli"):
            devices_info = await self.flutter_cli.execute("devices")
            context["available_devices"] = devices_info.get("output", "unknown")
        # System capabilities (RAM, disk)
        import shutil

        import psutil

        context["system_capabilities"] = {
            "ram_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "disk_free_gb": round(
                shutil.disk_usage(self.project_path).free / (1024**3), 2
            ),
        }
        self.logger.info(f"Context gathered: {context}")
        return context

    async def create_app(
        self,
        app_description: str,
        features: List[str],
        platforms: List[str] = ["ios", "android"],
        design_requirements: Optional[Dict[str, Any]] = None,
        performance_requirements: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """
        Create a complete Flutter application using LLM-powered agents.
        All Flutter knowledge and decisions come from LLMs.
        """

        self.logger.info(f"Creating Flutter app: {app_description}")

        # Create comprehensive task context
        context = {
            "app_requirements": {
                "app_description": app_description,
                "features": features,
                "platforms": platforms,
                "design_requirements": design_requirements or {},
                "performance_requirements": performance_requirements or {},
            },
            "app_description": app_description,
            "features": features,
            "platforms": platforms,
            "design_requirements": design_requirements or {},
            "performance_requirements": performance_requirements or {},
            "project_path": self.project_path,
        }

        # Execute app creation workflow using MAS
        result = await self.execute_workflow("create_flutter_app", context)

        # Convert to ExecutionResult if needed
        if not isinstance(result, ExecutionResult):
            result = ExecutionResult(
                success=True,
                agent_name="FlutterSwarm",
                task_id="create_flutter_app",
                output=result,
                execution_time=0,
                metadata=context,
            )

        self.logger.info(f"Flutter app creation completed: {result.success}")
        return result

    async def implement_feature(
        self, feature_description: str, context: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """
        Implement a new feature using Flutter development agents.
        """

        self.logger.info(f"Implementing Flutter feature: {feature_description}")

        # Create feature context
        feature_context = {
            "feature_description": feature_description,
            "project_path": self.project_path,
            **(context or {}),
        }

        # Execute feature implementation workflow
        result = await self.execute_workflow(
            "implement_flutter_feature", feature_context
        )

        self.logger.info(f"Feature implementation completed: {result.success}")
        return result

    async def analyze_project(self) -> ExecutionResult:
        """
        Analyze existing Flutter project structure and provide recommendations.
        """

        self.logger.info("Analyzing Flutter project")

        # Use architect agent to analyze project
        analysis_prompt = f"""
        Analyze the Flutter project at: {self.project_path}

        Provide comprehensive analysis including:
        1. Project structure assessment
        2. Code quality evaluation
        3. Performance optimization opportunities
        4. Architecture improvements
        5. Security considerations
        6. Testing coverage analysis
        7. Dependency management recommendations
        8. Platform-specific optimizations

        Generate detailed recommendations for improvements.
        """

        result = await self.architect.execute(analysis_prompt, self.context)

        self.logger.info(f"Project analysis completed: {result.success}")
        return result

    async def optimize_performance(
        self, target_areas: List[str] = None
    ) -> ExecutionResult:
        """
        Optimize Flutter app performance in specified areas.
        """

        target_areas = target_areas or [
            "build_time",
            "runtime",
            "memory",
            "bundle_size",
        ]
        self.logger.info(f"Optimizing Flutter app performance: {target_areas}")

        # Use developer agent to optimize performance
        optimization_context = {
            "target_areas": target_areas,
            "project_path": self.project_path,
        }

        result = await self.developer.optimize_performance(
            target_area=", ".join(target_areas),
            context=TaskContext(
                project_path=self.project_path, metadata=optimization_context
            ),
        )

        self.logger.info(f"Performance optimization completed: {result.success}")
        return result

    async def run_comprehensive_tests(self) -> ExecutionResult:
        """
        Run comprehensive test suite using tester agent.
        """

        self.logger.info("Running comprehensive Flutter tests")

        # Use tester agent to run all tests
        test_prompt = f"""
        Run comprehensive test suite for Flutter project at: {self.project_path}

        Include:
        1. Unit tests
        2. Widget tests
        3. Integration tests
        4. Performance tests
        5. Golden tests (if applicable)
        6. Platform-specific tests

        Provide detailed test results and recommendations.
        """

        result = await self.tester.execute(test_prompt, self.context)

        self.logger.info(f"Comprehensive testing completed: {result.success}")
        return result

    async def deploy_app(
        self, target_platforms: List[str], deployment_config: Dict[str, Any]
    ) -> ExecutionResult:
        """
        Deploy Flutter app to specified platforms.
        """

        self.logger.info(f"Deploying Flutter app to: {target_platforms}")

        # Create deployment task using MAS Task system
        deployment_task = mas.Task(
            name="deploy_flutter_app",
            description="Deploy Flutter app to target platforms",
            steps=[
                {
                    "agent": "flutter_developer",
                    "action": "prepare_deployment",
                    "input": "deployment_config",
                },
                {
                    "agent": "flutter_tester",
                    "action": "run_deployment_tests",
                    "input": "deployment_preparation",
                },
                {
                    "agent": "flutter_developer",
                    "action": "build_for_platforms",
                    "input": "target_platforms",
                },
                {
                    "agent": "flutter_developer",
                    "action": "deploy_to_platforms",
                    "input": "built_apps",
                },
            ],
        )

        # Execute deployment
        deployment_context = {
            "target_platforms": target_platforms,
            "deployment_config": deployment_config,
            "project_path": self.project_path,
        }

        # Register and execute deployment task
        self.register_task(deployment_task)
        result = await self.execute_task("deploy_flutter_app", deployment_context)

        self.logger.info(f"App deployment completed: {result.get('success', False)}")
        return ExecutionResult(
            success=result.get("success", False),
            agent_name="FlutterSwarm",
            task_id="deploy_flutter_app",
            output=result,
            execution_time=result.get("execution_time", 0),
            metadata=deployment_context,
        )

    async def add_feature(
        self,
        feature_description: str,
        feature_type: str = "ui",
        integration_requirements: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """
        Add a new feature to the Flutter application.
        """
        self.logger.info(f"Adding feature: {feature_description}")

        # Create feature implementation task using MAS Task system
        feature_task = mas.Task(
            name="implement_flutter_feature",
            description=f"Implement feature: {feature_description}",
            steps=[
                {
                    "agent": "flutter_architect",
                    "action": "analyze_feature_requirements",
                    "input": feature_description,
                },
                {
                    "agent": "flutter_ui_designer",
                    "action": "design_feature_ui",
                    "input": "feature_analysis",
                },
                {
                    "agent": "flutter_developer",
                    "action": "implement_feature",
                    "input": "feature_ui_design",
                },
                {
                    "agent": "flutter_tester",
                    "action": "test_feature",
                    "input": "feature_implementation",
                },
            ],
        )

        # Execute feature implementation
        feature_context = {
            "feature_description": feature_description,
            "feature_type": feature_type,
            "integration_requirements": integration_requirements or {},
            "project_path": self.project_path,
        }

        # Register and execute feature task
        self.register_task(feature_task)
        result = await self.execute_task("implement_flutter_feature", feature_context)

        self.logger.info(
            f"Feature implementation completed: {result.get('success', False)}"
        )
        return ExecutionResult(
            success=result.get("success", False),
            agent_name="FlutterSwarm",
            task_id="implement_flutter_feature",
            output=result,
            execution_time=result.get("execution_time", 0),
            metadata=feature_context,
        )

    async def debug_issue(
        self,
        issue_description: str,
        error_logs: Optional[str] = None,
        reproduction_steps: Optional[List[str]] = None,
    ) -> ExecutionResult:
        """
        Debug and resolve Flutter app issues using agent collaboration.
        """
        self.logger.info(f"Debugging issue: {issue_description}")

        # Create debugging task using MAS Task system
        debug_task = mas.Task(
            name="debug_flutter_issue",
            description=f"Debug and resolve issue: {issue_description}",
            steps=[
                {
                    "agent": "flutter_developer",
                    "action": "analyze_issue",
                    "input": "issue_description",
                },
                {
                    "agent": "flutter_tester",
                    "action": "reproduce_issue",
                    "input": "reproduction_steps",
                },
                {
                    "agent": "flutter_developer",
                    "action": "identify_root_cause",
                    "input": "reproduction_results",
                },
                {
                    "agent": "flutter_developer",
                    "action": "implement_fix",
                    "input": "root_cause_analysis",
                },
                {
                    "agent": "flutter_tester",
                    "action": "verify_fix",
                    "input": "implemented_fix",
                },
            ],
        )

        # Execute debugging
        debug_context = {
            "issue_description": issue_description,
            "error_logs": error_logs,
            "reproduction_steps": reproduction_steps or [],
            "project_path": self.project_path,
        }

        # Register and execute debug task
        self.register_task(debug_task)
        result = await self.execute_task("debug_flutter_issue", debug_context)

        self.logger.info(f"Issue debugging completed: {result.get('success', False)}")
        return ExecutionResult(
            success=result.get("success", False),
            agent_name="FlutterSwarm",
            task_id="debug_flutter_issue",
            output=result,
            execution_time=result.get("execution_time", 0),
            metadata=debug_context,
        )

    async def run_tests(
        self,
        test_types: List[str] = ["unit", "widget", "integration"],
        coverage_report: bool = True,
    ) -> ExecutionResult:
        """
        Run Flutter tests using the tester agent.
        """
        self.logger.info(f"Running Flutter tests: {test_types}")

        # Create test execution task using MAS Task system
        test_task = mas.Task(
            name="run_flutter_tests",
            description=f"Run Flutter tests: {', '.join(test_types)}",
            steps=[
                {
                    "agent": "flutter_tester",
                    "action": "setup_test_environment",
                    "input": "test_types",
                },
                {
                    "agent": "flutter_tester",
                    "action": "run_unit_tests",
                    "input": "test_environment",
                },
                {
                    "agent": "flutter_tester",
                    "action": "run_widget_tests",
                    "input": "test_environment",
                },
                {
                    "agent": "flutter_tester",
                    "action": "run_integration_tests",
                    "input": "test_environment",
                },
                {
                    "agent": "flutter_tester",
                    "action": "generate_coverage_report",
                    "input": "test_results",
                },
            ],
        )

        # Execute tests
        test_context = {
            "test_types": test_types,
            "coverage_report": coverage_report,
            "project_path": self.project_path,
        }

        # Register and execute test task
        self.register_task(test_task)
        result = await self.execute_task("run_flutter_tests", test_context)

        self.logger.info(f"Flutter tests completed: {result.get('success', False)}")
        return ExecutionResult(
            success=result.get("success", False),
            agent_name="FlutterSwarm",
            task_id="run_flutter_tests",
            output=result,
            execution_time=result.get("execution_time", 0),
            metadata=test_context,
        )

    async def get_project_status(
        self,
        include_analysis: bool = True,
        include_tests: bool = True,
        include_dependencies: bool = True,
    ) -> ExecutionResult:
        """
        Get comprehensive Flutter project status and analysis.
        """
        self.logger.info("Getting Flutter project status")

        # Create project status task using MAS Task system
        status_task = mas.Task(
            name="get_flutter_project_status",
            description="Get comprehensive Flutter project status and analysis",
            steps=[
                {
                    "agent": "flutter_architect",
                    "action": "analyze_project_structure",
                    "input": "project_path",
                },
                {
                    "agent": "flutter_developer",
                    "action": "check_code_quality",
                    "input": "project_structure",
                },
                {
                    "agent": "flutter_tester",
                    "action": "check_test_coverage",
                    "input": "project_structure",
                },
                {
                    "agent": "flutter_architect",
                    "action": "generate_status_report",
                    "input": "analysis_results",
                },
            ],
        )

        # Execute project status analysis
        status_context = {
            "include_analysis": include_analysis,
            "include_tests": include_tests,
            "include_dependencies": include_dependencies,
            "project_path": self.project_path,
        }

        # Register and execute status task
        self.register_task(status_task)
        result = await self.execute_task("get_flutter_project_status", status_context)

        self.logger.info(
            f"Project status analysis completed: {result.get('success', False)}"
        )
        return ExecutionResult(
            success=result.get("success", False),
            agent_name="FlutterSwarm",
            task_id="get_flutter_project_status",
            output=result,
            execution_time=result.get("execution_time", 0),
            metadata=status_context,
        )

    async def check_flutter_installed(self) -> bool:
        """Check if Flutter SDK is installed and available in PATH."""
        import shutil

        return shutil.which("flutter") is not None

    async def initialize_project(self, project_name: str = None) -> bool:
        """Initialize a Flutter project in the project_path if not already present."""
        import asyncio
        import os

        if not os.path.exists(os.path.join(self.project_path, "pubspec.yaml")):
            proc = await asyncio.create_subprocess_shell(
                f"flutter create .",
                cwd=self.project_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            out, err = await proc.communicate()
            if proc.returncode != 0:
                self.logger.error(
                    f"Failed to initialize Flutter project: {err.decode()}"
                )
                return False
            self.logger.info("Flutter project initialized.")
        return True

    async def _parse_and_execute_code(self, agent_output: str):
        """
        Parse and execute Python code blocks from agent output.

        Args:
            agent_output: The agent's string output containing potential Python code blocks
        """
        import asyncio
        import re

        # Extract Python code blocks using regex
        code_pattern = r"```python\s*\n(.*?)\n```"
        code_blocks = re.findall(code_pattern, agent_output, re.DOTALL)

        if not code_blocks:
            self.logger.debug("No Python code blocks found in agent output")
            return

        self.logger.info(f"Found {len(code_blocks)} Python code blocks to execute")

        # Create globals dictionary with tool mappings - use sync versions
        execution_globals = {
            "file_system": self._sync_file_system_wrapper,
            "flutter_cli": self._sync_flutter_cli_wrapper,
            "dart_cli": self._sync_dart_cli_wrapper,
            "__builtins__": __builtins__,
        }

        # Execute each code block
        for i, code_block in enumerate(code_blocks):
            try:
                self.logger.info(f"Executing code block {i + 1}/{len(code_blocks)}")
                self.logger.debug(f"Code block content:\n{code_block}")

                # Clean up the code block (remove extra whitespace)
                cleaned_code = code_block.strip()

                # Execute the code block
                exec(cleaned_code, execution_globals)

                self.logger.info(f"Successfully executed code block {i + 1}")

            except Exception as e:
                self.logger.error(f"Error executing code block {i + 1}: {str(e)}")
                self.logger.error(f"Code block that failed:\n{code_block}")
                # Continue with other code blocks even if one fails
                continue

    def _sync_file_system_wrapper(self, **kwargs):
        """Synchronous wrapper for file system operations."""
        import asyncio

        # Always use direct execution since it's more reliable
        self.logger.info(f"Executing file system operation: {kwargs}")
        return self._direct_file_system_execute(**kwargs)

    def _sync_flutter_cli_wrapper(self, **kwargs):
        """Synchronous wrapper for Flutter CLI operations."""
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return asyncio.run_coroutine_threadsafe(
                    self.flutter_cli_instance.execute(**kwargs), loop
                ).result()
            else:
                return asyncio.run(self.flutter_cli_instance.execute(**kwargs))
        except Exception as e:
            self.logger.error(f"Error in Flutter CLI operation: {str(e)}")
            return {"success": False, "error": str(e)}

    def _sync_dart_cli_wrapper(self, **kwargs):
        """Synchronous wrapper for Dart CLI operations."""
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return asyncio.run_coroutine_threadsafe(
                    self.dart_cli_instance.execute(**kwargs), loop
                ).result()
            else:
                return asyncio.run(self.dart_cli_instance.execute(**kwargs))
        except Exception as e:
            self.logger.error(f"Error in Dart CLI operation: {str(e)}")
            return {"success": False, "error": str(e)}

    def _direct_file_system_execute(self, **kwargs):
        """Direct file system execution for simple operations."""
        import os

        operation = kwargs.get("operation")
        path = kwargs.get("path")
        content = kwargs.get("content", "")

        try:
            # Resolve relative paths
            if not os.path.isabs(path):
                path = os.path.join(self.project_path, path)

            if operation == "write":
                # Create directory if it doesn't exist
                dir_path = os.path.dirname(path)
                if dir_path:
                    os.makedirs(dir_path, exist_ok=True)
                    self.logger.info(f"Created directory: {dir_path}")

                # Special handling for pubspec.yaml - ensure it has required dependencies
                if path.endswith("pubspec.yaml") and content:
                    content = self._ensure_pubspec_dependencies(content)

                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                self.logger.info(f"File written: {path} ({len(content)} characters)")
                return {
                    "success": True,
                    "message": f"File written: {path}",
                    "path": path,
                }

            elif operation == "mkdir":
                os.makedirs(path, exist_ok=True)
                self.logger.info(f"Directory created: {path}")
                return {
                    "success": True,
                    "message": f"Directory created: {path}",
                    "path": path,
                }

            elif operation == "read":
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                return {"success": True, "content": content, "path": path}

            elif operation == "exists":
                exists = os.path.exists(path)
                return {"success": True, "exists": exists, "path": path}

            elif operation == "list":
                if os.path.isdir(path):
                    items = os.listdir(path)
                    return {"success": True, "items": items, "path": path}
                else:
                    return {
                        "success": False,
                        "error": "Path is not a directory",
                        "path": path,
                    }

            else:
                self.logger.warning(f"Unknown file system operation: {operation}")
                return {"success": False, "error": f"Unknown operation: {operation}"}

        except Exception as e:
            self.logger.error(f"Direct file system operation failed: {str(e)}")
            self.logger.error(f"Operation: {operation}, Path: {path}")
            return {"success": False, "error": str(e), "path": path}

    def _ensure_pubspec_dependencies(self, content: str) -> str:
        """Ensure pubspec.yaml has required dependencies for Flutter apps."""
        # Check if provider is already in the content
        if "provider:" not in content and "dependencies:" in content:
            # Add provider dependency if missing
            import re

            # Find the dependencies section and add provider
            pattern = r"(dependencies:\s*\n(?:.*\n)*?)(\n\s*dev_dependencies:)"
            replacement = r"\1  provider: ^6.1.1\n\2"
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
            self.logger.info("Added provider dependency to pubspec.yaml")

        return content

    async def _dispatch_action(
        self, agent_name: str, action: str, input_data: Any, context: Dict[str, Any]
    ):
        """Map workflow action strings to agent methods and invoke them."""

        # Map short agent names to actual agent attributes
        agent_mapping = {
            "architect": "architect",
            "developer": "developer",
            "ui_designer": "ui_designer",
            "tester": "tester",
            "flutter_architect": "architect",
            "flutter_developer": "developer",
            "flutter_ui_designer": "ui_designer",
            "flutter_tester": "tester",
        }

        mapped_agent_name = agent_mapping.get(agent_name, agent_name)
        agent = getattr(self, mapped_agent_name, None)
        if agent is None:
            raise RuntimeError(
                f"Agent '{agent_name}' (mapped to '{mapped_agent_name}') not found in swarm."
            )

        # Map action string to method
        method = getattr(agent, action, None)
        if not method or not callable(method):
            raise RuntimeError(
                f"Action '{action}' not implemented on agent '{agent_name}'."
            )

        # Call the method (support async)
        import asyncio

        if asyncio.iscoroutinefunction(method):
            # Convert context to TaskContext if needed
            if isinstance(context, dict):
                from implementations.agentswarm.core.types import TaskContext

                # Extract supported TaskContext fields
                supported_fields = {
                    "project_structure",
                    "requirements",
                    "constraints",
                    "target_platforms",
                    "existing_files",
                    "dependencies",
                }

                task_context_kwargs = {}
                metadata = {}

                for key, value in context.items():
                    if key in supported_fields:
                        task_context_kwargs[key] = value
                    elif key != "project_path":  # Already handled as positional arg
                        metadata[key] = value

                task_context = TaskContext(
                    project_path=self.project_path,
                    metadata=metadata,
                    **task_context_kwargs,
                )
            else:
                task_context = context

            return await method(task_context)
        else:
            return method(context)

    async def execute_workflow(self, workflow_name: str, context: Dict[str, Any]):
        """Execute a workflow by mapping steps to agent methods."""
        # Find the workflow by name
        workflow = self.tasks.get(workflow_name)
        if not workflow:
            available_workflows = list(self.tasks.keys())
            raise RuntimeError(
                f"Workflow '{workflow_name}' not found. Available workflows: {available_workflows}"
            )

        result = None
        for step in workflow.steps:
            # Handle both TaskStep objects and dictionary steps
            if hasattr(step, "agent"):
                # TaskStep object
                agent_name = step.agent
                action = step.tool or "execute"  # Default action if no tool specified
                input_data = step.input_data or context
            else:
                # Dictionary step (legacy)
                agent_name = step["agent"]
                action = step["action"]
                input_key = step["input"]
                input_data = context.get(input_key)

            result = await self._dispatch_action(
                agent_name, action, input_data, context
            )

            # Parse and execute any Python code blocks in the agent's output
            try:
                # Extract the output string from the result
                output_text = ""
                if hasattr(result, "output"):
                    if isinstance(result.output, dict):
                        # Handle dictionary output - look for common keys
                        if "output" in result.output:
                            output_text = str(result.output["output"])
                        elif "content" in result.output:
                            output_text = str(result.output["content"])
                        elif "message" in result.output:
                            output_text = str(result.output["message"])
                        else:
                            # Convert entire dict to string
                            output_text = str(result.output)
                    else:
                        output_text = str(result.output)
                elif isinstance(result, str):
                    output_text = result
                elif hasattr(result, "content"):
                    output_text = str(result.content)
                elif hasattr(result, "message"):
                    output_text = str(result.message)
                else:
                    output_text = str(result)

                # Execute any code blocks found in the output
                if output_text and output_text.strip():
                    self.logger.info(
                        f"Parsing agent output for code blocks: {len(output_text)} characters"
                    )
                    await self._parse_and_execute_code(output_text)
                else:
                    self.logger.warning("No output text found to parse for code blocks")

            except Exception as e:
                self.logger.error(
                    f"Error parsing/executing code from agent output: {str(e)}"
                )
                self.logger.debug(f"Agent result type: {type(result)}")
                self.logger.debug(f"Agent result: {result}")

            # Update context with result for next step
            if hasattr(step, "agent"):
                context[f"{step.agent}_result"] = result
            else:
                context[action] = result
        return result
