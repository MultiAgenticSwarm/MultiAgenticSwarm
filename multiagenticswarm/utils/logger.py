"""
Comprehensive logging utilities for the multiagenticswarm package.
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging with JSON output."""

    def format(self, record):
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": getattr(record, "module", None),
            "function": getattr(record, "funcName", None),
            "line": getattr(record, "lineno", None),
        }

        # Add custom fields if they exist
        for key, value in record.__dict__.items():
            if key.startswith("mas_"):  # MultiAgenticSwarm custom fields
                log_entry[key] = value

        return json.dumps(log_entry, default=str)


class MultiAgenticSwarmLogger:
    """Enhanced logger for the multiagenticswarm with comprehensive tracking."""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    @property
    def name(self) -> str:
        """Get the logger name."""
        return self.logger.name

    # Standard logging methods for compatibility
    def info(self, message: str, extra: dict = None):
        """Log an info message."""
        if extra is None:
            extra = {}
        extra.update({"mas_event_type": "info", "mas_session_id": self.session_id})
        self.logger.info(message, extra=extra)

    def debug(self, message: str, extra: dict = None):
        """Log a debug message."""
        if extra is None:
            extra = {}
        extra.update({"mas_event_type": "debug", "mas_session_id": self.session_id})
        self.logger.debug(message, extra=extra)

    def warning(self, message: str, extra: dict = None):
        """Log a warning message."""
        if extra is None:
            extra = {}
        extra.update({"mas_event_type": "warning", "mas_session_id": self.session_id})
        self.logger.warning(message, extra=extra)

    def error(self, message: str, extra: dict = None):
        """Log an error message."""
        if extra is None:
            extra = {}
        extra.update({"mas_event_type": "error", "mas_session_id": self.session_id})
        self.logger.error(message, extra=extra)

    def log_function_call(
        self,
        func_name: str,
        args: tuple = None,
        kwargs: dict = None,
        context: dict = None,
        level: str = "INFO",
    ):
        """Log function calls with parameters."""
        extra = {
            "mas_event_type": "function_call",
            "mas_function": func_name,
            "mas_args": str(args) if args else None,
            "mas_kwargs": kwargs if kwargs else None,
            "mas_context": context if context else None,
            "mas_session_id": self.session_id,
        }
        getattr(self.logger, level.lower())(f"Function call: {func_name}", extra=extra)

    def log_function_result(
        self,
        func_name: str,
        result: Any,
        execution_time: float = None,
        level: str = "INFO",
    ):
        """Log function results."""
        extra = {
            "mas_event_type": "function_result",
            "mas_function": func_name,
            "mas_result": str(result)[:1000],  # Truncate long results
            "mas_execution_time": execution_time,
            "mas_session_id": self.session_id,
        }
        getattr(self.logger, level.lower())(
            f"Function result: {func_name}", extra=extra
        )

    def log_llm_request(
        self, provider: str, model: str, messages: List[Dict], context: dict = None
    ):
        """Log LLM requests."""
        extra = {
            "mas_event_type": "llm_request",
            "mas_provider": provider,
            "mas_model": model,
            "mas_messages": messages,
            "mas_context": context,
            "mas_session_id": self.session_id,
        }
        self.logger.info(f"LLM Request to {provider}/{model}", extra=extra)

    def log_llm_response(
        self,
        provider: str,
        model: str,
        response: str,
        metadata: dict = None,
        usage: dict = None,
    ):
        """Log LLM responses."""
        extra = {
            "mas_event_type": "llm_response",
            "mas_provider": provider,
            "mas_model": model,
            "mas_response": response[:2000],  # Truncate long responses
            "mas_metadata": metadata,
            "mas_usage": usage,
            "mas_session_id": self.session_id,
        }
        self.logger.info(f"LLM Response from {provider}/{model}", extra=extra)

    def log_tool_execution(
        self,
        tool_name: str,
        agent_name: str,
        parameters: dict = None,
        result: Any = None,
        execution_time: float = None,
    ):
        """Log tool executions."""
        extra = {
            "mas_event_type": "tool_execution",
            "mas_tool": tool_name,
            "mas_agent": agent_name,
            "mas_parameters": parameters,
            "mas_result": str(result)[:1000] if result is not None else None,
            "mas_execution_time": execution_time,
            "mas_session_id": self.session_id,
        }
        self.logger.info(f"Tool execution: {tool_name} by {agent_name}", extra=extra)

    def log_agent_action(
        self,
        agent_name: str,
        action: str,
        input_data: Any = None,
        output_data: Any = None,
        context: dict = None,
    ):
        """Log agent actions."""
        extra = {
            "mas_event_type": "agent_action",
            "mas_agent": agent_name,
            "mas_action": action,
            "mas_input": str(input_data)[:1000] if input_data is not None else None,
            "mas_output": str(output_data)[:1000] if output_data is not None else None,
            "mas_context": context,
            "mas_session_id": self.session_id,
        }
        self.logger.info(f"Agent action: {agent_name} - {action}", extra=extra)

    def log_task_execution(
        self,
        task_name: str,
        step: int = None,
        status: str = None,
        agent: str = None,
        tool: str = None,
        context: dict = None,
    ):
        """Log task execution steps."""
        extra = {
            "mas_event_type": "task_execution",
            "mas_task": task_name,
            "mas_step": step,
            "mas_status": status,
            "mas_agent": agent,
            "mas_tool": tool,
            "mas_context": context,
            "mas_session_id": self.session_id,
        }
        self.logger.info(f"Task execution: {task_name} step {step}", extra=extra)

    def log_system_event(self, event_type: str, data: dict = None, level: str = "INFO"):
        """Log general system events."""
        extra = {
            "mas_event_type": "system_event",
            "mas_system_event_type": event_type,
            "mas_data": data,
            "mas_session_id": self.session_id,
        }
        getattr(self.logger, level.lower())(f"System event: {event_type}", extra=extra)


