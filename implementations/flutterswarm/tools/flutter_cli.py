"""
Flutter CLI wrapper - ONLY executes commands, contains ZERO Flutter logic.
All decisions about WHAT commands to run come from LLMs.
"""
import os
import subprocess
import logging
from typing import Dict, Any, List, Optional, Union

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
    Simple wrapper around Flutter CLI - no logic, just execution.
    LLM decides what commands to run.
    """

    def __init__(self, working_directory: str = ".", name: str = "flutter_cli"):
        self.working_directory = working_directory
        self.name = name
        self.description = "Execute Flutter CLI commands"
        self.logger = mas.get_logger(f"flutterswarm.{name}") if MAS_AVAILABLE else logging.getLogger(f"flutterswarm.{name}")

        # Ensure working directory exists
        os.makedirs(working_directory, exist_ok=True)

    def execute(self, command: str, args: List[str] = None, **kwargs) -> Dict[str, Any]:
        """Execute Flutter CLI command - pure interface, no logic"""

        # Build command
        cmd = ["flutter", command]
        if args:
            cmd.extend(args)

        # Add any additional options
        for key, value in kwargs.items():
            if key.startswith('--'):
                cmd.append(f"{key}={value}")
            else:
                cmd.append(f"--{key}={value}")

        self.logger.info(f"Executing Flutter command: {' '.join(cmd)}")

        try:
            # Execute in working directory
            result = subprocess.run(
                cmd,
                cwd=self.working_directory,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            response = {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "command": " ".join(cmd)
            }

            if response["success"]:
                self.logger.info(f"Flutter command succeeded: {response['command']}")
            else:
                self.logger.error(f"Flutter command failed: {response['command']}, error: {response['stderr']}")

            return response

        except subprocess.TimeoutExpired:
            error_response = {
                "success": False,
                "error": "Command timed out",
                "command": " ".join(cmd)
            }
            self.logger.error(f"Flutter command timed out: {error_response['command']}")
            return error_response

        except Exception as e:
            error_response = {
                "success": False,
                "error": str(e),
                "command": " ".join(cmd)
            }
            self.logger.error(f"Flutter command exception: {error_response['command']}, error: {str(e)}")
            return error_response

        try:
            # Execute in working directory
            result = subprocess.run(
                cmd,
                cwd=self.working_directory,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            response = {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "command": " ".join(cmd)
            }

            if response["success"]:
                self.logger.info(f"Flutter command succeeded: {response['command']}")
            else:
                self.logger.error(f"Flutter command failed: {response['command']}, error: {response['stderr']}")

            return response

        except subprocess.TimeoutExpired:
            error_response = {
                "success": False,
                "error": "Command timed out",
                "command": " ".join(cmd)
            }
            self.logger.error(f"Flutter command timed out: {error_response['command']}")
            return error_response

        except Exception as e:
            error_response = {
                "success": False,
                "error": str(e),
                "command": " ".join(cmd)
            }
            self.logger.error(f"Flutter command exception: {error_response['command']}, error: {str(e)}")
            return error_response

    # Common Flutter commands as convenience methods
    def create_project(self, project_name: str, **kwargs) -> Dict[str, Any]:
        """Create a new Flutter project"""
        return self.execute("create", [project_name], **kwargs)

    def get_devices(self) -> Dict[str, Any]:
        """List available devices"""
        return self.execute("devices")

    def run_app(self, device_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Run the Flutter app"""
        args = []
        if device_id:
            args.extend(["-d", device_id])
        return self.execute("run", args, **kwargs)

    def build_app(self, target: str = "apk", **kwargs) -> Dict[str, Any]:
        """Build the Flutter app"""
        return self.execute("build", [target], **kwargs)

    def test_app(self, **kwargs) -> Dict[str, Any]:
        """Run tests"""
        return self.execute("test", **kwargs)

    def clean_project(self) -> Dict[str, Any]:
        """Clean the project"""
        return self.execute("clean")

    def pub_get(self) -> Dict[str, Any]:
        """Get dependencies"""
        return self.execute("pub", ["get"])

    def pub_upgrade(self) -> Dict[str, Any]:
        """Upgrade dependencies"""
        return self.execute("pub", ["upgrade"])

    def analyze_code(self) -> Dict[str, Any]:
        """Analyze code"""
        return self.execute("analyze")

    def format_code(self) -> Dict[str, Any]:
        """Format code"""
        return self.execute("format", ["."])


