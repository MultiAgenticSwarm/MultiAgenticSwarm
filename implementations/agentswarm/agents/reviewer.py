"""
Abstract reviewer agent interface.
All review logic comes from LLMs - no hardcoded review patterns.
"""

from abc import abstractmethod
from typing import Dict, Any, List, Optional
from ..core.base import BaseAgent
from ..core.types import AgentRole, TaskContext, ExecutionResult

class AbstractReviewerAgent(BaseAgent):
    """
    Abstract reviewer agent that uses LLM for ALL review decisions.
    No hardcoded review patterns - all knowledge comes from LLM.
    """

    def __init__(self, name: str, system: Optional[Any] = None, **kwargs):
        super().__init__(
            name=name,
            role=AgentRole.REVIEWER,
            system=system,
            **kwargs
        )

    def _get_specialized_instructions(self) -> str:
        """Base reviewer instructions"""
        return """You are an expert code reviewer responsible for:

- Reviewing code quality and standards
- Ensuring best practices are followed
- Identifying potential issues and improvements
- Providing constructive feedback
- Maintaining code consistency
- Sharing knowledge and expertise

Review principles:
- Be thorough but constructive
- Focus on code quality and maintainability
- Consider security and performance implications
- Provide specific, actionable feedback
- Recognize good practices as well as issues
- Maintain team coding standards

Key responsibilities:
- Review code for quality and standards
- Check for potential bugs and issues
- Verify adherence to best practices
- Ensure proper documentation
- Validate test coverage
- Provide learning opportunities

Always provide balanced, constructive feedback with clear explanations.
"""

    @abstractmethod
    async def review_code(
        self,
        code_path: str,
        review_criteria: List[str],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Review code using LLM analysis.

        Args:
            code_path: Path to code to review
            review_criteria: Criteria for review
            context: Additional context

        Returns:
            ExecutionResult with review feedback
        """
        pass

    @abstractmethod
    async def review_architecture(
        self,
        architecture: Dict[str, Any],
        review_criteria: List[str],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Review system architecture.

        Args:
            architecture: Architecture to review
            review_criteria: Review criteria
            context: Additional context

        Returns:
            ExecutionResult with architecture review
        """
        pass

    @abstractmethod
    async def review_tests(
        self,
        test_suite: str,
        coverage_report: Dict[str, Any],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Review test suite and coverage.

        Args:
            test_suite: Test suite to review
            coverage_report: Test coverage report
            context: Additional context

        Returns:
            ExecutionResult with test review
        """
        pass

    @abstractmethod
    async def review_documentation(
        self,
        documentation: str,
        completeness_criteria: List[str],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Review documentation quality and completeness.

        Args:
            documentation: Documentation to review
            completeness_criteria: Criteria for completeness
            context: Additional context

        Returns:
            ExecutionResult with documentation review
        """
        pass

    @abstractmethod
    async def review_security(
        self,
        code_path: str,
        security_checklist: List[str],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Review code for security issues.

        Args:
            code_path: Path to code to review
            security_checklist: Security checklist
            context: Additional context

        Returns:
            ExecutionResult with security review
        """
        pass

    @abstractmethod
    async def review_performance(
        self,
        code_path: str,
        performance_metrics: Dict[str, Any],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Review code for performance issues.

        Args:
            code_path: Path to code to review
            performance_metrics: Performance metrics
            context: Additional context

        Returns:
            ExecutionResult with performance review
        """
        pass

    async def provide_feedback(
        self,
        review_results: List[ExecutionResult],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Provide consolidated feedback from multiple reviews.

        Args:
            review_results: Results from various reviews
            context: Additional context

        Returns:
            ExecutionResult with consolidated feedback
        """

        feedback_task = f"""
        Provide consolidated feedback based on these review results:
        {[result.output for result in review_results]}

        Create a comprehensive summary that includes:
        1. Overall assessment
        2. Key issues to address
        3. Recommendations for improvement
        4. Positive aspects to highlight
        5. Prioritized action items

        Make the feedback constructive and actionable.
        """

        return await self.execute(feedback_task, context)
