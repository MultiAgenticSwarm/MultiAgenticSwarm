"""
Abstract debugger agent interface.
All debugging logic comes from LLMs - no hardcoded debug patterns.
"""

from abc import abstractmethod
from typing import Dict, Any, List, Optional
from ..core.base import BaseAgent
from ..core.types import AgentRole, TaskContext, ExecutionResult

class AbstractDebuggerAgent(BaseAgent):
    """
    Abstract debugger agent that uses LLM for ALL debugging decisions.
    No hardcoded debugging patterns - all knowledge comes from LLM.
    """

    def __init__(self, name: str, system: Optional[Any] = None, **kwargs):
        super().__init__(
            name=name,
            role=AgentRole.DEBUGGER,
            system=system,
            **kwargs
        )

    def _get_specialized_instructions(self) -> str:
        """Base debugger instructions"""
        return """You are an expert debugger responsible for:

- Analyzing errors and issues
- Identifying root causes of problems
- Providing debugging strategies
- Fixing bugs and issues
- Preventing future issues
- Improving system reliability

Debugging principles:
- Reproduce issues consistently
- Use systematic debugging approaches
- Gather comprehensive information
- Test hypotheses methodically
- Document findings clearly
- Implement robust fixes

Key responsibilities:
- Analyze error logs and stack traces
- Identify patterns in failures
- Design debugging experiments
- Implement fixes and improvements
- Validate solutions thoroughly
- Share debugging knowledge

Always provide step-by-step analysis and clear explanations.
"""

    @abstractmethod
    async def analyze_error(
        self,
        error_description: str,
        error_logs: List[str],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Analyze an error using LLM analysis.

        Args:
            error_description: Description of the error
            error_logs: Error logs and stack traces
            context: Additional context

        Returns:
            ExecutionResult with error analysis
        """
        pass

    @abstractmethod
    async def identify_root_cause(
        self,
        error_analysis: Dict[str, Any],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Identify the root cause of an issue.

        Args:
            error_analysis: Analysis of the error
            context: Additional context

        Returns:
            ExecutionResult with root cause analysis
        """
        pass

    @abstractmethod
    async def create_debugging_plan(
        self,
        issue_description: str,
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Create a systematic debugging plan.

        Args:
            issue_description: Description of the issue
            context: Additional context

        Returns:
            ExecutionResult with debugging plan
        """
        pass

    @abstractmethod
    async def implement_fix(
        self,
        root_cause: Dict[str, Any],
        fix_strategy: str,
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Implement a fix for the identified issue.

        Args:
            root_cause: Root cause analysis
            fix_strategy: Strategy for fixing
            context: Additional context

        Returns:
            ExecutionResult with fix implementation
        """
        pass

    @abstractmethod
    async def validate_fix(
        self,
        fix_implementation: Dict[str, Any],
        test_scenarios: List[str],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Validate that the fix works correctly.

        Args:
            fix_implementation: The implemented fix
            test_scenarios: Test scenarios to validate
            context: Additional context

        Returns:
            ExecutionResult with validation results
        """
        pass

    @abstractmethod
    async def prevent_regression(
        self,
        issue_analysis: Dict[str, Any],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Implement measures to prevent regression.

        Args:
            issue_analysis: Analysis of the issue
            context: Additional context

        Returns:
            ExecutionResult with prevention measures
        """
        pass
