"""
File system operations tool - ONLY executes file operations, contains ZERO domain logic.
All decisions about WHAT files to create/modify come from LLMs.
"""
import json
import logging
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import multiagenticswarm as mas
    from multiagenticswarm.core.base_tool import FunctionTool

    MAS_AVAILABLE = True
except ImportError:
    MAS_AVAILABLE = False
    FunctionTool = None
    mas = None


def create_file_system_tool(working_directory: str = ".") -> Any:
    """Create a file system tool using MAS Tool interface"""

    def file_system_func(operation: str, path: str, **kwargs) -> Dict[str, Any]:
        """Execute file system operation - pure interface, no logic"""

        full_path = (
            os.path.join(working_directory, path) if not os.path.isabs(path) else path
        )

        try:
            if operation == "read":
                encoding = kwargs.get("encoding", "utf-8")
                with open(full_path, "r", encoding=encoding) as f:
                    content = f.read()
                return {
                    "success": True,
                    "content": content,
                    "path": full_path,
                    "operation": operation,
                }

            elif operation == "write":
                content = kwargs.get("content", "")
                encoding = kwargs.get("encoding", "utf-8")
                create_dirs = kwargs.get("create_dirs", True)

                if create_dirs:
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)

                with open(full_path, "w", encoding=encoding) as f:
                    f.write(content)

                return {
                    "success": True,
                    "path": full_path,
                    "operation": operation,
                    "bytes_written": len(content.encode(encoding)),
                }

            elif operation == "mkdir":
                os.makedirs(full_path, exist_ok=True)
                return {"success": True, "path": full_path, "operation": operation}

            elif operation == "list":
                recursive = kwargs.get("recursive", False)
                include_hidden = kwargs.get("include_hidden", False)

                if recursive:
                    items = []
                    for root, dirs, files in os.walk(full_path):
                        if not include_hidden:
                            dirs[:] = [d for d in dirs if not d.startswith(".")]
                            files = [f for f in files if not f.startswith(".")]

                        for file in files:
                            items.append(
                                os.path.relpath(os.path.join(root, file), full_path)
                            )
                        for dir in dirs:
                            items.append(
                                os.path.relpath(os.path.join(root, dir), full_path)
                                + "/"
                            )
                else:
                    items = []
                    for item in os.listdir(full_path):
                        if not include_hidden and item.startswith("."):
                            continue
                        item_path = os.path.join(full_path, item)
                        if os.path.isdir(item_path):
                            items.append(item + "/")
                        else:
                            items.append(item)

                return {
                    "success": True,
                    "items": items,
                    "path": full_path,
                    "operation": operation,
                }

            elif operation == "exists":
                return {
                    "success": True,
                    "exists": os.path.exists(full_path),
                    "path": full_path,
                    "operation": operation,
                }

            elif operation == "delete":
                if os.path.isfile(full_path):
                    os.remove(full_path)
                elif os.path.isdir(full_path):
                    shutil.rmtree(full_path)

                return {"success": True, "path": full_path, "operation": operation}

            elif operation == "copy":
                dest = kwargs.get("dest")
                if not dest:
                    raise ValueError("dest parameter required for copy operation")

                dest_path = (
                    os.path.join(working_directory, dest)
                    if not os.path.isabs(dest)
                    else dest
                )

                if os.path.isfile(full_path):
                    shutil.copy2(full_path, dest_path)
                elif os.path.isdir(full_path):
                    shutil.copytree(full_path, dest_path)

                return {
                    "success": True,
                    "source": full_path,
                    "dest": dest_path,
                    "operation": operation,
                }

            elif operation == "move":
                dest = kwargs.get("dest")
                if not dest:
                    raise ValueError("dest parameter required for move operation")

                dest_path = (
                    os.path.join(working_directory, dest)
                    if not os.path.isabs(dest)
                    else dest
                )
                shutil.move(full_path, dest_path)

                return {
                    "success": True,
                    "source": full_path,
                    "dest": dest_path,
                    "operation": operation,
                }

            else:
                raise ValueError(f"Unknown operation: {operation}")

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "path": full_path,
                "operation": operation,
            }

    # Create MAS Tool
    if MAS_AVAILABLE:
        return FunctionTool(
            func=file_system_func,
            name="file_system",
            description="Performs file system operations like read, write, list, etc. This tool is a pure interface - it has no logic, it only executes the file operations you provide.",
            parameters={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": "The file system operation to perform (e.g., 'read', 'write', 'list_dir').",
                    },
                    "path": {
                        "type": "string",
                        "description": "The path to the file or directory.",
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write to the file (for 'write' operation).",
                    },
                },
                "required": ["operation", "path"],
            },
        )

    return None


