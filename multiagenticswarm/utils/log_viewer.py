"""
Log viewer utility for the multiagenticswarm package.
Provides easy access to view and filter logs.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class LogViewer:
    """Utility class for viewing and analyzing multiagenticswarm logs."""

    def __init__(self, log_dir: Optional[str] = None):
        """Initialize the LogViewer.

        Args:
            log_dir: Directory containing log files. If None, uses default.
        """
        if log_dir is None:
            # Default to logs directory in current working directory
            log_dir = os.path.join(os.getcwd(), "logs")

        self.log_dir = Path(log_dir)

    def get_log_files(self) -> List[Path]:
        """Get all log files in the log directory."""
        if not self.log_dir.exists():
            return []

        log_files = []
        for file in self.log_dir.rglob("*.log"):
            log_files.append(file)

        return sorted(log_files, key=lambda x: x.stat().st_mtime, reverse=True)

    def get_latest_log_file(self) -> Optional[Path]:
        """Get the most recently modified log file."""
        log_files = self.get_log_files()
        return log_files[0] if log_files else None

    def read_logs(
        self, log_file: Optional[str] = None, lines: Optional[int] = None
    ) -> List[str]:
        """Read logs from a file.

        Args:
            log_file: Path to log file. If None, uses latest log file.
            lines: Number of lines to read from end. If None, reads all.

        Returns:
            List of log lines.
        """
        if log_file is None:
            log_path = self.get_latest_log_file()
            if log_path is None:
                return []
        else:
            log_path = Path(log_file)

        try:
            with open(log_path, "r", encoding="utf-8") as f:
                if lines is None:
                    return f.readlines()
                else:
                    # Read last N lines
                    return f.readlines()[-lines:]
        except Exception as e:
            print(f"Error reading log file {log_path}: {e}")
            return []

    def filter_logs(
        self,
        log_file: Optional[str] = None,
        level: Optional[str] = None,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        component: Optional[str] = None,
        search_text: Optional[str] = None,
    ) -> List[str]:
        """Filter logs based on criteria.

        Args:
            log_file: Path to log file. If None, uses latest log file.
            level: Log level to filter by (DEBUG, INFO, WARNING, ERROR).
            agent_id: Agent ID to filter by.
            session_id: Session ID to filter by.
            component: Component name to filter by.
            search_text: Text to search for in log messages.

        Returns:
            List of filtered log lines.
        """
        lines = self.read_logs(log_file)
        filtered_lines = []

        for line in lines:
            # Apply filters
            if level and f"[{level}]" not in line:
                continue
            if agent_id and f"agent_id:{agent_id}" not in line:
                continue
            if session_id and f"session_id:{session_id}" not in line:
                continue
            if component and f"component:{component}" not in line:
                continue
            if search_text and search_text.lower() not in line.lower():
                continue

            filtered_lines.append(line)

        return filtered_lines

    def get_sessions(self, log_file: Optional[str] = None) -> List[str]:
        """Get all unique session IDs from logs.

        Args:
            log_file: Path to log file. If None, uses latest log file.

        Returns:
            List of unique session IDs.
        """
        lines = self.read_logs(log_file)
        sessions = set()

        for line in lines:
            # Extract session_id from log line
            if "session_id:" in line:
                try:
                    start = line.index("session_id:") + len("session_id:")
                    end = line.index(",", start) if "," in line[start:] else len(line)
                    session_id = line[start:end].strip()
                    sessions.add(session_id)
                except (ValueError, IndexError):
                    continue

        return sorted(list(sessions))

    def get_agents(self, log_file: Optional[str] = None) -> List[str]:
        """Get all unique agent IDs from logs.

        Args:
            log_file: Path to log file. If None, uses latest log file.

        Returns:
            List of unique agent IDs.
        """
        lines = self.read_logs(log_file)
        agents = set()

        for line in lines:
            # Extract agent_id from log line
            if "agent_id:" in line:
                try:
                    start = line.index("agent_id:") + len("agent_id:")
                    end = line.index(",", start) if "," in line[start:] else len(line)
                    agent_id = line[start:end].strip()
                    agents.add(agent_id)
                except (ValueError, IndexError):
                    continue

        return sorted(list(agents))

    def get_log_summary(self, log_file: Optional[str] = None) -> Dict[str, Any]:
        """Get a summary of log activity.

        Args:
            log_file: Path to log file. If None, uses latest log file.

        Returns:
            Dictionary with log summary statistics.
        """
        lines = self.read_logs(log_file)

        summary = {
            "total_lines": len(lines),
            "levels": {"DEBUG": 0, "INFO": 0, "WARNING": 0, "ERROR": 0},
            "agents": len(self.get_agents(log_file)),
            "sessions": len(self.get_sessions(log_file)),
            "components": set(),
            "first_log": None,
            "last_log": None,
        }

        for line in lines:
            # Count log levels
            for level in summary["levels"]:
                if f"[{level}]" in line:
                    summary["levels"][level] += 1

            # Extract components
            if "component:" in line:
                try:
                    start = line.index("component:") + len("component:")
                    end = line.index(",", start) if "," in line[start:] else len(line)
                    component = line[start:end].strip()
                    summary["components"].add(component)
                except (ValueError, IndexError):
                    continue

            # Extract timestamps for first/last log
            try:
                timestamp_str = line.split(" - ")[0]
                if summary["first_log"] is None:
                    summary["first_log"] = timestamp_str
                summary["last_log"] = timestamp_str
            except IndexError:
                continue

        summary["components"] = sorted(list(summary["components"]))
        return summary

    def print_summary(self, log_file: Optional[str] = None):
        """Print a formatted summary of log activity."""
        summary = self.get_log_summary(log_file)

        print("=== Log Summary ===")
        print(f"Total lines: {summary['total_lines']}")
        print(f"Agents: {summary['agents']}")
        print(f"Sessions: {summary['sessions']}")
        print(f"Components: {len(summary['components'])}")

        print("\nLog levels:")
        for level, count in summary["levels"].items():
            print(f"  {level}: {count}")

        if summary["components"]:
            print(f"\nComponents: {', '.join(summary['components'])}")

        if summary["first_log"] and summary["last_log"]:
            print(f"\nTime range: {summary['first_log']} to {summary['last_log']}")

    def tail_logs(self, log_file: Optional[str] = None, lines: int = 20):
        """Print the last N lines of logs (like tail command).

        Args:
            log_file: Path to log file. If None, uses latest log file.
            lines: Number of lines to show.
        """
        log_lines = self.read_logs(log_file, lines)

        print(f"=== Last {len(log_lines)} log lines ===")
        for line in log_lines:
            print(line.rstrip())

    def search_logs(
        self, search_text: str, log_file: Optional[str] = None, context_lines: int = 0
    ):
        """Search for text in logs and display results with optional context.

        Args:
            search_text: Text to search for.
            log_file: Path to log file. If None, uses latest log file.
            context_lines: Number of lines before/after each match to include.
        """
        lines = self.read_logs(log_file)
        matches = []

        for i, line in enumerate(lines):
            if search_text.lower() in line.lower():
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)
                matches.append((i, start, end))

        if not matches:
            print(f"No matches found for '{search_text}'")
            return

        print(f"=== Found {len(matches)} matches for '{search_text}' ===")

        for match_idx, (line_num, start, end) in enumerate(matches):
            print(f"\n--- Match {match_idx + 1} (line {line_num + 1}) ---")
            for i in range(start, end):
                prefix = ">>> " if i == line_num else "    "
                print(f"{prefix}{i + 1:4}: {lines[i].rstrip()}")


def quick_view_logs(lines: int = 20, level: Optional[str] = None):
    """Quick function to view recent logs.

    Args:
        lines: Number of lines to show.
        level: Log level to filter by.
    """
    viewer = LogViewer()

    if level:
        log_lines = viewer.filter_logs(level=level)[-lines:]
    else:
        log_lines = viewer.read_logs(lines=lines)

    print(
        f"=== Last {len(log_lines)} log lines"
        + (f" ({level})" if level else "")
        + " ==="
    )
    for line in log_lines:
        print(line.rstrip())


def search_logs(search_text: str, context_lines: int = 2):
    """Quick function to search logs.

    Args:
        search_text: Text to search for.
        context_lines: Number of context lines around matches.
    """
    viewer = LogViewer()
    viewer.search_logs(search_text, context_lines=context_lines)