def create_flutter_cli_tool(working_directory: str = ".") -> Any:
    """Create a Flutter CLI tool using MAS FunctionTool interface"""

    def flutter_cli_func(command: str, args: List[str] = None, **kwargs) -> Dict[str, Any]:
        """Execute Flutter CLI command - pure interface, no logic"""

        # Build command
        cmd = ["flutter", command]
        if args:
            cmd.extend(args)

        # Add any additional options
        for key, value in kwargs.items():
            if key.startswith('--'):
                cmd.append(f"{key}={value}")
            else:
                cmd.append(f"--{key}={value}")

        logger = mas.get_logger("flutterswarm.flutter_cli") if MAS_AVAILABLE else logging.getLogger("flutterswarm.flutter_cli")
        logger.info(f"Executing Flutter command: {' '.join(cmd)}")

        try:
            # Execute in working directory
            result = subprocess.run(
                cmd,
                cwd=working_directory,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            response = {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "command": " ".join(cmd)
            }

            if response["success"]:
                logger.info(f"Flutter command succeeded: {response['command']}")
            else:
                logger.error(f"Flutter command failed: {response['command']}, error: {response['stderr']}")

            return response

        except subprocess.TimeoutExpired:
            error_response = {
                "success": False,
                "error": "Command timed out",
                "command": " ".join(cmd)
            }
            logger.error(f"Flutter command timed out: {error_response['command']}")
            return error_response

        except Exception as e:
            error_response = {
                "success": False,
                "error": str(e),
                "command": " ".join(cmd)
            }
            logger.error(f"Flutter command exception: {error_response['command']}, error: {str(e)}")
            return error_response

    # Create MAS FunctionTool
    if MAS_AVAILABLE:
        return FunctionTool(
            func=flutter_cli_func,
            name="flutter_cli",
            description="Execute Flutter CLI commands. Pass 'command' and optional 'args' list.",
            parameters={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Flutter command to execute"},
                    "args": {"type": "array", "items": {"type": "string"}, "description": "Optional command arguments"}
                },
                "required": ["command"]
            }
        )

    return None


