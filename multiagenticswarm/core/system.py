"""
Main system orchestrator that manages agents, tools, tasks, and automations.
"""

import asyncio
import json
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .agent import Agent
from .tool import Tool, create_logger_tool, create_memory_tool
from .task import Task, Collaboration, TaskStatus
from .trigger import Trigger
from .automation import Automation
from .base_tool import BaseTool, FunctionTool, ToolScope
from .tool_executor import ToolExecutor
from ..utils.logger import get_logger, setup_comprehensive_logging, get_logging_config

logger = get_logger(__name__)


class System:
    """
    The main orchestration system for multi-agent workflows.
    
    The System class manages:
    - Agent registry and lifecycle
    - Tool registry with hierarchical sharing
    - Task execution and coordination
    - Event-driven automations
    - Configuration loading and management
    """
    
    def __init__(self, config_path: Optional[str] = None, enable_logging: bool = True, verbose: bool = False):
        """
        Initialize the system.
        
        Args:
            config_path: Optional path to configuration file
            enable_logging: Whether to enable comprehensive logging
            verbose: Enable verbose/debug logging
        """
        # Initialize comprehensive logging if requested
        if enable_logging:
            # Check if logging is already configured
            current_config = get_logging_config()
            if not current_config:
                setup_comprehensive_logging(verbose=verbose)
        
        # Core registries
        self.agents: Dict[str, Agent] = {}
        self.tools: Dict[str, Tool] = {}
        self.tasks: Dict[str, Task] = {}
        self.triggers: Dict[str, Trigger] = {}
        self.automations: Dict[str, Automation] = {}
        self.collaborations: Dict[str, Collaboration] = {}
        
        # Initialize new standardized tool executor
        self.tool_executor = ToolExecutor()
        
        # Runtime state
        self.running = False
        self.event_queue: List[Dict[str, Any]] = []
        self.execution_context: Dict[str, Any] = {}
        
        # Add built-in tools
        self._add_builtin_tools()
        
        # Load configuration if provided
        if config_path:
            self.load_config(config_path)
        
        logger.log_system_event("system_initialized", {
            "config_path": config_path,
            "logging_enabled": enable_logging,
            "verbose": verbose
        })
        logger.info("MultiAgenticSwarm initialized")
    
    @property
    def events(self) -> List[Dict[str, Any]]:
        """Alias for event_queue to maintain backward compatibility with tests."""
        return self.event_queue
    
    def _add_builtin_tools(self) -> None:
        """Add built-in utility tools to the system."""
        # Add standardized built-in tools
        def log_message(message: str, level: str = "info") -> str:
            logger_func = getattr(logger, level.lower(), logger.info)
            logger_func(f"AGENT LOG: {message}")
            return f"Logged: {message}"
        
        logger_std_tool = FunctionTool(
            func=log_message,
            name="Logger",
            description="Log messages for debugging and tracking"
        )
        logger_std_tool.set_global()
        self.register_tool(logger_std_tool)
        
        # Memory tool
        memory_store = {}
        
        def store_memory(key: str, value: str) -> str:
            memory_store[key] = value
            return f"Stored '{key}': {value}"
        
        memory_std_tool = FunctionTool(
            func=store_memory,
            name="StoreMemory", 
            description="Store information in memory"
        )
        memory_std_tool.set_global()
        self.register_tool(memory_std_tool)
        
        logger.debug("Added built-in tools: Logger, StoreMemory")
    
    # Agent Management
    def register_agent(self, agent: Agent) -> None:
        """Register a single agent."""
        self.agents[agent.name] = agent
        self._update_agent_tools(agent)
        logger.info(f"Registered agent: {agent.name}")
    
    def register_agents(self, *agents: Agent) -> None:
        """Register multiple agents."""
        for agent in agents:
            self.register_agent(agent)
    
    def get_agent(self, name: str) -> Optional[Agent]:
        """Get an agent by name."""
        return self.agents.get(name)
    
    def list_agents(self) -> List[str]:
        """List all registered agent names."""
        return list(self.agents.keys())
    
    def remove_agent(self, name: str) -> bool:
        """Remove an agent from the system."""
        if name in self.agents:
            del self.agents[name]
            logger.info(f"Removed agent: {name}")
            return True
        return False
    
    # Tool Management
    def register_tool(self, tool: Union[Tool, BaseTool]) -> None:
        """Register a single tool (legacy or standardized)."""
        # Register with legacy system for backwards compatibility
        if isinstance(tool, Tool):
            self.tools[tool.name] = tool
            self._update_all_agent_tools()
        elif isinstance(tool, BaseTool):
            # For BaseTool instances (like FunctionTool), also add to legacy tools dict
            # This ensures backward compatibility with existing tests and code
            self.tools[tool.name] = tool
            self._update_all_agent_tools()
        
        # Register with new standardized system
        if isinstance(tool, BaseTool):
            self.tool_executor.register_tool(tool)
        
        logger.info(f"Registered tool: {tool.name}")
    
    def register_tools(self, *tools: Union[Tool, BaseTool]) -> None:
        """Register multiple tools (legacy or standardized)."""
        for tool in tools:
            self.register_tool(tool)
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self.tools.get(name)
    
    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self.tools.keys())
    
    def remove_tool(self, name: str) -> bool:
        """Remove a tool from the system."""
        removed = False
        
        # Remove from legacy tools
        if name in self.tools:
            del self.tools[name]
            self._update_all_agent_tools()
            removed = True
        
        # Remove from standardized tool executor
        if hasattr(self.tool_executor, 'tools') and name in self.tool_executor.tools:
            del self.tool_executor.tools[name]
            removed = True
        
        if removed:
            logger.info(f"Removed tool: {name}")
        
        return removed
    
    def _update_agent_tools(self, agent: Agent) -> None:
        """Update an agent's tool access lists."""
        agent.local_tools.clear()
        agent.shared_tools.clear()
        agent.global_tools.clear()
        
        for tool_name, tool in self.tools.items():
            if tool.is_global:
                agent.global_tools.append(tool_name)
            elif tool.local_agent == agent.name:
                agent.local_tools.append(tool_name)
            elif agent.name in tool.shared_agents:
                agent.shared_tools.append(tool_name)
    
    def _update_all_agent_tools(self) -> None:
        """Update tool access for all agents."""
        for agent in self.agents.values():
            self._update_agent_tools(agent)
    
    # Task Management
    def register_task(self, task: Task) -> None:
        """Register a single task."""
        self.tasks[task.name] = task
        logger.info(f"Registered task: {task.name}")
    
    def register_tasks(self, *tasks: Task) -> None:
        """Register multiple tasks."""
        for task in tasks:
            self.register_task(task)
    
    def get_task(self, name: str) -> Optional[Task]:
        """Get a task by name."""
        return self.tasks.get(name)
    
    def list_tasks(self) -> List[str]:
        """List all registered task names."""
        return list(self.tasks.keys())
    
    def remove_task(self, name: str) -> bool:
        """Remove a task from the system."""
        if name in self.tasks:
            del self.tasks[name]
            logger.info(f"Removed task: {name}")
            return True
        return False
    
    # Trigger Management
    def register_trigger(self, trigger: Trigger) -> None:
        """Register a single trigger."""
        self.triggers[trigger.name] = trigger
        logger.info(f"Registered trigger: {trigger.name}")
    
    def register_triggers(self, *triggers: Trigger) -> None:
        """Register multiple triggers."""
        for trigger in triggers:
            self.register_trigger(trigger)
    
    def get_trigger(self, name: str) -> Optional[Trigger]:
        """Get a trigger by name."""
        return self.triggers.get(name)
    
    def list_triggers(self) -> List[str]:
        """List all registered trigger names."""
        return list(self.triggers.keys())
    
    def remove_trigger(self, name: str) -> bool:
        """Remove a trigger from the system."""
        if name in self.triggers:
            del self.triggers[name]
            logger.info(f"Removed trigger: {name}")
            return True
        return False
    
    # Automation Management
    def register_automation(self, automation: Automation) -> None:
        """Register a single automation."""
        self.automations[automation.name] = automation
        logger.info(f"Registered automation: {automation.name}")
    
    def register_automations(self, *automations: Automation) -> None:
        """Register multiple automations."""
        for automation in automations:
            self.register_automation(automation)
    
    def get_automation(self, name: str) -> Optional[Automation]:
        """Get an automation by name."""
        return self.automations.get(name)
    
    def list_automations(self) -> List[str]:
        """List all registered automation names."""
        return list(self.automations.keys())
    
    def remove_automation(self, name: str) -> bool:
        """Remove an automation from the system."""
        if name in self.automations:
            del self.automations[name]
            logger.info(f"Removed automation: {name}")
            return True
        return False
    
    # Collaboration Management
    def register_collaboration(self, collaboration: Collaboration) -> None:
        """Register a collaboration."""
        self.collaborations[collaboration.name] = collaboration
        logger.info(f"Registered collaboration: {collaboration.name}")
    
    def register_collaborations(self, *collaborations: Collaboration) -> None:
        """Register multiple collaborations."""
        for collaboration in collaborations:
            self.register_collaboration(collaboration)
    
    # Event Processing
    def emit_event(self, event: Dict[str, Any]) -> None:
        """Emit an event to the system."""
        self.event_queue.append(event)
        logger.debug(f"Emitted event: {event.get('type', 'unknown')}")
    
    async def process_events(self) -> None:
        """Process pending events and trigger automations."""
        while self.event_queue:
            event = self.event_queue.pop(0)
            await self._process_single_event(event)
    
    async def _process_single_event(self, event: Dict[str, Any]) -> None:
        """Process a single event."""
        logger.debug(f"Processing event: {event}")
        
        # Check all triggers
        for trigger in self.triggers.values():
            if trigger.evaluate(event):
                trigger.fire(event)
                
                # Find automations for this trigger
                for automation in self.automations.values():
                    if automation.trigger_name == trigger.name:
                        await automation.execute(event, self.execution_context, self.tasks)
    
    # Execution Methods
    async def execute_task(
        self,
        task_name: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a specific task."""
        task = self.get_task(task_name)
        if not task:
            logger.error(f"Task '{task_name}' not found")
            return {
                "task_name": task_name,
                "status": "failed",
                "error": f"Task '{task_name}' not found",
                "results": [],
                "success": False
            }
        
        logger.info(f"Executing task: {task_name}")
        
        results = []
        task.status = TaskStatus.RUNNING
        
        for step in task.steps:
            agent = self.get_agent(step.agent)
            if not agent:
                error_msg = f"Agent '{step.agent}' not found for task '{task_name}'"
                logger.error(error_msg)
                task.mark_step_failed(error_msg)
                return {
                    "task_name": task_name,
                    "status": "failed",
                    "error": error_msg,
                    "results": results,
                    "success": False
                }
            
            # Get available tools for this agent
            available_tools = agent.get_available_tools(self.tools)
            
            # Execute the step - CRITICAL FIX: Pass tool registry
            try:
                result = await agent.execute(
                    input_text=step.input_data,
                    context=context or {},
                    available_tools=available_tools,
                    tool_registry=self.tools  # CRITICAL FIX: Pass tool registry
                )
                
                results.append(result)
                task.mark_step_completed(result)
                
            except Exception as e:
                task.mark_step_failed(str(e))
                logger.error(f"Task step failed: {e}")
                break
        
        task.status = TaskStatus.COMPLETED if task.current_step >= len(task.steps) else TaskStatus.FAILED
        
        return {
            "task_name": task_name,
            "status": task.status,
            "results": results,
            "success": task.is_completed()
        }
    
    async def execute_agent(
        self,
        agent_name: str,
        input_text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a single agent with standardized tool support."""
        agent = self.get_agent(agent_name)
        if not agent:
            logger.error(f"Agent '{agent_name}' not found")
            return {
                "agent_name": agent_name,
                "error": f"Agent '{agent_name}' not found",
                "result": None,
                "success": False
            }
        
        try:
            result = await agent.execute(
                input_text, 
                context or {}, 
                tool_executor=self.tool_executor  # Pass the standardized tool executor
            )
            return {
                "agent_name": agent_name,
                "result": result,
                "success": True
            }
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            return {
                "agent_name": agent_name,
                "error": str(e),
                "result": None,
                "success": False
            }
    
    # Configuration Management
    def load_config(self, config_path: str) -> None:
        """Load system configuration from file."""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_file, 'r') as f:
                if config_file.suffix.lower() in ['.yaml', '.yml']:
                    config = yaml.safe_load(f)
                else:
                    config = json.load(f)
            
            self._apply_config(config)
            logger.info(f"Loaded configuration from: {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _apply_config(self, config: Dict[str, Any]) -> None:
        """Apply configuration to the system."""
        # Load agents
        for agent_config in config.get('agents', []):
            agent = Agent.from_dict(agent_config)
            self.register_agent(agent)
        
        # Load tools (function implementations need to be provided separately)
        for tool_config in config.get('tools', []):
            tool = Tool.from_dict(tool_config)
            self.register_tool(tool)
        
        # Load tasks
        for task_config in config.get('tasks', []):
            task = Task.from_dict(task_config)
            self.register_task(task)
        
        # Load triggers
        for trigger_config in config.get('triggers', []):
            trigger = Trigger.from_dict(trigger_config)
            self.register_trigger(trigger)
        
        # Load automations
        for automation_config in config.get('automations', []):
            automation = Automation.from_dict(automation_config, self.triggers)
            self.register_automation(automation)
    
    def save_config(self, config_path: str) -> None:
        """Save current system configuration to file."""
        config = {
            'agents': [agent.to_dict() for agent in self.agents.values()],
            'tools': [tool.to_dict() for tool in self.tools.values()],
            'tasks': [task.to_dict() for task in self.tasks.values()],
            'triggers': [trigger.to_dict() for trigger in self.triggers.values()],
            'automations': [automation.to_dict() for automation in self.automations.values()]
        }
        
        config_file = Path(config_path)
        with open(config_file, 'w') as f:
            if config_file.suffix.lower() in ['.yaml', '.yml']:
                yaml.safe_dump(config, f, default_flow_style=False)
            else:
                json.dump(config, f, indent=2)
        
        logger.info(f"Saved configuration to: {config_path}")
    
    # System Control
    def run(self) -> None:
        """Run the system in blocking mode."""
        asyncio.run(self.run_async())
    
    async def run_async(self) -> None:
        """Run the system asynchronously."""
        self.running = True
        logger.info("Starting MultiAgenticSwarm...")
        
        try:
            while self.running:
                await self.process_events()
                await asyncio.sleep(0.1)  # Small delay to prevent tight loop
                
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            await self.shutdown()
    
    async def shutdown(self) -> None:
        """Shutdown the system gracefully."""
        self.running = False
        logger.info("MultiAgenticSwarm shut down")
    
    # System Information
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status."""
        return {
            "running": self.running,
            "agents": len(self.agents),
            "tools": len(self.tools),
            "tasks": len(self.tasks),
            "triggers": len(self.triggers),
            "automations": len(self.automations),
            "collaborations": len(self.collaborations),
            "pending_events": len(self.event_queue)
        }
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get detailed system information."""
        # Convert tools safely
        tools_info = {}
        for name, tool in self.tools.items():
            try:
                if hasattr(tool, 'to_dict'):
                    tools_info[name] = tool.to_dict()
                else:
                    # Fallback for tools without to_dict method
                    tools_info[name] = {
                        "name": getattr(tool, 'name', name),
                        "description": getattr(tool, 'description', ''),
                        "scope": getattr(tool, 'scope', 'unknown')
                    }
            except Exception as e:
                # Fallback in case of any error
                tools_info[name] = {
                    "name": name,
                    "error": str(e)
                }
        
        return {
            "version": "1.0.0",  # Add version info for compatibility
            "components": {  # Add components info for compatibility
                "agents": len(self.agents),
                "tools": len(self.tools),
                "tasks": len(self.tasks),
                "triggers": len(self.triggers),
                "automations": len(self.automations)
            },
            "status": self.get_system_status(),
            "agents": {name: agent.to_dict() for name, agent in self.agents.items()},
            "tools": tools_info,
            "tasks": {name: task.to_dict() for name, task in self.tasks.items()},
            "triggers": {name: trigger.to_dict() for name, trigger in self.triggers.items()},
            "automations": {name: automation.to_dict() for name, automation in self.automations.items()}
        }
    
    @classmethod
    def from_config(cls, config_path: str) -> "System":
        """Create a system instance from configuration file."""
        system = cls()
        system.load_config(config_path)
        return system
    
    @classmethod
    def create_default(cls) -> "System":
        """Create a system with sensible defaults."""
        return cls(enable_logging=False)  # Create with default settings
    
    def __repr__(self) -> str:
        return f"System(agents={len(self.agents)}, tools={len(self.tools)}, tasks={len(self.tasks)})"
    
    # Logging and Stats Methods
    def get_logging_info(self) -> Dict[str, Any]:
        """Get information about current logging configuration."""
        config = get_logging_config()
        if not config:
            return {"logging_enabled": False, "message": "Logging not configured"}
        
        return {
            "logging_enabled": True,
            "session_id": config.get("session_id"),
            "log_directory": config.get("log_directory"),
            "text_log_file": config.get("text_log_file"),
            "json_log_file": config.get("json_log_file"),
            "verbose": config.get("verbose", False)
        }
    
    def enable_logging(self, verbose: bool = False, log_directory: Optional[str] = None) -> Dict[str, str]:
        """Enable comprehensive logging for the system."""
        return setup_comprehensive_logging(
            verbose=verbose,
            log_directory=log_directory
        )
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics and activity."""
        stats = {
            "components": {  # Add components for test compatibility
                "agents": len(self.agents),
                "tools": len(self.tools),
                "tasks": len(self.tasks),
                "triggers": len(self.triggers),
                "automations": len(self.automations)
            },
            "agents": {
                "count": len(self.agents),
                "names": list(self.agents.keys())
            },
            "tools": {
                "count": len(self.tools),
                "names": list(self.tools.keys())
            },
            "tasks": {
                "count": len(self.tasks),
                "names": list(self.tasks.keys())
            },
            "triggers": {
                "count": len(self.triggers),
                "names": list(self.triggers.keys())
            },
            "automations": {
                "count": len(self.automations),
                "names": list(self.automations.keys())
            },
            "system_state": {
                "running": self.running,
                "event_queue_size": len(self.event_queue)
            },
            "logging": self.get_logging_info()
        }
        
        logger.log_system_event("system_stats_requested", stats)
        return stats