def setup_comprehensive_logging(
    verbose: bool = False,
    log_to_file: bool = True,
    log_directory: Optional[str] = None,
    max_log_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    enable_json_logs: bool = True,
    enable_real_time_view: bool = False,
) -> Dict[str, str]:
    """
    Setup comprehensive logging for the package.

    Args:
        verbose: Enable debug level logging to console
        log_to_file: Enable file logging
        log_directory: Custom log directory path
        max_log_size: Maximum size per log file in bytes
        backup_count: Number of backup files to keep
        enable_json_logs: Enable structured JSON logging
        enable_real_time_view: Enable real-time log viewing capability

    Returns:
        Dictionary with paths to log files and configuration info
    """
    level = logging.DEBUG if verbose else logging.INFO
    log_info = {}

    # Create log directory if needed
    if log_to_file:
        if log_directory is None:
            log_directory = os.path.join(os.getcwd(), "logs", "MultiAgenticSwarm")

        log_path = Path(log_directory)
        log_path.mkdir(parents=True, exist_ok=True)
        log_info["log_directory"] = str(log_path)

        # Setup file handler with rotation
        from logging.handlers import RotatingFileHandler

        log_file = (
            log_path / f"MultiAgenticSwarm_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_log_size, backupCount=backup_count
        )
        file_handler.setFormatter(StructuredFormatter())
        file_handler.setLevel(logging.DEBUG)  # Always log everything to file
        log_info["text_log_file"] = str(log_file)

        # Setup JSON log file for structured logs
        if enable_json_logs:
            json_log_file = (
                log_path / f"MultiAgenticSwarm_{datetime.now().strftime('%Y%m%d')}.json"
            )
            json_handler = RotatingFileHandler(
                json_log_file, maxBytes=max_log_size, backupCount=backup_count
            )
            json_handler.setFormatter(StructuredFormatter())
            json_handler.setLevel(logging.DEBUG)
            log_info["json_log_file"] = str(json_log_file)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    console_handler.setFormatter(logging.Formatter(console_format))
    console_handler.setLevel(level)

    # Configure root logger for MultiAgenticSwarm
    mas_logger = logging.getLogger("MultiAgenticSwarm")
    mas_logger.setLevel(logging.DEBUG)

    # Clear existing handlers
    mas_logger.handlers.clear()

    # Add handlers
    mas_logger.addHandler(console_handler)
    if log_to_file:
        mas_logger.addHandler(file_handler)
        if enable_json_logs:
            mas_logger.addHandler(json_handler)

    # Prevent propagation to root logger
    mas_logger.propagate = False

    # Store configuration for runtime access
    log_info.update(
        {
            "verbose": verbose,
            "log_to_file": log_to_file,
            "max_log_size": max_log_size,
            "backup_count": backup_count,
            "enable_json_logs": enable_json_logs,
            "enable_real_time_view": enable_real_time_view,
            "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        }
    )

    # Store globally for easy access
    set_logging_config(log_info)

    print(f"✅ MultiAgenticSwarm logging initialized")
    print(f"📁 Log directory: {log_info.get('log_directory', 'None')}")
    if log_to_file:
        print(f"📄 Text logs: {log_info.get('text_log_file', 'None')}")
        if enable_json_logs:
            print(f"📊 JSON logs: {log_info.get('json_log_file', 'None')}")
    print(f"🆔 Session ID: {log_info['session_id']}")

    return log_info


def setup_logging(
    level: str = "INFO",
    log_dir: str = "./logs",
    session_id: Optional[str] = None,
    format_type: str = "detailed",
    console_output: bool = True,
    max_file_size: str = "10MB",
    backup_count: int = 5,
    include_metadata: bool = True,
) -> Dict[str, str]:
    """
    Set up comprehensive logging for MultiAgenticSwarm.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_dir: Directory to store log files
        session_id: Unique session identifier
        format_type: Format type ("simple", "detailed", "json")
        console_output: Whether to also output to console
        max_file_size: Maximum size before rotating log files
        backup_count: Number of backup files to keep
        include_metadata: Whether to include structured metadata

    Returns:
        Dictionary with paths to log files and configuration info
    """
    # Map the parameters to what setup_comprehensive_logging expects
    verbose = level.upper() == "DEBUG"

    # Convert max_file_size string to bytes
    max_log_size = 10 * 1024 * 1024  # Default 10MB
    if max_file_size.upper().endswith("MB"):
        max_log_size = int(max_file_size[:-2]) * 1024 * 1024
    elif max_file_size.upper().endswith("KB"):
        max_log_size = int(max_file_size[:-2]) * 1024
    elif max_file_size.isdigit():
        max_log_size = int(max_file_size)

    return setup_comprehensive_logging(
        verbose=verbose,
        log_to_file=True,
        log_directory=log_dir,
        max_log_size=max_log_size,
        backup_count=backup_count,
        enable_json_logs=True,
        enable_real_time_view=False,
    )


def setup_logger(verbose: bool = False) -> None:
    """Setup the main logger for the package (legacy function)."""
    setup_comprehensive_logging(verbose=verbose)


def get_logger(name: str) -> MultiAgenticSwarmLogger:
    """Get an enhanced logger instance for the given name."""
    return MultiAgenticSwarmLogger(name)


def get_simple_logger(name: str) -> logging.Logger:
    """Get a simple logger instance (for backward compatibility)."""
    return logging.getLogger(name)


def log_decorator(logger: MultiAgenticSwarmLogger):
    """Decorator to automatically log function calls and results."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            # Log function call
            logger.log_function_call(
                func.__name__,
                args=args,
                kwargs=kwargs,
                context={"module": func.__module__},
            )

            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time

                # Log successful result
                logger.log_function_result(
                    func.__name__, result=result, execution_time=execution_time
                )

                return result

            except Exception as e:
                execution_time = time.time() - start_time

                # Log error
                logger.log_function_result(
                    func.__name__,
                    result=f"ERROR: {str(e)}",
                    execution_time=execution_time,
                    level="ERROR",
                )
                raise

        return wrapper

    return decorator


def async_log_decorator(logger: MultiAgenticSwarmLogger):
    """Decorator to automatically log async function calls and results."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()

            # Log function call
            logger.log_function_call(
                func.__name__,
                args=args,
                kwargs=kwargs,
                context={"module": func.__module__},
            )

            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time

                # Log successful result
                logger.log_function_result(
                    func.__name__, result=result, execution_time=execution_time
                )

                return result

            except Exception as e:
                execution_time = time.time() - start_time

                # Log error
                logger.log_function_result(
                    func.__name__,
                    result=f"ERROR: {str(e)}",
                    execution_time=execution_time,
                    level="ERROR",
                )
                raise

        return wrapper

    return decorator


class LogViewer:
    """Utility class for viewing and managing logs."""

    def __init__(self, log_directory: Optional[str] = None):
        """Initialize log viewer with specified directory."""
        self.log_directory = log_directory or os.path.join(
            os.getcwd(), "logs", "MultiAgenticSwarm"
        )
        self.log_path = Path(self.log_directory)

    def get_log_files(self) -> Dict[str, List[str]]:
        """Get all available log files."""
        log_files = {"text_logs": [], "json_logs": []}

        if self.log_path.exists():
            for file in self.log_path.glob("*.log"):
                log_files["text_logs"].append(str(file))
            for file in self.log_path.glob("*.json"):
                log_files["json_logs"].append(str(file))

        return log_files

    def get_latest_logs(self, lines: int = 100, log_type: str = "text") -> List[str]:
        """Get the latest log entries."""
        log_files = self.get_log_files()
        file_list = log_files.get(f"{log_type}_logs", [])

        if not file_list:
            return []

        # Get the most recent log file
        latest_file = max(file_list, key=lambda x: os.path.getmtime(x))

        try:
            with open(latest_file, "r") as f:
                all_lines = f.readlines()
                return all_lines[-lines:] if len(all_lines) > lines else all_lines
        except Exception as e:
            return [f"Error reading log file: {e}"]

    def search_logs(
        self, query: str, log_type: str = "text", case_sensitive: bool = False
    ) -> List[str]:
        """Search for specific patterns in logs."""
        log_files = self.get_log_files()
        file_list = log_files.get(f"{log_type}_logs", [])

        results = []
        for log_file in file_list:
            try:
                with open(log_file, "r") as f:
                    for line_num, line in enumerate(f, 1):
                        if case_sensitive:
                            if query in line:
                                results.append(f"{log_file}:{line_num}: {line.strip()}")
                        else:
                            if query.lower() in line.lower():
                                results.append(f"{log_file}:{line_num}: {line.strip()}")
            except Exception as e:
                results.append(f"Error reading {log_file}: {e}")

        return results

    def get_session_logs(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all logs for a specific session."""
        log_files = self.get_log_files()
        json_files = log_files.get("json_logs", [])

        session_logs = []
        for log_file in json_files:
            try:
                with open(log_file, "r") as f:
                    for line in f:
                        try:
                            log_entry = json.loads(line.strip())
                            if log_entry.get("mas_session_id") == session_id:
                                session_logs.append(log_entry)
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                print(f"Error reading {log_file}: {e}")

        return sorted(session_logs, key=lambda x: x.get("timestamp", ""))

    def get_agent_logs(self, agent_name: str) -> List[Dict[str, Any]]:
        """Get all logs for a specific agent."""
        log_files = self.get_log_files()
        json_files = log_files.get("json_logs", [])

        agent_logs = []
        for log_file in json_files:
            try:
                with open(log_file, "r") as f:
                    for line in f:
                        try:
                            log_entry = json.loads(line.strip())
                            if log_entry.get("mas_agent") == agent_name:
                                agent_logs.append(log_entry)
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                print(f"Error reading {log_file}: {e}")

        return sorted(agent_logs, key=lambda x: x.get("timestamp", ""))

    def get_llm_logs(self, provider: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all LLM-related logs, optionally filtered by provider."""
        log_files = self.get_log_files()
        json_files = log_files.get("json_logs", [])

        llm_logs = []
        for log_file in json_files:
            try:
                with open(log_file, "r") as f:
                    for line in f:
                        try:
                            log_entry = json.loads(line.strip())
                            event_type = log_entry.get("mas_event_type", "")

                            if event_type in ["llm_request", "llm_response"]:
                                if (
                                    provider is None
                                    or log_entry.get("mas_provider") == provider
                                ):
                                    llm_logs.append(log_entry)
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                print(f"Error reading {log_file}: {e}")

        return sorted(llm_logs, key=lambda x: x.get("timestamp", ""))

    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate a summary report of system activity."""
        log_files = self.get_log_files()
        json_files = log_files.get("json_logs", [])

        summary = {
            "total_log_files": len(log_files["text_logs"])
            + len(log_files["json_logs"]),
            "agents": set(),
            "llm_providers": set(),
            "tools_used": set(),
            "event_counts": {},
            "sessions": set(),
            "errors": 0,
            "warnings": 0,
        }

        for log_file in json_files:
            try:
                with open(log_file, "r") as f:
                    for line in f:
                        try:
                            log_entry = json.loads(line.strip())

                            # Count events
                            event_type = log_entry.get("mas_event_type", "unknown")
                            summary["event_counts"][event_type] = (
                                summary["event_counts"].get(event_type, 0) + 1
                            )

                            # Track agents
                            if "mas_agent" in log_entry:
                                summary["agents"].add(log_entry["mas_agent"])

                            # Track LLM providers
                            if "mas_provider" in log_entry:
                                summary["llm_providers"].add(log_entry["mas_provider"])

                            # Track tools
                            if "mas_tool" in log_entry:
                                summary["tools_used"].add(log_entry["mas_tool"])

                            # Track sessions
                            if "mas_session_id" in log_entry:
                                summary["sessions"].add(log_entry["mas_session_id"])

                            # Count errors and warnings
                            level = log_entry.get("level", "").upper()
                            if level == "ERROR":
                                summary["errors"] += 1
                            elif level == "WARNING":
                                summary["warnings"] += 1

                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                print(f"Error reading {log_file}: {e}")

        # Convert sets to lists for JSON serialization
        summary["agents"] = list(summary["agents"])
        summary["llm_providers"] = list(summary["llm_providers"])
        summary["tools_used"] = list(summary["tools_used"])
        summary["sessions"] = list(summary["sessions"])

        return summary


def get_log_viewer(log_directory: Optional[str] = None) -> LogViewer:
    """Get a LogViewer instance."""
    return LogViewer(log_directory)


def view_latest_logs(lines: int = 50, log_type: str = "text") -> None:
    """Quick utility to view latest logs."""
    viewer = get_log_viewer()
    logs = viewer.get_latest_logs(lines, log_type)

    print(f"\n=== Latest {lines} lines from {log_type} logs ===")
    for log_line in logs:
        print(log_line.rstrip())
    print("=" * 50)


def search_logs(
    query: str, log_type: str = "text", case_sensitive: bool = False
) -> None:
    """Quick utility to search logs."""
    viewer = get_log_viewer()
    results = viewer.search_logs(query, log_type, case_sensitive)

    print(f"\n=== Search results for '{query}' in {log_type} logs ===")
    for result in results:
        print(result)
    print(f"Found {len(results)} matches")
    print("=" * 50)


def get_system_summary() -> None:
    """Quick utility to get system activity summary."""
    viewer = get_log_viewer()
    summary = viewer.generate_summary_report()

    print("\n=== MultiAgenticSwarm Activity Summary ===")
    print(f"Total log files: {summary['total_log_files']}")
    print(f"Active sessions: {len(summary['sessions'])}")
    print(f"Agents used: {len(summary['agents'])}")
    print(f"LLM providers: {len(summary['llm_providers'])}")
    print(f"Tools used: {len(summary['tools_used'])}")
    print(f"Errors: {summary['errors']}")
    print(f"Warnings: {summary['warnings']}")

    print("\nEvent breakdown:")
    for event_type, count in summary["event_counts"].items():
        print(f"  {event_type}: {count}")

    if summary["agents"]:
        print(f"\nAgents: {', '.join(summary['agents'])}")
    if summary["llm_providers"]:
        print(f"LLM Providers: {', '.join(summary['llm_providers'])}")
    if summary["tools_used"]:
        print(f"Tools: {', '.join(summary['tools_used'])}")

    print("=" * 50)


# Global logging configuration storage
_log_config: Dict[str, Any] = {}


def get_logging_config() -> Dict[str, Any]:
    """Get current logging configuration."""
    return _log_config.copy()


def set_logging_config(config: Dict[str, Any]) -> None:
    """Set logging configuration."""
    global _log_config
    _log_config = config


def get_logs(
    lines: Optional[int] = None, format: str = "text", log_file: Optional[str] = None
) -> Union[List[str], List[Dict]]:
    """
    Get log entries from the most recent log file.

    Args:
        lines: Number of lines to retrieve. If None, get all.
        format: Return format - "text" or "json"
        log_file: Specific log file to read. If None, uses most recent.

    Returns:
        List of log entries (strings or dicts depending on format)
    """
    from .log_viewer import LogViewer

    viewer = LogViewer()
    log_lines = viewer.read_logs(log_file, lines)

    if format == "json":
        # Try to parse each line as JSON
        json_logs = []
        for line in log_lines:
            try:
                json_logs.append(json.loads(line))
            except json.JSONDecodeError:
                # If not JSON, create a simple structure
                json_logs.append(
                    {"message": line.strip(), "level": "UNKNOWN", "timestamp": None}
                )
        return json_logs
    else:
        return log_lines


def view_logs(
    lines: int = 20, level: Optional[str] = None, component: Optional[str] = None
):
    """
    Display recent logs in a formatted way.

    Args:
        lines: Number of lines to show
        level: Filter by log level
        component: Filter by component name
    """
    from .log_viewer import LogViewer

    viewer = LogViewer()

    if level or component:
        filtered_logs = viewer.filter_logs(level=level, component=component)
        logs_to_show = filtered_logs[-lines:] if filtered_logs else []
    else:
        logs_to_show = viewer.read_logs(lines=lines)

    print(f"=== Last {len(logs_to_show)} log entries ===")
    for log in logs_to_show:
        print(log.rstrip())


def clear_logs(log_dir: Optional[str] = None, confirm: bool = True):
    """
    Clear log files from the specified directory.

    Args:
        log_dir: Directory containing logs. If None, uses default.
        confirm: Whether to ask for confirmation before deleting.
    """
    import os

    from .log_viewer import LogViewer

    viewer = LogViewer(log_dir)
    log_files = viewer.get_log_files()

    if not log_files:
        print("No log files found to clear.")
        return

    if confirm:
        response = input(f"Delete {len(log_files)} log files? (y/N): ")
        if response.lower() != "y":
            print("Cancelled.")
            return

    for log_file in log_files:
        try:
            os.remove(log_file)
            print(f"Deleted: {log_file}")
        except Exception as e:
            print(f"Error deleting {log_file}: {e}")
