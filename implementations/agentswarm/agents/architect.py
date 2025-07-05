"""
Abstract architect agent interface.
All architectural decisions come from LLMs - no hardcoded patterns.
"""

from abc import abstractmethod
from typing import Dict, Any, List, Optional
from ..core.base import BaseAgent
from ..core.types import AgentRole, TaskContext, ExecutionResult

class AbstractArchitectAgent(BaseAgent):
    """
    Abstract architect agent that uses LLM for ALL architectural decisions.
    No hardcoded architectural patterns - all knowledge comes from LLM.
    """

    def __init__(self, name: str, system: Optional[Any] = None, **kwargs):
        super().__init__(
            name=name,
            role=AgentRole.ARCHITECT,
            system=system,
            **kwargs
        )

    def _get_specialized_instructions(self) -> str:
        """Base architect instructions"""
        return """You are an expert software architect responsible for:

- Designing system architectures and patterns
- Making technology stack decisions
- Creating technical specifications
- Defining component interactions
- Ensuring scalability and maintainability
- Establishing coding standards and practices

Architectural principles:
- Design for scalability and performance
- Ensure loose coupling and high cohesion
- Follow SOLID principles
- Choose appropriate design patterns
- Consider security from the start
- Plan for testing and maintenance

Key responsibilities:
- Analyze requirements and constraints
- Design system architecture
- Choose appropriate technologies
- Define interfaces and APIs
- Create technical documentation
- Guide implementation decisions

Always provide clear rationale for your architectural decisions.
"""

    @abstractmethod
    async def analyze_requirements(
        self,
        requirements: str,
        constraints: List[str],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Analyze requirements and identify architectural needs.

        Args:
            requirements: System requirements
            constraints: Technical constraints
            context: Additional context

        Returns:
            ExecutionResult with requirements analysis
        """
        pass

    @abstractmethod
    async def design_architecture(
        self,
        requirements_analysis: Dict[str, Any],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Design system architecture using LLM analysis.

        Args:
            requirements_analysis: Analysis of requirements
            context: Additional context

        Returns:
            ExecutionResult with architectural design
        """
        pass

    @abstractmethod
    async def choose_technology_stack(
        self,
        requirements: Dict[str, Any],
        constraints: List[str],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Choose appropriate technology stack.

        Args:
            requirements: System requirements
            constraints: Technical constraints
            context: Additional context

        Returns:
            ExecutionResult with technology recommendations
        """
        pass

    @abstractmethod
    async def define_interfaces(
        self,
        architecture: Dict[str, Any],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Define component interfaces and APIs.

        Args:
            architecture: System architecture
            context: Additional context

        Returns:
            ExecutionResult with interface definitions
        """
        pass

    @abstractmethod
    async def create_technical_specification(
        self,
        architecture: Dict[str, Any],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Create detailed technical specification.

        Args:
            architecture: System architecture
            context: Additional context

        Returns:
            ExecutionResult with technical specification
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
        Review and validate architecture.

        Args:
            architecture: Architecture to review
            review_criteria: Review criteria
            context: Additional context

        Returns:
            ExecutionResult with architecture review
        """
        pass
