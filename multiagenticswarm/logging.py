"""
Logging utilities and convenience functions for MultiAgenticSwarm.

This module provides easy access to logging functionality when using the package.
"""

from typing import Any, Dict, List, Optional
from .utils.logger import (
    setup_comprehensive_logging,
    get_logger,
    get_log_viewer,
    view_latest_logs,
    search_logs,
    get_system_summary,
    get_logging_config,
    LogViewer
)

__all__ = [
    'setup_logging',
    'get_log_viewer',
    'view_logs', 
    'search_logs_func',
    'get_summary',
    'get_config',
    'LogViewer',
    'get_logs_for_agent',
    'get_logs_for_session',
    'get_llm_logs',
    'export_logs',
    'log_info',
    'log_debug', 
    'log_warning',
    'log_error'
]


def setup_logging(
    verbose: bool = False,
    log_directory: Optional[str] = None,
    enable_json_logs: bool = True
) -> Dict[str, str]:
    """
    Setup comprehensive logging for MultiAgenticSwarm.
    
    Args:
        verbose: Enable debug level logging
        log_directory: Custom directory for log files
        enable_json_logs: Enable structured JSON logging
        
    Returns:
        Dictionary with log file paths and configuration
        
    Example:
        >>> from multiagenticswarm.logging import setup_logging
        >>> log_info = setup_logging(verbose=True)
        >>> print(f"Logs are stored in: {log_info['log_directory']}")
    """
    return setup_comprehensive_logging(
        verbose=verbose,
        log_directory=log_directory,
        enable_json_logs=enable_json_logs
    )


def view_logs(lines: int = 50, log_type: str = "text") -> None:
    """
    View the latest log entries.
    
    Args:
        lines: Number of lines to display
        log_type: Type of logs to view ("text" or "json")
        
    Example:
        >>> from multiagenticswarm.logging import view_logs
        >>> view_logs(100)  # View last 100 lines
    """
    view_latest_logs(lines, log_type)


def search_logs_func(query: str, log_type: str = "text", case_sensitive: bool = False) -> None:
    """
    Search for specific patterns in logs.
    
    Args:
        query: Text to search for
        log_type: Type of logs to search ("text" or "json")
        case_sensitive: Whether search should be case sensitive
        
    Example:
        >>> from multiagenticswarm.logging import search_logs
        >>> search_logs("error")  # Find all error entries
        >>> search_logs("agent_action")  # Find all agent actions
    """
    search_logs(query, log_type, case_sensitive)


def get_summary() -> None:
    """
    Display a summary of system activity.
    
    Example:
        >>> from multiagenticswarm.logging import get_summary
        >>> get_summary()
    """
    get_system_summary()


def get_config() -> Dict[str, Any]:
    """
    Get current logging configuration.
    
    Returns:
        Dictionary with current logging settings
        
    Example:
        >>> from multiagenticswarm.logging import get_config
        >>> config = get_config()
        >>> print(f"Session ID: {config.get('session_id')}")
    """
    return get_logging_config()


def get_logs_for_agent(agent_name: str) -> List[Dict[str, Any]]:
    """
    Get all logs for a specific agent.
    
    Args:
        agent_name: Name of the agent
        
    Returns:
        List of log entries for the agent
        
    Example:
        >>> from multiagenticswarm.logging import get_logs_for_agent
        >>> logs = get_logs_for_agent("DataAnalyst")
        >>> print(f"Found {len(logs)} log entries for DataAnalyst")
    """
    viewer = get_log_viewer()
    return viewer.get_agent_logs(agent_name)


def get_logs_for_session(session_id: str) -> List[Dict[str, Any]]:
    """
    Get all logs for a specific session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        List of log entries for the session
        
    Example:
        >>> from multiagenticswarm.logging import get_logs_for_session
        >>> logs = get_logs_for_session("20250623_141500")
        >>> print(f"Found {len(logs)} log entries for session")
    """
    viewer = get_log_viewer()
    return viewer.get_session_logs(session_id)


def get_llm_logs(provider: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get all LLM-related logs.
    
    Args:
        provider: Optional provider filter ("openai", "anthropic", etc.)
        
    Returns:
        List of LLM log entries
        
    Example:
        >>> from multiagenticswarm.logging import get_llm_logs
        >>> logs = get_llm_logs("openai")  # Only OpenAI logs
        >>> all_llm_logs = get_llm_logs()  # All LLM logs
    """
    viewer = get_log_viewer()
    return viewer.get_llm_logs(provider)


def export_logs(
    output_file: str,
    session_id: Optional[str] = None,
    agent_name: Optional[str] = None,
    log_type: str = "json"
) -> bool:
    """
    Export logs to a file.
    
    Args:
        output_file: Path to output file
        session_id: Optional session filter
        agent_name: Optional agent filter
        log_type: Type of logs to export
        
    Returns:
        True if export successful
        
    Example:
        >>> from multiagenticswarm.logging import export_logs
        >>> export_logs("my_session_logs.json", session_id="20250623_141500")
    """
    import json
    from pathlib import Path
    
    viewer = get_log_viewer()
    
    try:
        if session_id:
            logs = viewer.get_session_logs(session_id)
        elif agent_name:
            logs = viewer.get_agent_logs(agent_name)
        else:
            # Get all logs from JSON files
            logs = []
            log_files = viewer.get_log_files()
            for log_file in log_files.get("json_logs", []):
                with open(log_file, 'r') as f:
                    for line in f:
                        try:
                            logs.append(json.loads(line.strip()))
                        except json.JSONDecodeError:
                            continue
        
        # Write to output file
        output_path = Path(output_file)
        with open(output_path, 'w') as f:
            json.dump(logs, f, indent=2, default=str)
        
        print(f"✅ Exported {len(logs)} log entries to {output_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error exporting logs: {e}")
        return False


# Convenience functions for common logging patterns
def log_info(message: str, **kwargs) -> None:
    """Log an info message."""
    logger = get_logger("user")
    logger.log_system_event("user_info", {"message": message, **kwargs})


def log_debug(message: str, **kwargs) -> None:
    """Log a debug message."""
    logger = get_logger("user")
    logger.log_system_event("user_debug", {"message": message, **kwargs}, level="DEBUG")


def log_warning(message: str, **kwargs) -> None:
    """Log a warning message."""
    logger = get_logger("user")
    logger.log_system_event("user_warning", {"message": message, **kwargs}, level="WARNING")


def log_error(message: str, **kwargs) -> None:
    """Log an error message."""
    logger = get_logger("user")
    logger.log_system_event("user_error", {"message": message, **kwargs}, level="ERROR")
