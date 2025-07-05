"""
Abstract developer agent interface.
All development logic comes from LLMs - no hardcoded patterns.
"""

from abc import abstractmethod
from typing import Dict, Any, List, Optional
from ..core.base import BaseAgent
from ..core.types import AgentRole, TaskContext, ExecutionResult

class AbstractDeveloperAgent(BaseAgent):
    """
    Abstract developer agent that uses LLM for ALL development decisions.
    No hardcoded logic - all knowledge comes from LLM.

    This class defines the interface that all developer agents must implement,
    regardless of the target platform or technology.
    """

    def __init__(self, name: str, system: Optional[Any] = None, **kwargs):
        super().__init__(
            name=name,
            role=AgentRole.DEVELOPER,
            system=system,
            **kwargs
        )

    def _get_specialized_instructions(self) -> str:
        """Base developer instructions - should be extended by implementations"""
        return """You are an expert software developer responsible for:

- Writing clean, maintainable, and efficient code
- Following industry best practices and patterns
- Implementing features according to requirements
- Refactoring code to improve quality
- Debugging and fixing issues
- Collaborating with other agents (architects, testers, reviewers)

Key principles:
- Write self-documenting code with clear variable names
- Add comprehensive error handling
- Follow the DRY (Don't Repeat Yourself) principle
- Use appropriate design patterns
- Optimize for readability and maintainability
- Include detailed comments for complex logic

When implementing features:
1. Analyze requirements thoroughly
2. Design the solution architecture
3. Write the implementation
4. Test your code
5. Document your work

Always explain your decisions and provide context for your choices.
"""

    @abstractmethod
    async def generate_code(
        self,
        requirements: str,
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Generate code based on requirements.
        ALL code comes from LLM, no templates or hardcoded logic.

        Args:
            requirements: Natural language description of what to build
            context: Additional context about the project

        Returns:
            ExecutionResult with generated code and implementation details
        """
        pass

    @abstractmethod
    async def implement_feature(
        self,
        feature_description: str,
        project_context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Implement a complete feature using LLM reasoning.
        LLM decides architecture, patterns, and implementation.

        Args:
            feature_description: Description of the feature to implement
            project_context: Current state of the project

        Returns:
            ExecutionResult with implementation details
        """
        pass

    @abstractmethod
    async def refactor_code(
        self,
        code_path: str,
        refactoring_goals: List[str],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Refactor code using LLM analysis and decisions.

        Args:
            code_path: Path to the code to refactor
            refactoring_goals: List of goals for refactoring
            context: Additional context

        Returns:
            ExecutionResult with refactoring details
        """
        pass

    @abstractmethod
    async def debug_issue(
        self,
        issue_description: str,
        error_logs: Optional[List[str]] = None,
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Debug and fix issues using LLM analysis.

        Args:
            issue_description: Description of the issue
            error_logs: Optional error logs
            context: Additional context

        Returns:
            ExecutionResult with debugging analysis and fixes
        """
        pass

    @abstractmethod
    async def optimize_performance(
        self,
        performance_targets: Dict[str, Any],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Optimize code performance using LLM analysis.

        Args:
            performance_targets: Performance goals and metrics
            context: Additional context

        Returns:
            ExecutionResult with optimization recommendations
        """
        pass

    async def code_review(
        self,
        code_path: str,
        review_criteria: List[str],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Perform code review using LLM analysis.

        Args:
            code_path: Path to code to review
            review_criteria: Criteria for the review
            context: Additional context

        Returns:
            ExecutionResult with review feedback
        """

        review_task = f"""
        Perform a thorough code review of the code at: {code_path}

        Review criteria: {review_criteria}

        Provide:
        1. Overall assessment
        2. Specific issues found
        3. Suggestions for improvement
        4. Positive aspects
        5. Rating (1-10)

        Focus on:
        - Code quality and readability
        - Best practices adherence
        - Security considerations
        - Performance implications
        - Maintainability
        """

        return await self.execute(review_task, context)

    async def generate_documentation(
        self,
        code_path: str,
        documentation_type: str = "api",
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Generate documentation using LLM analysis.

        Args:
            code_path: Path to code to document
            documentation_type: Type of documentation (api, user, dev)
            context: Additional context

        Returns:
            ExecutionResult with generated documentation
        """

        doc_task = f"""
        Generate {documentation_type} documentation for the code at: {code_path}

        Include:
        - Clear descriptions of functionality
        - Usage examples
        - Parameter explanations
        - Return value descriptions
        - Error handling information

        Make the documentation clear, comprehensive, and user-friendly.
        """

        return await self.execute(doc_task, context)
