"""
Flutter CLI wrapper - ONLY executes commands, contains ZERO Flutter logic.
All decisions about WHAT commands to run come from LLMs.
"""
import os
import subprocess
import logging
from typing import Dict, Any, List, Optional, Union
import shutil
import asyncio
import psutil
import time
import json
import re

try:
    import multiagenticswarm as mas
    from multiagenticswarm.core.base_tool import FunctionTool
    MAS_AVAILABLE = True
except ImportError:
    MAS_AVAILABLE = False
    mas = None
    FunctionTool = None
    mas = None
    FunctionTool = None


class FlutterCLITool:
    """
    Robust Flutter CLI wrapper with comprehensive error handling.
    LLM decides what commands to run - this tool just executes them safely.
    """

    def __init__(self, working_directory: str = ".", name: str = "flutter_cli"):
        self.working_directory = os.path.abspath(working_directory)
        self.name = name
        self.description = "Execute Flutter CLI commands with robust error handling"
        self.logger = mas.get_logger(f"flutterswarm.{name}") if MAS_AVAILABLE else logging.getLogger(f"flutterswarm.{name}")

        # Ensure working directory exists
        os.makedirs(self.working_directory, exist_ok=True)

        # Note: Flutter SDK verification should be done asynchronously, not in constructor
        # Call verify_flutter_sdk() separately when needed to avoid blocking initialization

        # Cache for Flutter doctor and device info
        self._doctor_cache = None
        self._devices_cache = None
        self._cache_time = 0
        self._cache_duration = 300  # 5 minutes

    def verify_flutter_sdk(self) -> None:
        """Verify Flutter SDK is properly installed - call this separately, not in constructor"""
        try:
            # Check if flutter command exists
            if not shutil.which("flutter"):
                raise RuntimeError("Flutter SDK not found in PATH. Please install Flutter and add it to PATH.")

            # Check Flutter version
            result = subprocess.run(
                ["flutter", "--version"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.working_directory
            )

            if result.returncode != 0:
                raise RuntimeError(f"Flutter SDK error: {result.stderr}")

            version_info = result.stdout.strip().split('\n')[0] if result.stdout else "Unknown version"
            self.logger.info(f"Flutter SDK verified: {version_info}")

        except subprocess.TimeoutExpired:
            raise RuntimeError("Flutter SDK verification timed out")
        except Exception as e:
            self.logger.error(f"Flutter SDK verification failed: {e}")
            raise

    async def execute(self, command: str, args: Optional[List[str]] = None, timeout: int = 120) -> Dict[str, Any]:
        """Execute a Flutter CLI command asynchronously with error handling."""
        cmd = ["flutter"] + command.split()
        if args:
            cmd += args
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.working_directory,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return {"success": False, "error": "Flutter command timed out."}
            output = stdout.decode()
            error = stderr.decode()
            if proc.returncode != 0:
                parsed_error = self._parse_flutter_error(error)
                return {"success": False, "output": output, "error": parsed_error}
            return {"success": True, "output": output}
        except Exception as e:
            self.logger.error(f"Flutter CLI execution failed: {e}")
            return {"success": False, "error": str(e)}

    def _parse_flutter_error(self, error_output: str) -> str:
        # Simple error parsing for actionable feedback
        if "No such file or directory" in error_output:
            return "File or directory not found. Check your project path."
        if "not found" in error_output and "flutter" in error_output:
            return "Flutter SDK not found. Please install Flutter."
        if "pub get failed" in error_output:
            return "Dependency resolution failed. Check your pubspec.yaml."
        return error_output.strip()

    async def health_check(self) -> Dict[str, Any]:
        """Check if Flutter CLI is available and working."""
        try:
            result = await self.execute("--version", timeout=10)
            if result.get("success"):
                return {"healthy": True, "version": result.get("output")}
            return {"healthy": False, "error": result.get("error")}
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    def _check_flutter_doctor(self) -> Dict[str, Any]:
        """Check Flutter doctor status with caching"""
        current_time = time.time()

        if self._doctor_cache and (current_time - self._cache_time) < self._cache_duration:
            return self._doctor_cache

        try:
            result = subprocess.run(
                ["flutter", "doctor", "--machine"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.working_directory
            )

            if result.returncode == 0:
                try:
                    doctor_data = json.loads(result.stdout)
                    self._doctor_cache = {
                        "success": True,
                        "data": doctor_data,
                        "issues": [item for item in doctor_data if item.get("statusInfo") == "partial" or item.get("statusInfo") == "notAvailable"]
                    }
                except json.JSONDecodeError:
                    self._doctor_cache = {
                        "success": False,
                        "error": "Failed to parse doctor output",
                        "issues": ["Flutter doctor output parsing failed"]
                    }
            else:
                self._doctor_cache = {
                    "success": False,
                    "error": result.stderr,
                    "issues": ["Flutter doctor check failed"]
                }

            self._cache_time = current_time
            return self._doctor_cache

        except Exception as e:
            self._doctor_cache = {
                "success": False,
                "error": str(e),
                "issues": ["Flutter doctor check failed"]
            }
            return self._doctor_cache

    def _validate_project_name(self, project_name: str) -> bool:
        """Validate Flutter project name"""
        # Flutter project names must follow Dart package naming conventions
        pattern = r'^[a-z][a-z0-9_]*[a-z0-9]$'
        return bool(re.match(pattern, project_name)) and len(project_name) >= 2

    async def create_project(
        self,
        project_name: str,
        template: str = None,
        org: str = None,
        platforms: List[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a new Flutter project with validation"""

        # Validate project name
        if not self._validate_project_name(project_name):
            return {
                "success": False,
                "error": "Invalid project name",
                "suggestion": "Use lowercase letters, numbers, and underscores only (e.g., 'my_app')"
            }

        # Check if project already exists
        project_path = os.path.join(self.working_directory, project_name)
        if os.path.exists(project_path):
            return {
                "success": False,
                "error": f"Project '{project_name}' already exists",
                "suggestion": "Choose a different name or remove existing project"
            }

        # Check available disk space (require at least 500MB)
        try:
            stat = shutil.disk_usage(self.working_directory)
            free_space = stat.free / (1024 * 1024)  # MB
            if free_space < 500:
                return {
                    "success": False,
                    "error": "Insufficient disk space",
                    "suggestion": f"At least 500MB required, {free_space:.0f}MB available"
                }
        except Exception:
            pass  # Skip disk space check if it fails

        # Build arguments
        args = [project_name]
        options = {}

        if template:
            options["--template"] = template
        if org:
            options["--org"] = org
        if platforms:
            options["--platforms"] = ",".join(platforms)

        # Add any additional options
        options.update(kwargs)

        # Execute create command
        result = await self.execute("create", args, options, timeout=600, check_doctor=True)

        # If creation failed, try to clean up
        if not result["success"] and os.path.exists(project_path):
            try:
                shutil.rmtree(project_path)
                self.logger.info(f"Cleaned up failed project creation: {project_path}")
            except Exception as e:
                self.logger.warning(f"Failed to clean up project: {e}")

        return result

    async def get_devices(self) -> Dict[str, Any]:
        """Get available devices with caching"""
        current_time = time.time()

        if self._devices_cache and (current_time - self._cache_time) < 60:  # Cache for 1 minute
            return self._devices_cache

        result = await self.execute("devices", ["--machine"], timeout=30)

        if result["success"]:
            try:
                devices = json.loads(result["output"])
                self._devices_cache = {
                    "success": True,
                    "devices": devices,
                    "count": len(devices)
                }
            except json.JSONDecodeError:
                self._devices_cache = {
                    "success": False,
                    "error": "Failed to parse devices output",
                    "raw_output": result["output"]
                }
        else:
            self._devices_cache = result

        return self._devices_cache

    async def run_app(
        self,
        device_id: Optional[str] = None,
        hot_reload: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """Run Flutter app with device validation"""

        # Get available devices
        devices_result = await self.get_devices()
        if not devices_result["success"]:
            return {
                "success": False,
                "error": "Failed to get available devices",
                "suggestion": "Connect a device or start an emulator"
            }

        if devices_result["count"] == 0:
            return {
                "success": False,
                "error": "No devices available",
                "suggestion": "Connect a device or start an emulator"
            }

        # Build options
        options = {}
        if device_id:
            options["--device-id"] = device_id
        if hot_reload:
            options["--hot"] = True

        options.update(kwargs)

        return await self.execute("run", [], options, timeout=600)

    async def build_app(
        self,
        target: str = "apk",
        release: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """Build Flutter app"""

        args = [target]
        options = {}

        if release:
            options["--release"] = True

        options.update(kwargs)

        return await self.execute("build", args, options, timeout=1200)

    async def test_app(
        self,
        coverage: bool = False,
        test_file: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Run Flutter tests"""

        args = []
        if test_file:
            args.append(test_file)

        options = {}
        if coverage:
            options["--coverage"] = True

        options.update(kwargs)

        return await self.execute("test", args, options, timeout=300)

    async def pub_get(self) -> Dict[str, Any]:
        """Get Flutter dependencies"""
        return await self.execute("pub", ["get"], timeout=300)

    async def pub_add(self, package: str) -> Dict[str, Any]:
        """Add Flutter dependency"""
        return await self.execute("pub", ["add", package], timeout=300)

    async def pub_upgrade(self) -> Dict[str, Any]:
        """Upgrade Flutter dependencies"""
        return await self.execute("pub", ["upgrade"], timeout=300)

    async def clean_project(self) -> Dict[str, Any]:
        """Clean Flutter project"""
        return await self.execute("clean", [], timeout=60)

    async def analyze_code(self) -> Dict[str, Any]:
        """Analyze Flutter code"""
        return await self.execute("analyze", [], timeout=120)

    async def format_code(self, path: str = ".") -> Dict[str, Any]:
        """Format Flutter code"""
        return await self.execute("format", [path], timeout=60)

    async def doctor(self) -> Dict[str, Any]:
        """Run Flutter doctor"""
        return await self.execute("doctor", [], timeout=60)

    async def custom_command(self, command: str, args: List[str] = None, **kwargs) -> Dict[str, Any]:
        """Execute custom Flutter command"""
        return await self.execute(command, args, kwargs, timeout=300)


def create_flutter_cli_tool(working_directory: str = ".") -> Any:
    """Create a Flutter CLI tool using MAS FunctionTool interface"""

    def flutter_cli_func(command: str, args: List[str] = None, **kwargs) -> Dict[str, Any]:
        """Execute Flutter CLI command - pure interface, no logic"""

        try:
            # Create tool instance
            tool = FlutterCLITool(working_directory)

            # Execute command synchronously for MAS compatibility
            result = tool.execute_sync(command, args, kwargs)

            return result

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "suggestion": "Check Flutter installation and command syntax"
            }

    # Create MAS FunctionTool
    if MAS_AVAILABLE:
        return FunctionTool(
            func=flutter_cli_func,
            name="flutter_cli",
            description="Executes Flutter CLI commands with robust error handling and validation. This tool provides a safe interface to Flutter commands with comprehensive error recovery.",
            parameters={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The Flutter command to execute (e.g., 'create', 'build', 'run', 'test')"
                    },
                    "args": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Arguments for the command"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Command timeout in seconds (default: 300)"
                    },
                    "check_doctor": {
                        "type": "boolean",
                        "description": "Whether to check Flutter doctor before execution"
                    }
                },
                "required": ["command"]
            }
        )

    return None