# Create MAS Tool wrapper if available
if MAS_AVAILABLE:
    FlutterCLITool_MAS = create_flutter_cli_tool

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
        Execute a Flutter CLI command.

        Args:
            command: Flutter command to execute
            args: Optional command arguments
            options: Optional command options

        Returns:
            Dict with execution results
        """

        # Build command
        cmd = ["flutter", command]
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
    async def create(
        self,
        project_name: str,
        template: str = None,
        org: str = None,
        platforms: List[str] = None
    ) -> Dict[str, Any]:
        """Create a new Flutter project"""
        args = ["create", project_name]

        if template:
            args.extend(["--template", template])
        if org:
            args.extend(["--org", org])
        if platforms:
            args.extend(["--platforms", ",".join(platforms)])

        return await self.execute(args[0], args[1:])

    async def build(
        self,
        target: str = "apk",
        release: bool = True,
        debug: bool = False
    ) -> Dict[str, Any]:
        """Build Flutter app"""
        args = ["build", target]

        if release:
            args.append("--release")
        elif debug:
            args.append("--debug")

        return await self.execute(args[0], args[1:])

    async def run(
        self,
        device: str = None,
        hot_reload: bool = True
    ) -> Dict[str, Any]:
        """Run Flutter app"""
        args = ["run"]

        if device:
            args.extend(["--device-id", device])
        if not hot_reload:
            args.append("--no-hot")

        return await self.execute(args[0], args[1:])

    async def test(
        self,
        coverage: bool = False,
        test_file: str = None
    ) -> Dict[str, Any]:
        """Run Flutter tests"""
        args = ["test"]

        if coverage:
            args.append("--coverage")
        if test_file:
            args.append(test_file)

        return await self.execute(args[0], args[1:])

    async def pub_get(self) -> Dict[str, Any]:
        """Get Flutter dependencies"""
        return await self.execute("pub", ["get"])

    async def pub_add(self, package: str) -> Dict[str, Any]:
        """Add a Flutter package"""
        return await self.execute("pub", ["add", package])

    async def clean(self) -> Dict[str, Any]:
        """Clean Flutter build artifacts"""
        return await self.execute("clean")

    async def doctor(self) -> Dict[str, Any]:
        """Run Flutter doctor"""
        return await self.execute("doctor")

    async def devices(self) -> Dict[str, Any]:
        """List connected devices"""
        return await self.execute("devices")

    async def analyze(self) -> Dict[str, Any]:
        """Analyze Flutter code"""
        return await self.execute("analyze")

    async def format(self, path: str = ".") -> Dict[str, Any]:
        """Format Flutter code"""
        return await self.execute("format", [path])

    async def gen_l10n(self) -> Dict[str, Any]:
        """Generate localization files"""
        return await self.execute("gen-l10n")

    async def install(self) -> Dict[str, Any]:
        """Install Flutter app on device"""
        return await self.execute("install")

    async def logs(self) -> Dict[str, Any]:
        """Show Flutter app logs"""
        return await self.execute("logs")

    async def screenshot(self, output: str = "flutter_screenshot.png") -> Dict[str, Any]:
        """Take a screenshot"""
        return await self.execute("screenshot", ["-o", output])

    async def symbolize(self, input_file: str, output_file: str) -> Dict[str, Any]:
        """Symbolize stack traces"""
        return await self.execute("symbolize", ["-i", input_file, "-o", output_file])

    async def attach(self, debug_port: int = None) -> Dict[str, Any]:
        """Attach to running Flutter app"""
        args = ["attach"]
        if debug_port:
            args.extend(["--debug-port", str(debug_port)])
        return await self.execute(args[0], args[1:])

    async def drive(self, test_file: str, target: str = None) -> Dict[str, Any]:
        """Run Flutter integration tests"""
        args = ["drive", "--target", test_file]
        if target:
            args.extend(["--target", target])
        return await self.execute(args[0], args[1:])

    async def precache(self) -> Dict[str, Any]:
        """Precache Flutter binaries"""
        return await self.execute("precache")

    async def upgrade(self) -> Dict[str, Any]:
        """Upgrade Flutter"""
        return await self.execute("upgrade")

    async def downgrade(self) -> Dict[str, Any]:
        """Downgrade Flutter"""
        return await self.execute("downgrade")

    async def channel(self, channel: str = None) -> Dict[str, Any]:
        """Switch Flutter channel"""
        args = ["channel"]
        if channel:
            args.append(channel)
        return await self.execute(args[0], args[1:])

    async def config(self, key: str = None, value: str = None) -> Dict[str, Any]:
        """Configure Flutter settings"""
        args = ["config"]
        if key and value:
            args.extend([f"--{key}", value])
        return await self.execute(args[0], args[1:])

    async def custom_command(self, command: str, args: List[str] = None) -> Dict[str, Any]:
        """Execute custom Flutter command"""
        return await self.execute(command, args or [])


# Create MAS Tool wrapper if available
if MAS_AVAILABLE:
    def FlutterCLITool_MAS(working_directory: str = "."):
        """Create Flutter CLI tool as MAS Tool"""
        return create_flutter_cli_tool(working_directory)