class FileSystemTool:
    """
    Simple wrapper around file system operations - no logic, just execution.
    LLM decides what files to create/modify.
    Comprehensive logging tracks all file operations.
    """

    def __init__(self, working_directory: str = ".", name: str = "file_system"):
        self.working_directory = working_directory
        self.name = name
        self.description = "Execute file system operations with comprehensive logging"

        # Initialize comprehensive logging using direct import
        from multiagenticswarm.utils.logger import get_logger

        self.logger = get_logger(f"flutterswarm.tools.{name}")

        # Ensure working directory exists
        os.makedirs(working_directory, exist_ok=True)

        # Create MAS tool
        if MAS_AVAILABLE:
            self.mas_tool = create_file_system_tool(working_directory)
        else:
            self.mas_tool = None

        self.logger.log_tool_call_detailed(
            tool_name=self.name,
            agent_name="system",
            command="initialize",
            parameters={"working_directory": self.working_directory},
            success=True,
        )

    def get_mas_tool(self):
        """Get the MAS tool instance"""
        return self.mas_tool

    def _get_full_path(self, path: str) -> str:
        """Get the full path for a file/directory"""
        if os.path.isabs(path):
            return path
        return os.path.join(self.working_directory, path)

    async def execute(self, operation: str, path: str, **kwargs) -> Dict[str, Any]:
        """Execute file system operation - dispatcher method"""

        if operation == "read":
            return await self.read_file(path, kwargs.get("encoding", "utf-8"))
        elif operation == "write":
            return await self.write_file(
                path,
                kwargs.get("content", ""),
                kwargs.get("encoding", "utf-8"),
                kwargs.get("create_dirs", True),
            )
        elif operation == "mkdir":
            return await self.create_directory(path)
        elif operation == "list":
            return await self.list_directory(
                path,
                kwargs.get("recursive", False),
                kwargs.get("include_hidden", False),
            )
        elif operation == "exists":
            return await self.exists(path)
        elif operation == "delete":
            return await self.delete(path)
        elif operation == "copy":
            return await self.copy(path, kwargs.get("dest", ""))
        elif operation == "move":
            return await self.move(path, kwargs.get("dest", ""))
        elif operation == "info":
            return await self.get_file_info(path)
        elif operation == "read_json":
            return await self.read_json(path)
        elif operation == "write_json":
            return await self.write_json(
                path, kwargs.get("data", {}), kwargs.get("indent", 2)
            )
        else:
            return {
                "success": False,
                "error": f"Unknown operation: {operation}",
                "path": path,
            }

    async def read_file(self, path: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """Read a file"""
        full_path = self._get_full_path(path)

        try:
            with open(full_path, "r", encoding=encoding) as f:
                content = f.read()

            result = {
                "success": True,
                "content": content,
                "path": full_path,
                "size": len(content.encode(encoding)),
            }

            # Log file read
            self.logger.log_file_operation(
                operation="read",
                file_path=full_path,
                content_length=len(content.encode(encoding)),
                success=True,
            )

            return result

        except Exception as e:
            # Log failed file read
            self.logger.log_file_operation(
                operation="read", file_path=full_path, success=False
            )

            return {"success": False, "error": str(e), "path": full_path}

    async def write_file(
        self, path: str, content: str, encoding: str = "utf-8", create_dirs: bool = True
    ) -> Dict[str, Any]:
        """Write to a file"""
        full_path = self._get_full_path(path)

        try:
            if create_dirs:
                os.makedirs(os.path.dirname(full_path), exist_ok=True)

            with open(full_path, "w", encoding=encoding) as f:
                f.write(content)

            result = {
                "success": True,
                "path": full_path,
                "bytes_written": len(content.encode(encoding)),
            }

            # Log file write
            self.logger.log_file_operation(
                operation="write",
                file_path=full_path,
                content_length=len(content.encode(encoding)),
                success=True,
            )

            return result

        except Exception as e:
            # Log failed file write
            self.logger.log_file_operation(
                operation="write",
                file_path=full_path,
                content_length=len(content.encode(encoding)) if content else 0,
                success=False,
            )

            return {"success": False, "error": str(e), "path": full_path}

    async def create_directory(self, path: str) -> Dict[str, Any]:
        """Create a directory"""
        full_path = self._get_full_path(path)

        try:
            os.makedirs(full_path, exist_ok=True)
            return {"success": True, "path": full_path, "created": True}

        except Exception as e:
            return {"success": False, "error": str(e), "path": full_path}

    async def list_directory(
        self, path: str = ".", recursive: bool = False, include_hidden: bool = False
    ) -> Dict[str, Any]:
        """List directory contents"""
        full_path = self._get_full_path(path)

        try:
            if recursive:
                items = []
                for root, dirs, files in os.walk(full_path):
                    if not include_hidden:
                        dirs[:] = [d for d in dirs if not d.startswith(".")]
                        files = [f for f in files if not f.startswith(".")]

                    for file in files:
                        items.append(
                            {
                                "name": file,
                                "path": os.path.relpath(
                                    os.path.join(root, file), full_path
                                ),
                                "type": "file",
                            }
                        )
                    for dir in dirs:
                        items.append(
                            {
                                "name": dir,
                                "path": os.path.relpath(
                                    os.path.join(root, dir), full_path
                                ),
                                "type": "directory",
                            }
                        )
            else:
                items = []
                for item in os.listdir(full_path):
                    if not include_hidden and item.startswith("."):
                        continue

                    item_path = os.path.join(full_path, item)
                    items.append(
                        {
                            "name": item,
                            "path": item,
                            "type": "directory" if os.path.isdir(item_path) else "file",
                        }
                    )

            return {
                "success": True,
                "items": items,
                "path": full_path,
                "count": len(items),
            }

        except Exception as e:
            return {"success": False, "error": str(e), "path": full_path}

    async def exists(self, path: str) -> Dict[str, Any]:
        """Check if a file or directory exists"""
        full_path = self._get_full_path(path)

        return {
            "success": True,
            "exists": os.path.exists(full_path),
            "path": full_path,
            "type": "directory"
            if os.path.isdir(full_path)
            else "file"
            if os.path.isfile(full_path)
            else "unknown",
        }

    async def delete(self, path: str) -> Dict[str, Any]:
        """Delete a file or directory"""
        full_path = self._get_full_path(path)

        try:
            if os.path.isfile(full_path):
                os.remove(full_path)
            elif os.path.isdir(full_path):
                shutil.rmtree(full_path)
            else:
                return {
                    "success": False,
                    "error": "Path does not exist",
                    "path": full_path,
                }

            return {"success": True, "path": full_path, "deleted": True}

        except Exception as e:
            return {"success": False, "error": str(e), "path": full_path}

    async def copy(self, source: str, dest: str) -> Dict[str, Any]:
        """Copy a file or directory"""
        source_path = self._get_full_path(source)
        dest_path = self._get_full_path(dest)

        try:
            if os.path.isfile(source_path):
                shutil.copy2(source_path, dest_path)
            elif os.path.isdir(source_path):
                shutil.copytree(source_path, dest_path)
            else:
                return {
                    "success": False,
                    "error": "Source path does not exist",
                    "source": source_path,
                }

            return {
                "success": True,
                "source": source_path,
                "dest": dest_path,
                "copied": True,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "source": source_path,
                "dest": dest_path,
            }

    async def move(self, source: str, dest: str) -> Dict[str, Any]:
        """Move a file or directory"""
        source_path = self._get_full_path(source)
        dest_path = self._get_full_path(dest)

        try:
            shutil.move(source_path, dest_path)

            return {
                "success": True,
                "source": source_path,
                "dest": dest_path,
                "moved": True,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "source": source_path,
                "dest": dest_path,
            }

    async def get_file_info(self, path: str) -> Dict[str, Any]:
        """Get file information"""
        full_path = self._get_full_path(path)

        try:
            stat = os.stat(full_path)

            return {
                "success": True,
                "path": full_path,
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "created": stat.st_ctime,
                "type": "directory" if os.path.isdir(full_path) else "file",
            }

        except Exception as e:
            return {"success": False, "error": str(e), "path": full_path}

    async def read_json(self, path: str) -> Dict[str, Any]:
        """Read and parse JSON file"""
        full_path = self._get_full_path(path)

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            return {"success": True, "data": data, "path": full_path}

        except Exception as e:
            return {"success": False, "error": str(e), "path": full_path}

    async def write_json(self, path: str, data: Any, indent: int = 2) -> Dict[str, Any]:
        """Write data to JSON file"""
        full_path = self._get_full_path(path)

        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            with open(full_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)

            return {"success": True, "path": full_path, "written": True}

        except Exception as e:
            return {"success": False, "error": str(e), "path": full_path}


# Create MAS Tool wrapper if available
if MAS_AVAILABLE:

    def FileSystemTool_MAS(working_directory: str = "."):
        """Create file system tool as MAS Tool"""
        return create_file_system_tool(working_directory)
