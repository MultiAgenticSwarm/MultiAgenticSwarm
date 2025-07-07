"""
FlutterSwarm - Orchestrates LLM-powered Flutter development.
Uses MultiAgenticSwarm SDK for all infrastructure.

This implementation ensures comprehensive logging of all operations for
universal coverage across all swarms (FlutterSwarm, PythonSwarm, etc.).
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

# Import MultiAgenticSwarm as the core SDK
import multiagenticswarm as mas


# Shared Project Memory System using mas.Trigger
class SharedProjectMemory:
    """
    Shared project memory that accumulates knowledge across agents.
    Uses mas.Trigger to maintain state continuity between agent phases.
    """

    def __init__(self, project_path: str):
        self.project_path = project_path
        self.memory = {
            "architecture_decisions": {},
            "implementation_patterns": {},
            "file_structure": {},
            "dependencies": [],
            "completed_tasks": [],
            "partial_work": {},
            "agent_handoffs": [],
        }

        # Create trigger for memory updates
        self.memory_trigger = mas.Trigger(
            name="project_memory_update",
            description="Triggered when project memory needs updating",
            condition_string="agent_completion or task_progress or file_creation",
        )

    def update_memory(self, agent_name: str, task_result: dict, context: dict):
        """Update shared memory with agent results"""
        self.memory["agent_handoffs"].append(
            {
                "agent": agent_name,
                "timestamp": __import__("datetime").datetime.now().isoformat(),
                "task_result": task_result,
                "context": context,
            }
        )

        # Fire memory update trigger
        self.memory_trigger.fire(
            {
                "agent": agent_name,
                "memory_state": self.memory,
                "project_path": self.project_path,
            }
        )

    def get_context_for_agent(self, agent_name: str) -> dict:
        """Get comprehensive context for an agent including actual file contents"""
        import os

        # Gather current project state
        current_files = {}
        file_structure = {}

        try:
            for root, dirs, files in os.walk(self.project_path):
                rel_root = os.path.relpath(root, self.project_path)
                file_structure[rel_root] = {"directories": dirs, "files": files}

                for file in files:
                    if file.endswith((".dart", ".yaml", ".json", ".md")):
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, self.project_path)
                        try:
                            with open(file_path, "r", encoding="utf-8") as f:
                                content = f.read()
                            current_files[rel_path] = {
                                "content": content,
                                "size": len(content),
                                "type": file.split(".")[-1],
                                "complete": self._is_file_complete(content),
                            }
                        except Exception as e:
                            current_files[rel_path] = {
                                "error": str(e),
                                "size": 0,
                                "type": file.split(".")[-1],
                                "complete": False,
                            }
        except Exception as e:
            # If we can't read the project, just use what we have in memory
            pass

        # Update memory with current state
        self.memory["file_structure"] = file_structure
        self.memory["current_files"] = current_files

        return {
            "project_path": self.project_path,
            "previous_work": self.memory,
            "last_agent": self.memory["agent_handoffs"][-1]
            if self.memory["agent_handoffs"]
            else None,
            "file_structure": file_structure,
            "current_files": current_files,
            "architecture_decisions": self.memory["architecture_decisions"],
            "implementation_patterns": self.memory["implementation_patterns"],
            "agent_name": agent_name,
            "handoff_count": len(self.memory["agent_handoffs"]),
        }

    def _is_file_complete(self, content: str) -> bool:
        """Check if a file appears to be complete"""
        if not content or len(content.strip()) < 20:
            return False

        # Check for obvious incomplete markers
        incomplete_patterns = [
            "TODO",
            "FIXME",
            "// ...",
            "class }",
            "void }",
            "{ }",
            "get }",
            "set }",
            "String }",
            "Widget }",
        ]

        for pattern in incomplete_patterns:
            if pattern in content:
                return False

        # Check balanced braces for Dart files
        if "{" in content:
            if content.count("{") != content.count("}"):
                return False

        # Check balanced parentheses
        if "(" in content:
            if content.count("(") != content.count(")"):
                return False

        # Check for incomplete structures at end
        content_lines = content.strip().split("\n")
        if content_lines:
            last_line = content_lines[-1].strip()
            if last_line.endswith(
                ("class", "void", "String", "Widget", "get", "set", "{")
            ):
                return False

        return True


# Task Continuation System using mas.Automation
class TaskContinuation:
    """
    Manages task continuation when agents hit output limits.
    Uses mas.Automation to detect incomplete work and resume tasks.
    """

    def __init__(self, project_path: str):
        self.project_path = project_path
        self.incomplete_tasks = {}

        # Create trigger for task continuation
        self.continuation_trigger = mas.Trigger(
            name="task_continuation_trigger",
            description="Triggered when tasks need continuation",
            condition_string="output_limit_reached or incomplete_task_detected",
        )

    def detect_incomplete_work(
        self, agent_output: str, expected_deliverables: list, project_path: str = None
    ) -> dict:
        """Detect if agent work is incomplete using multiple validation methods"""
        incomplete_items = []
        truncation_indicators = []
        code_issues = []

        # Method 1: Check for expected deliverables in output
        for deliverable in expected_deliverables:
            if deliverable not in agent_output:
                incomplete_items.append(deliverable)

        # Method 2: Check for truncation indicators
        truncation_patterns = [
            r"\w+\s*$",  # Word followed by whitespace at end (likely cut off)
            r"[{(\[]\s*$",  # Opening brace/bracket at end
            r"=\s*$",  # Assignment operator at end
            r"\.\s*$",  # Dot at end (method call cut off)
            r"@\w*\s*$",  # Annotation cut off
            r"import\s+[\w.]*\s*$",  # Import statement cut off
            r"class\s+\w*\s*$",  # Class declaration cut off
            r"void\s+\w*\s*$",  # Method declaration cut off
            r"String\s+get\s*$",  # Getter cut off
            r"const\s+\w*\s*$",  # Const declaration cut off
        ]

        import re

        for pattern in truncation_patterns:
            if re.search(pattern, agent_output):
                truncation_indicators.append(
                    f"Output likely truncated: ends with pattern '{pattern}'"
                )

        # Method 3: Check for incomplete code structures if project_path provided
        if project_path:
            import os

            for root, dirs, files in os.walk(project_path):
                for file in files:
                    if file.endswith(".dart"):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, "r") as f:
                                content = f.read()

                            # Check for incomplete structures
                            if "{" in content and content.count("{") != content.count(
                                "}"
                            ):
                                code_issues.append(f"{file_path}: Mismatched braces")
                            if "TODO" in content or "FIXME" in content:
                                code_issues.append(f"{file_path}: Contains TODO/FIXME")
                            if content.strip().endswith(
                                ("class", "void", "String", "Widget", "{")
                            ):
                                code_issues.append(
                                    f"{file_path}: Incomplete code structure"
                                )
                            if len(content.strip()) < 50:
                                code_issues.append(
                                    f"{file_path}: File too small, likely incomplete"
                                )

                        except Exception as e:
                            code_issues.append(
                                f"{file_path}: Could not read file - {str(e)}"
                            )

        # Determine if work is incomplete
        is_incomplete = bool(incomplete_items or truncation_indicators or code_issues)

        if is_incomplete:
            return {
                "is_incomplete": True,
                "missing_items": incomplete_items,
                "truncation_indicators": truncation_indicators,
                "code_issues": code_issues,
                "completion_percentage": max(
                    0,
                    (len(expected_deliverables) - len(incomplete_items))
                    / len(expected_deliverables)
                    * 100,
                )
                if expected_deliverables
                else 0,
            }

        return {"is_incomplete": False, "completion_percentage": 100}

    def create_continuation_prompt(
        self, agent_name: str, incomplete_work: dict, project_path: str = None
    ) -> str:
        """Create a detailed prompt to continue incomplete work"""
        prompt = f"""
        URGENT CONTINUATION TASK for {agent_name}:
        
        Your previous work was incomplete. Here's the detailed analysis:
        
        MISSING DELIVERABLES: {incomplete_work.get('missing_items', [])}
        TRUNCATION INDICATORS: {incomplete_work.get('truncation_indicators', [])}
        CODE ISSUES: {incomplete_work.get('code_issues', [])}
        COMPLETION STATUS: {incomplete_work.get('completion_percentage', 0):.1f}%
        
        """

        # Add specific instructions based on issues found
        if incomplete_work.get("truncation_indicators"):
            prompt += """
        CRITICAL: Your previous output was truncated mid-sentence/mid-code. 
        You MUST complete the code that was cut off and continue until ALL deliverables are complete.
        """

        if incomplete_work.get("code_issues"):
            prompt += """
        CODE QUALITY ISSUES DETECTED: 
        Please fix these specific issues and complete all incomplete code structures.
        """

        # Add current project state if available
        if project_path:
            try:
                import os

                existing_files = []
                for root, dirs, files in os.walk(project_path):
                    for file in files:
                        if file.endswith((".dart", ".yaml", ".json", ".md")):
                            rel_path = os.path.relpath(
                                os.path.join(root, file), project_path
                            )
                            existing_files.append(rel_path)

                if existing_files:
                    prompt += f"""
        
        CURRENT PROJECT STATE:
        Existing files: {existing_files}
        
        Please read these files and build upon them. DO NOT recreate existing work.
        """
            except:
                pass

        prompt += """
        
        COMPLETION REQUIREMENTS:
        1. Complete ALL missing deliverables
        2. Fix ALL truncated/incomplete code
        3. Ensure ALL files are syntactically correct
        4. Verify ALL imports resolve correctly
        5. Use file_system tool to write COMPLETE files
        6. DO NOT stop until everything is finished
        
        CRITICAL: Continue working until you have addressed every single issue listed above.
        """

        return prompt


# Progressive Enhancement System
class ProgressiveEnhancement:
    """
    Ensures agents build upon existing work rather than recreating.
    Uses mas.Trigger to coordinate progressive development.
    """

    def __init__(self, project_path: str):
        self.project_path = project_path
        self.enhancement_trigger = mas.Trigger(
            name="progressive_enhancement",
            description="Triggered when agents should enhance existing work",
            condition_string="existing_work_detected or agent_handoff",
        )

    def analyze_existing_work(self, agent_name: str) -> dict:
        """Analyze what work already exists for progressive enhancement"""
        import os

        existing_files = []

        for root, dirs, files in os.walk(self.project_path):
            for file in files:
                if file.endswith((".dart", ".yaml", ".json", ".md")):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r") as f:
                            content = f.read()
                        existing_files.append(
                            {
                                "path": file_path,
                                "size": len(content),
                                "type": file.split(".")[-1],
                                "content_preview": content[:200] + "..."
                                if len(content) > 200
                                else content,
                            }
                        )
                    except:
                        continue

        return {
            "existing_files": existing_files,
            "project_structure": self._analyze_project_structure(),
            "enhancement_opportunities": self._identify_enhancement_opportunities(
                existing_files
            ),
        }

    def _analyze_project_structure(self) -> dict:
        """Analyze the current project structure"""
        structure = {}
        import os

        for root, dirs, files in os.walk(self.project_path):
            rel_root = os.path.relpath(root, self.project_path)
            structure[rel_root] = {
                "directories": dirs,
                "files": files,
                "dart_files": [f for f in files if f.endswith(".dart")],
                "config_files": [f for f in files if f.endswith((".yaml", ".json"))],
            }

        return structure

    def _identify_enhancement_opportunities(self, existing_files: list) -> list:
        """Identify opportunities for progressive enhancement"""
        opportunities = []

        # Check for incomplete files
        for file_info in existing_files:
            if file_info["size"] < 100:  # Very small files might be incomplete
                opportunities.append(
                    f"Enhance {file_info['path']} - appears incomplete"
                )

        # Check for missing common files
        file_paths = [f["path"] for f in existing_files]
        common_files = ["pubspec.yaml", "main.dart", "README.md"]

        for common_file in common_files:
            if not any(common_file in path for path in file_paths):
                opportunities.append(f"Create missing {common_file}")

        return opportunities


# Validation Gates System
class ValidationGates:
    """
    Implements validation gates between agent phases.
    Uses mas.Automation to ensure completeness before handoff.
    """

    def __init__(self, project_path: str):
        self.project_path = project_path
        self.validation_trigger = mas.Trigger(
            name="validation_gates",
            description="Validates agent work before phase transitions",
            condition_string="agent_completion or phase_transition",
        )

    async def validate_agent_work(
        self, agent_name: str, expected_deliverables: list
    ) -> dict:
        """Validate that agent work meets requirements with comprehensive checks"""
        validation_result = {
            "agent": agent_name,
            "passed": True,
            "issues": [],
            "missing_deliverables": [],
            "compilation_issues": [],
            "recommendations": [],
        }

        # Check for expected deliverables
        for deliverable in expected_deliverables:
            if not self._check_deliverable_exists(deliverable):
                validation_result["missing_deliverables"].append(deliverable)
                validation_result["passed"] = False

        # Check code quality
        quality_issues = self._check_code_quality()
        if quality_issues:
            validation_result["issues"].extend(quality_issues)
            validation_result["passed"] = False

        # Check Flutter compilation if we have Dart files
        dart_files_exist = any(
            f.endswith(".dart")
            for root, dirs, files in __import__("os").walk(self.project_path)
            for f in files
        )
        if dart_files_exist:
            compilation_issues = await self._check_flutter_compilation()
            if compilation_issues:
                validation_result["compilation_issues"].extend(compilation_issues)
                validation_result["passed"] = False

        # Generate recommendations
        if not validation_result["passed"]:
            validation_result["recommendations"] = self._generate_recommendations(
                validation_result
            )

        return validation_result

    def _check_deliverable_exists(self, deliverable: str) -> bool:
        """Check if a deliverable exists"""
        import os

        deliverable_path = os.path.join(self.project_path, deliverable)
        return os.path.exists(deliverable_path)

    def _check_code_quality(self) -> list:
        """Check code quality issues including compilation"""
        issues = []
        import os

        # Check Dart file quality
        for root, dirs, files in os.walk(self.project_path):
            for file in files:
                if file.endswith(".dart"):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r") as f:
                            content = f.read()

                        # Basic syntax checks
                        if len(content) < 50:
                            issues.append(f"{file_path} appears too small/incomplete")
                        if content.count("{") != content.count("}"):
                            issues.append(f"{file_path} has mismatched braces")
                        if content.count("(") != content.count(")"):
                            issues.append(f"{file_path} has mismatched parentheses")
                        if "TODO" in content or "FIXME" in content:
                            issues.append(f"{file_path} contains TODO/FIXME markers")

                        # Check for incomplete structures
                        if content.strip().endswith(
                            ("class", "void", "String", "Widget", "get", "set", "{")
                        ):
                            issues.append(f"{file_path} has incomplete code structure")

                        # Check for proper imports
                        if "import " in content:
                            import_lines = [
                                line.strip()
                                for line in content.split("\n")
                                if line.strip().startswith("import")
                            ]
                            for import_line in import_lines:
                                if not import_line.endswith(";"):
                                    issues.append(
                                        f"{file_path} has incomplete import: {import_line}"
                                    )

                        # Check for unmatched quotes
                        single_quotes = content.count("'")
                        double_quotes = content.count('"')
                        if single_quotes % 2 != 0:
                            issues.append(f"{file_path} has unmatched single quotes")
                        if double_quotes % 2 != 0:
                            issues.append(f"{file_path} has unmatched double quotes")

                    except Exception as e:
                        issues.append(f"Could not read {file_path}: {str(e)}")

        # Check if pubspec.yaml is valid
        pubspec_path = os.path.join(self.project_path, "pubspec.yaml")
        if os.path.exists(pubspec_path):
            try:
                with open(pubspec_path, "r") as f:
                    content = f.read()
                if "name:" not in content:
                    issues.append(f"pubspec.yaml missing name field")
                if "dependencies:" not in content:
                    issues.append(f"pubspec.yaml missing dependencies section")
            except Exception as e:
                issues.append(f"Could not read pubspec.yaml: {str(e)}")
        else:
            issues.append("pubspec.yaml file missing")

        return issues

    async def _check_flutter_compilation(self) -> list:
        """Check if Flutter project compiles successfully"""
        issues = []
        import asyncio
        import os

        # Check if pubspec.yaml exists first
        pubspec_path = os.path.join(self.project_path, "pubspec.yaml")
        if not os.path.exists(pubspec_path):
            return ["pubspec.yaml missing - cannot check compilation"]

        try:
            # Run flutter analyze
            proc = await asyncio.create_subprocess_shell(
                "flutter analyze",
                cwd=self.project_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                analyze_output = stdout.decode() + stderr.decode()
                issues.append(f"Flutter analyze failed: {analyze_output}")

            # Run dart analyze for additional checks
            proc = await asyncio.create_subprocess_shell(
                "dart analyze",
                cwd=self.project_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                dart_output = stdout.decode() + stderr.decode()
                issues.append(f"Dart analyze failed: {dart_output}")

        except Exception as e:
            issues.append(f"Could not run compilation checks: {str(e)}")

        return issues

    def _generate_recommendations(self, validation_result: dict) -> list:
        """Generate recommendations based on validation results"""
        recommendations = []

        if validation_result["missing_deliverables"]:
            recommendations.append("Complete missing deliverables before proceeding")

        if validation_result["issues"]:
            recommendations.append("Fix code quality issues identified")

        recommendations.append("Re-run validation after fixes")

        return recommendations


# Define our own decorator for comprehensive logging
def comprehensive_async_log_decorator(logger_name):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Use MAS logger directly from utils
            from multiagenticswarm.utils.logger import get_logger

            logger = get_logger(logger_name)
            logger.info(f"Starting {func.__name__}")
            start_time = __import__("time").time()
            try:
                result = await func(*args, **kwargs)
                duration = __import__("time").time() - start_time
                logger.info(f"Completed {func.__name__} in {duration:.2f}s")
                return result
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                raise

        return wrapper

    return decorator


# Add it to the mas module if it doesn't exist
if not hasattr(mas, "comprehensive_async_log_decorator"):
    mas.comprehensive_async_log_decorator = comprehensive_async_log_decorator

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
        enable_comprehensive_logging: bool = True,
        verbose_logging: bool = False,
        **kwargs,
    ):
        # Initialize coordination systems to fix isolation issues
        self.shared_memory = SharedProjectMemory(project_path)
        self.task_continuation = TaskContinuation(project_path)
        self.progressive_enhancement = ProgressiveEnhancement(project_path)
        self.validation_gates = ValidationGates(project_path)

        # Auto-initialize comprehensive logging for universal coverage
        if enable_comprehensive_logging:
            from multiagenticswarm.logging import setup_logging

            log_config = setup_logging(
                verbose=verbose_logging,
                log_directory=kwargs.get(
                    "log_directory",
                    os.path.join(
                        os.path.dirname(os.path.abspath(project_path)), "logs"
                    ),
                ),
                enable_json_logs=True,
            )

            # Import MAS logging module
            import multiagenticswarm.logging as mas_logging

            print(f"🔍 FlutterSwarm: Comprehensive logging initialized")
            print(f"📁 Log directory: {log_config.get('log_directory', 'None')}")
            print(f"🆔 Session ID: {log_config.get('session_id', 'None')}")

            # Store the logging configuration for future reference
            self.log_config = log_config

        # Initialize using BaseSwarm (which inherits from MAS System)
        super().__init__(
            name="FlutterSwarm",
            project_path=project_path,
            system=system,
            llm_provider=llm_provider,
            llm_model=llm_model,
            **kwargs,
        )

        # Setup detailed logging for the swarm
        from multiagenticswarm.utils.logger import get_logger

        self.logger = get_logger("flutterswarm")
        self.logger.info(f"FlutterSwarm initialized with project path: {project_path}")
        self.logger.info(f"Using LLM provider: {llm_provider}, model: {llm_model}")

        # Register additional log handlers for comprehensive logging
        if hasattr(mas, "logging"):
            mas.logging.log_info(
                f"FlutterSwarm initialized with project path: {project_path}",
                component="flutterswarm",
                operation="initialization",
            )
        self.logger.log_swarm_operation(
            "FlutterSwarm",
            "initialization",
            {
                "project_path": project_path,
                "llm_provider": llm_provider,
                "llm_model": llm_model,
            },
        )

        self._setup_tools()
        self._setup_agents()
        self._setup_workflows()  # Ensure workflows are registered
        self._validate_tools()

        self.logger.log_swarm_operation(
            "FlutterSwarm", "initialization", status="completed"
        )

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

    @comprehensive_async_log_decorator("flutterswarm.create_app")
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
        Central orchestrator that manually iterates through agents.
        Comprehensive logging captures all operations, LLM interactions, and file operations.
        """

        # Ensure logging is properly set up
        self._ensure_logging_active()

        # Log the start of app creation with comprehensive details
        operation_data = {
            "app_description": app_description,
            "features": features,
            "platforms": platforms,
            "design_requirements": design_requirements or {},
            "performance_requirements": performance_requirements or {},
            "project_path": self.project_path,
            "session_id": getattr(self, "log_config", {}).get("session_id", "unknown"),
        }

        # Log using the standard logger
        self.logger.info(
            f"Starting Flutter app creation: {len(features)} features for platforms {platforms}"
        )

        # Log with comprehensive logging
        import multiagenticswarm.logging as mas_logging

        mas_logging.log_info(
            f"Starting Flutter app creation: {len(features)} features for platforms {platforms}",
            component="flutterswarm",
            operation="create_app",
            metadata=operation_data,
        )

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

        # Initialize execution result aggregation
        all_created_files = []
        all_modified_files = []
        all_outputs = {}
        execution_start_time = __import__("time").time()

        try:
            # Initialize expected deliverables for validation
            architect_deliverables = [
                "pubspec.yaml",
                "main.dart",
                "lib/app.dart",
                "lib/core/",
            ]
            ui_designer_deliverables = ["lib/screens/", "lib/widgets/", "lib/theme/"]
            developer_deliverables = ["lib/services/", "lib/models/", "lib/providers/"]
            tester_deliverables = ["test/", "integration_test/"]

            # Step 1: Architect - Design system architecture
            # Get enhanced context from shared memory
            architect_enhanced_context = self.shared_memory.get_context_for_agent(
                "architect"
            )
            architect_enhanced_context.update(context)

            # Log the step with comprehensive details
            step_info = {
                "step": "architect_design",
                "step_number": 1,
                "agent": "flutter_architect",
                "inputs": {
                    "app_description": app_description,
                    "features": features,
                    "platforms": platforms,
                    "design_requirements": design_requirements,
                    "performance_requirements": performance_requirements,
                },
            }

            # Log using standard logger
            self.logger.log_workflow_step(
                "create_flutter_app",
                "architect_design",
                1,
                "flutter_architect",
                "started",
            )

            # Log with enhanced MAS logging system
            try:
                import multiagenticswarm.logging as mas_logging

                mas_logging.log_info(
                    f"Starting architecture design with flutter_architect",
                    component="flutterswarm.workflow",
                    operation="architect_design",
                    metadata=step_info,
                )
            except (ImportError, AttributeError):
                pass

            architect_context = TaskContext(
                project_path=self.project_path, metadata=context
            )
            # First analyze requirements, then design architecture
            requirements_analysis = {
                "app_description": app_description,
                "features": features,
                "platforms": platforms,
                "design_requirements": design_requirements or {},
                "performance_requirements": performance_requirements or {},
            }
            architect_result = await self.architect.design_architecture(
                requirements_analysis=requirements_analysis, context=architect_context
            )

            # Log detailed architect results
            self.logger.log_workflow_step(
                "create_flutter_app",
                "architect_design",
                1,
                "flutter_architect",
                "completed" if architect_result.success else "failed",
                input_data=requirements_analysis,
                output_data=architect_result.output,
            )

            # Ensure architect work is fully complete using recursive continuation
            if architect_result.success:
                architect_result = await self.ensure_agent_work_completion(
                    "architect",
                    architect_result,
                    architect_deliverables,
                    architect_enhanced_context,
                )

                # Validate architect deliverables
                validation_result = await self.validation_gates.validate_agent_work(
                    "architect", architect_deliverables
                )
                if not validation_result["passed"]:
                    self.logger.error(
                        f"Architect validation failed: {validation_result['issues']}"
                    )
                    if validation_result.get("compilation_issues"):
                        self.logger.error(
                            f"Architect compilation issues: {validation_result['compilation_issues']}"
                        )

                all_outputs["architect"] = architect_result.output
                context["architect_result"] = architect_result.output
            else:
                self.logger.error(f"Architect failed: {architect_result.error_message}")
                return ExecutionResult(
                    success=False,
                    agent_name="FlutterSwarm",
                    task_id="create_flutter_app",
                    error_message=f"Architect failed: {architect_result.error_message}",
                    execution_time=__import__("time").time() - execution_start_time,
                    metadata=context,
                )

            # Step 2: UI Designer - Create UI designs
            # Get enhanced context including progressive enhancement analysis
            ui_designer_enhanced_context = self.shared_memory.get_context_for_agent(
                "ui_designer"
            )
            progressive_analysis = self.progressive_enhancement.analyze_existing_work(
                "ui_designer"
            )
            ui_designer_enhanced_context.update(
                {
                    **context,
                    "architecture_design": architect_result.output,
                    "existing_work_analysis": progressive_analysis,
                }
            )

            self.logger.log_workflow_step(
                "create_flutter_app", "ui_design", 2, "flutter_ui_designer", "started"
            )
            ui_designer_context = TaskContext(
                project_path=self.project_path,
                metadata=ui_designer_enhanced_context,
            )
            ui_designer_result = await self.ui_designer.design_ui(
                context=ui_designer_context
            )

            # Log detailed UI designer results
            self.logger.log_workflow_step(
                "create_flutter_app",
                "ui_design",
                2,
                "flutter_ui_designer",
                "completed" if ui_designer_result.success else "failed",
                input_data=ui_designer_context.metadata,
                output_data=ui_designer_result.output,
            )

            # Ensure UI designer work is fully complete using recursive continuation
            if ui_designer_result.success:
                ui_designer_result = await self.ensure_agent_work_completion(
                    "ui_designer",
                    ui_designer_result,
                    ui_designer_deliverables,
                    ui_designer_enhanced_context,
                )

                # Validate UI designer deliverables
                validation_result = await self.validation_gates.validate_agent_work(
                    "ui_designer", ui_designer_deliverables
                )
                if not validation_result["passed"]:
                    self.logger.error(
                        f"UI Designer validation failed: {validation_result['issues']}"
                    )
                    if validation_result.get("compilation_issues"):
                        self.logger.error(
                            f"UI Designer compilation issues: {validation_result['compilation_issues']}"
                        )

                all_outputs["ui_designer"] = ui_designer_result.output
                context["ui_design"] = ui_designer_result.output
            else:
                self.logger.error(
                    f"UI Designer failed: {ui_designer_result.error_message}"
                )
                return ExecutionResult(
                    success=False,
                    agent_name="FlutterSwarm",
                    task_id="create_flutter_app",
                    error_message=f"UI Designer failed: {ui_designer_result.error_message}",
                    execution_time=__import__("time").time() - execution_start_time,
                    metadata=context,
                )

            # Step 3: Developer - Implement features
            # Get enhanced context with full project knowledge
            developer_enhanced_context = self.shared_memory.get_context_for_agent(
                "developer"
            )
            progressive_analysis = self.progressive_enhancement.analyze_existing_work(
                "developer"
            )
            developer_enhanced_context.update(
                {
                    **context,
                    "ui_design": ui_designer_result.output,
                    "existing_work_analysis": progressive_analysis,
                }
            )

            self.logger.log_workflow_step(
                "create_flutter_app",
                "feature_implementation",
                3,
                "flutter_developer",
                "started",
            )
            developer_context = TaskContext(
                project_path=self.project_path,
                metadata=developer_enhanced_context,
            )
            developer_result = await self.developer.implement_feature(
                feature_description=f"Implement all features: {', '.join(features)}",
                project_context=developer_context,
            )

            # Log detailed developer results
            self.logger.log_workflow_step(
                "create_flutter_app",
                "feature_implementation",
                3,
                "flutter_developer",
                "completed" if developer_result.success else "failed",
                input_data=f"Implement all features: {', '.join(features)}",
                output_data=developer_result.output,
            )

            # Ensure developer work is fully complete using recursive continuation
            if developer_result.success:
                developer_result = await self.ensure_agent_work_completion(
                    "developer",
                    developer_result,
                    developer_deliverables,
                    developer_enhanced_context,
                )

                # Validate developer deliverables
                validation_result = await self.validation_gates.validate_agent_work(
                    "developer", developer_deliverables
                )
                if not validation_result["passed"]:
                    self.logger.error(
                        f"Developer validation failed: {validation_result['issues']}"
                    )
                    if validation_result.get("compilation_issues"):
                        self.logger.error(
                            f"Developer compilation issues: {validation_result['compilation_issues']}"
                        )

                all_outputs["developer"] = developer_result.output
                context["implementation"] = developer_result.output
            else:
                self.logger.error(f"Developer failed: {developer_result.error_message}")
                return ExecutionResult(
                    success=False,
                    agent_name="FlutterSwarm",
                    task_id="create_flutter_app",
                    error_message=f"Developer failed: {developer_result.error_message}",
                    execution_time=__import__("time").time() - execution_start_time,
                    metadata=context,
                )

            # Step 4: Tester - Create tests
            # Get enhanced context with full project knowledge
            tester_enhanced_context = self.shared_memory.get_context_for_agent("tester")
            progressive_analysis = self.progressive_enhancement.analyze_existing_work(
                "tester"
            )
            tester_enhanced_context.update(
                {
                    **context,
                    "implementation": developer_result.output,
                    "existing_work_analysis": progressive_analysis,
                }
            )

            self.logger.info("Step 4: Tester creating tests...")
            tester_context = TaskContext(
                project_path=self.project_path,
                metadata=tester_enhanced_context,
            )
            tester_result = await self.tester.write_tests(context=tester_context)

            # Ensure tester work is fully complete using recursive continuation
            if tester_result.success:
                tester_result = await self.ensure_agent_work_completion(
                    "tester",
                    tester_result,
                    tester_deliverables,
                    tester_enhanced_context,
                )

                # Validate tester deliverables
                validation_result = await self.validation_gates.validate_agent_work(
                    "tester", tester_deliverables
                )
                if not validation_result["passed"]:
                    self.logger.warning(
                        f"Tester validation failed: {validation_result['issues']}"
                    )
                    if validation_result.get("compilation_issues"):
                        self.logger.warning(
                            f"Tester compilation issues: {validation_result['compilation_issues']}"
                        )

                all_outputs["tester"] = tester_result.output
            else:
                self.logger.warning(
                    f"Tester failed but continuing: {tester_result.error_message}"
                )
                all_outputs["tester"] = tester_result.error_message

            # Final Integration Phase - Ensure all pieces fit together
            self.logger.info("Starting final integration phase...")
            final_validation = await self.validation_gates.validate_agent_work(
                "final_integration",
                architect_deliverables
                + ui_designer_deliverables
                + developer_deliverables
                + tester_deliverables,
            )

            if not final_validation["passed"]:
                self.logger.error(
                    f"Final integration validation failed: {final_validation['issues']}"
                )
                # Create repair tasks for any missing pieces
                for issue in final_validation["issues"]:
                    self.logger.warning(f"Integration issue: {issue}")

            # Update final project state in shared memory
            final_project_state = {
                "all_agent_outputs": all_outputs,
                "final_validation": final_validation,
                "project_structure": self.progressive_enhancement.analyze_existing_work(
                    "final_integration"
                ),
                "completion_timestamp": __import__("datetime")
                .datetime.now()
                .isoformat(),
            }
            self.shared_memory.update_memory(
                "final_integration", final_project_state, context
            )

            # Aggregate results
            execution_time = __import__("time").time() - execution_start_time

            # Create final execution result
            final_result = ExecutionResult(
                success=True,
                agent_name="FlutterSwarm",
                task_id="create_flutter_app",
                output=all_outputs,
                execution_time=execution_time,
                metadata={
                    **context,
                    "created_files": all_created_files,
                    "modified_files": all_modified_files,
                    "agent_results": all_outputs,
                    "shared_memory_state": self.shared_memory.memory,
                    "final_validation": final_validation,
                    "coordination_systems": {
                        "shared_memory": "active",
                        "task_continuation": "active",
                        "progressive_enhancement": "active",
                        "validation_gates": "active",
                    },
                },
            )

            self.logger.info(
                f"Flutter app creation completed successfully in {execution_time:.2f}s"
            )
            return final_result

        except Exception as e:
            self.logger.error(f"App creation failed with exception: {str(e)}")
            return ExecutionResult(
                success=False,
                agent_name="FlutterSwarm",
                task_id="create_flutter_app",
                error_message=f"App creation failed: {str(e)}",
                execution_time=__import__("time").time() - execution_start_time,
                metadata=context,
            )

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

    async def ensure_agent_work_completion(
        self,
        agent_name: str,
        agent_result: ExecutionResult,
        expected_deliverables: list,
        enhanced_context: dict,
    ) -> ExecutionResult:
        """
        Ensure agent work is fully complete using recursive continuation.
        This is the core fix for the completion problem.
        """
        if not agent_result.success:
            return agent_result

        # Extract output text
        output_text = ""
        if hasattr(agent_result, "output"):
            if isinstance(agent_result.output, dict):
                for key in ["content", "response", "output", "message"]:
                    if key in agent_result.output:
                        output_text = str(agent_result.output[key])
                        break
                if not output_text:
                    output_text = str(agent_result.output)
            else:
                output_text = str(agent_result.output)

        # Parse and execute initial code
        if output_text:
            await self._parse_and_execute_code(output_text)

        # Update shared memory with initial results
        self.shared_memory.update_memory(
            agent_name, agent_result.output, enhanced_context
        )

        # Recursive continuation loop until work is complete
        max_continuations = 5
        continuation_count = 0
        last_successful_output = output_text

        while continuation_count < max_continuations:
            incompleteness_check = self.task_continuation.detect_incomplete_work(
                last_successful_output, expected_deliverables, self.project_path
            )

            if not incompleteness_check["is_incomplete"]:
                self.logger.info(
                    f"{agent_name} work completed successfully after {continuation_count} continuations"
                )
                break

            continuation_count += 1
            self.logger.warning(
                f"{agent_name} work incomplete (attempt {continuation_count}): {incompleteness_check['completion_percentage']}%"
            )

            # Log specific issues found
            if incompleteness_check.get("truncation_indicators"):
                self.logger.warning(
                    f"Truncation indicators: {incompleteness_check['truncation_indicators']}"
                )
            if incompleteness_check.get("code_issues"):
                self.logger.warning(
                    f"Code issues: {incompleteness_check['code_issues']}"
                )
            if incompleteness_check.get("missing_items"):
                self.logger.warning(
                    f"Missing items: {incompleteness_check['missing_items']}"
                )

            continuation_prompt = self.task_continuation.create_continuation_prompt(
                agent_name, incompleteness_check, self.project_path
            )

            # Get the appropriate agent
            agent_mapping = {
                "architect": self.architect,
                "developer": self.developer,
                "ui_designer": self.ui_designer,
                "tester": self.tester,
            }

            agent = agent_mapping.get(agent_name)
            if not agent:
                self.logger.error(f"Unknown agent: {agent_name}")
                break

            # Continue the agent's work
            continuation_context = TaskContext(
                project_path=self.project_path, metadata=enhanced_context
            )
            continuation_result = await agent.execute(
                continuation_prompt, continuation_context
            )

            if continuation_result.success:
                # Parse and execute continuation code
                continuation_output = str(continuation_result.output)
                if continuation_output:
                    await self._parse_and_execute_code(continuation_output)
                    last_successful_output = (
                        continuation_output  # Update for next iteration
                    )

                # Update memory with continuation results
                self.shared_memory.update_memory(
                    f"{agent_name}_continuation_{continuation_count}",
                    continuation_result.output,
                    enhanced_context,
                )
            else:
                self.logger.error(
                    f"{agent_name} continuation {continuation_count} failed: {continuation_result.error_message}"
                )
                break

        if continuation_count >= max_continuations:
            self.logger.error(
                f"{agent_name} failed to complete work after {max_continuations} attempts"
            )
            return ExecutionResult(
                success=False,
                error_message=f"Agent {agent_name} could not complete work after {max_continuations} attempts",
                agent_name=agent_name,
                task_id="ensure_completion",
            )

        # Return the original result (now with completed work)
        return agent_result

    async def resume_incomplete_agent_work(
        self, agent_name: str, incomplete_work: dict
    ) -> ExecutionResult:
        """
        Resume incomplete agent work using the continuation mechanism.
        This method implements the core continuation functionality.
        """
        self.logger.info(f"Resuming incomplete work for agent: {agent_name}")

        # Get enhanced context from shared memory
        enhanced_context = self.shared_memory.get_context_for_agent(agent_name)

        # Create continuation prompt
        continuation_prompt = self.task_continuation.create_continuation_prompt(
            agent_name, incomplete_work
        )

        # Get the appropriate agent
        agent_mapping = {
            "architect": self.architect,
            "developer": self.developer,
            "ui_designer": self.ui_designer,
            "tester": self.tester,
        }

        agent = agent_mapping.get(agent_name)
        if not agent:
            return ExecutionResult(
                success=False,
                error_message=f"Unknown agent: {agent_name}",
                agent_name=agent_name,
                task_id="resume_work",
            )

        # Create task context for continuation
        continuation_context = TaskContext(
            project_path=self.project_path, metadata=enhanced_context
        )

        try:
            # Execute continuation task
            continuation_result = await agent.execute(
                continuation_prompt, continuation_context
            )

            if continuation_result.success:
                # Parse and execute any code blocks
                output_text = str(continuation_result.output)
                if output_text:
                    await self._parse_and_execute_code(output_text)

                # Update shared memory with continuation results
                self.shared_memory.update_memory(
                    f"{agent_name}_continuation",
                    continuation_result.output,
                    enhanced_context,
                )

                self.logger.info(f"Successfully resumed work for agent: {agent_name}")
                return continuation_result
            else:
                self.logger.error(
                    f"Failed to resume work for agent {agent_name}: {continuation_result.error_message}"
                )
                return continuation_result

        except Exception as e:
            self.logger.error(
                f"Exception during agent resumption for {agent_name}: {str(e)}"
            )
            return ExecutionResult(
                success=False,
                error_message=f"Exception during resumption: {str(e)}",
                agent_name=agent_name,
                task_id="resume_work",
            )

    def _ensure_logging_active(self):
        """Ensure that logging is properly configured and active"""
        # Use MultiAgenticSwarm logging
        import multiagenticswarm.logging as mas_logging

        # Ensure log directory exists
        log_dir = getattr(
            self, "log_directory", os.path.join(self.project_path, "../logs")
        )
        os.makedirs(log_dir, exist_ok=True)

        # Initialize logging if not already done
        log_config = mas_logging.setup_logging(
            verbose=True, log_directory=log_dir, enable_json_logs=True
        )

        # Store the logging configuration
        self.log_config = log_config
        self.logger.info(f"Logging initialized: {log_config}")

        return True
