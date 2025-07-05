"""
Dart CLI wrapper - ONLY executes commands, contains ZERO Dart logic.
All decisions about WHAT commands to run come from LLMs.
"""
import os
import subprocess
import logging
from typing import Dict, Any, List, Optional

try:
    from multiagenticswarm.core.base_tool import FunctionTool
    import multiagenticswarm as mas
    MAS_AVAILABLE = True
except ImportError:
    MAS_AVAILABLE = False
    FunctionTool = None
    mas = None

def create_dart_cli_tool(working_directory: str = ".") -> Any:
    """Create a Dart CLI tool using MAS Tool interface"""

    def dart_cli_func(command: str, args: List[str] = None, **kwargs) -> Dict[str, Any]:
        """Execute Dart CLI command - pure interface, no logic"""

        # Build command
        cmd = ["dart", command]
        if args:
            cmd.extend(args)

        # Add any additional options
        for key, value in kwargs.items():
            if key.startswith('--'):
                cmd.append(f"{key}={value}")
            else:
                cmd.append(f"--{key}={value}")

        try:
            # Execute in working directory
            result = subprocess.run(
                cmd,
                cwd=working_directory,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "command": " ".join(cmd)
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command timed out",
                "command": " ".join(cmd)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": " ".join(cmd)
            }

    # Create MAS Tool
    if MAS_AVAILABLE:
        return FunctionTool(
            func=dart_cli_func,
            name="dart_cli",
            description="Executes Dart CLI commands. This tool is a pure interface - it has no logic, it only executes the commands you provide.",
            parameters={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The dart command to execute (e.g., 'pub', 'run')."},
                    "args": {"type": "array", "items": {"type": "string"}, "description": "Arguments for the command."},
                },
                "required": ["command"]
            }
        )

    return None

class DartCLITool:
    """
    Simple wrapper around Dart CLI - no logic, just execution.
    LLM decides what commands to run.
    """

    def __init__(self, working_directory: str = ".", name: str = "dart_cli"):
        self.working_directory = working_directory
        self.name = name
        self.description = "Execute Dart CLI commands"
        self.logger = logging.getLogger(f"flutterswarm.{name}")

        # Ensure working directory exists
        os.makedirs(working_directory, exist_ok=True)

        # Create MAS tool
        if MAS_AVAILABLE:
            self.mas_tool = create_dart_cli_tool(working_directory)
        else:
            self.mas_tool = None

    def get_mas_tool(self):
        """Get the MAS tool instance"""
        return self.mas_tool

    async def execute(
        self,
        command: str,
        args: List[str] = None,
        options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute a Dart CLI command.

        Args:
            command: Dart command to execute
            args: Optional command arguments
            options: Optional command options

        Returns:
            Dict with execution results
        """

        # Build command
        cmd = ["dart", command]
        if args:
            cmd.extend(args)

        # Add options
        if options:
            for key, value in options.items():
                if key.startswith('--'):
                    cmd.append(f"{key}={value}")
                else:
                    cmd.append(f"--{key}={value}")

        try:
            # Execute in working directory
            result = subprocess.run(
                cmd,
                cwd=self.working_directory,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "command": " ".join(cmd)
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command timed out",
                "command": " ".join(cmd)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": " ".join(cmd)
            }

    # Convenience methods for common commands - still just wrappers
    async def run(
        self,
        dart_file: str,
        args: List[str] = None
    ) -> Dict[str, Any]:
        """Run a Dart script"""
        cmd_args = ["run", dart_file]
        if args:
            cmd_args.extend(args)
        return await self.execute(cmd_args[0], cmd_args[1:])

    async def compile(
        self,
        dart_file: str,
        output: str = None,
        target: str = "exe"
    ) -> Dict[str, Any]:
        """Compile Dart code"""
        cmd_args = ["compile", target, dart_file]
        if output:
            cmd_args.extend(["-o", output])
        return await self.execute(cmd_args[0], cmd_args[1:])

    async def analyze(
        self,
        path: str = "."
    ) -> Dict[str, Any]:
        """Analyze Dart code"""
        return await self.execute("analyze", [path])

    async def test(
        self,
        test_file: str = None,
        coverage: bool = False
    ) -> Dict[str, Any]:
        """Run Dart tests"""
        cmd_args = ["test"]
        if test_file:
            cmd_args.append(test_file)
        if coverage:
            cmd_args.append("--coverage")
        return await self.execute(cmd_args[0], cmd_args[1:])

    async def pub_get(self) -> Dict[str, Any]:
        """Get Dart dependencies"""
        return await self.execute("pub", ["get"])

    async def pub_add(self, package: str) -> Dict[str, Any]:
        """Add a Dart package"""
        return await self.execute("pub", ["add", package])

    async def pub_upgrade(self) -> Dict[str, Any]:
        """Upgrade Dart packages"""
        return await self.execute("pub", ["upgrade"])

    async def pub_deps(self) -> Dict[str, Any]:
        """List Dart dependencies"""
        return await self.execute("pub", ["deps"])

    async def format(self, path: str = ".") -> Dict[str, Any]:
        """Format Dart code"""
        return await self.execute("format", [path])

    async def create(
        self,
        project_name: str,
        template: str = "console"
    ) -> Dict[str, Any]:
        """Create a new Dart project"""
        return await self.execute("create", ["-t", template, project_name])

    async def fix(self, path: str = ".") -> Dict[str, Any]:
        """Apply Dart fixes"""
        return await self.execute("fix", ["--apply", path])

    async def doc(self, path: str = ".") -> Dict[str, Any]:
        """Generate Dart documentation"""
        return await self.execute("doc", [path])

    async def custom_command(self, command: str, args: List[str] = None) -> Dict[str, Any]:
        """Execute custom Dart command"""
        return await self.execute(command, args or [])


# Create MAS Tool wrapper if available
if MAS_AVAILABLE:
    def DartCLITool_MAS(working_directory: str = "."):
        """Create Dart CLI tool as MAS Tool"""
        return create_dart_cli_tool(working_directory)
