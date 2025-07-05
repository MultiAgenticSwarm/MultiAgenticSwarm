"""
FlutterArchitectAgent - ALL architectural knowledge comes from LLM.
No hardcoded architectural patterns or decisions.
"""

from typing import Dict, Any, List, Optional
import logging

from implementations.agentswarm.agents import AbstractArchitectAgent
from implementations.agentswarm.core.types import TaskContext, ExecutionResult
from ..tools import FlutterCLITool, DartCLITool, FileSystemTool

# Import MAS as the core SDK
import multiagenticswarm as mas
from multiagenticswarm.core.agent import Agent

class FlutterArchitectAgent(AbstractArchitectAgent, Agent):
    """
    Flutter architect agent - ALL architectural knowledge comes from LLM.
    No hardcoded architectural patterns - all knowledge comes from LLM.
    """

    def __init__(self, name: str = "flutter_architect", working_directory: str = ".", **kwargs):
        self.working_directory = working_directory
        super().__init__(name=name, **kwargs)

        # Initialize tools
        self.flutter_cli = FlutterCLITool(working_directory)
        self.dart_cli = DartCLITool(working_directory)
        self.file_system = FileSystemTool(working_directory)

        self.logger = logging.getLogger(f"flutterswarm.{name}")

    def _get_specialized_instructions(self) -> str:
        """Flutter architecture specific instructions"""
        return """You are an expert Flutter architect with comprehensive knowledge of:

FLUTTER ARCHITECTURE PATTERNS:
- Clean Architecture for Flutter applications
- MVVM (Model-View-ViewModel) pattern
- MVC (Model-View-Controller) pattern
- Repository pattern for data access
- Service layer architecture
- Dependency injection patterns
- Layered architecture principles

STATE MANAGEMENT ARCHITECTURES:
- Provider pattern and state management
- Riverpod for dependency injection and state
- BLoC pattern and event-driven architecture
- GetX for state, navigation, and dependency management
- Redux pattern for predictable state management
- MobX for reactive state management
- setState and InheritedWidget patterns

PROJECT STRUCTURE:
- Feature-based folder organization
- Layer-based folder organization
- Domain-driven design structure
- Modular architecture patterns
- Package organization strategies
- File naming conventions

SCALABILITY CONSIDERATIONS:
- Modular architecture for large applications
- Microservices integration patterns
- Code reusability strategies
- Performance optimization architectures
- Memory management patterns
- Lazy loading and pagination strategies

PLATFORM ARCHITECTURE:
- Multi-platform considerations (iOS, Android, Web, Desktop)
- Platform-specific implementations
- Native integration patterns
- Plugin architecture and development
- Platform channel design
- Responsive design architectures

DATA ARCHITECTURE:
- Local data storage patterns (SQLite, Hive, SharedPreferences)
- Remote data integration (REST APIs, GraphQL)
- Caching strategies and implementations
- Offline-first architecture patterns
- Data synchronization patterns
- Database architecture design

NAVIGATION ARCHITECTURE:
- Navigator 1.0 and 2.0 patterns
- Nested navigation strategies
- Deep linking architecture
- Route management patterns
- Navigation state management
- Multi-screen navigation patterns

SECURITY ARCHITECTURE:
- Authentication and authorization patterns
- Secure storage implementations
- API security considerations
- Data encryption patterns
- Certificate pinning strategies
- Platform security integration

TESTING ARCHITECTURE:
- Testable architecture design
- Dependency injection for testing
- Mock and stub patterns
- Testing pyramid implementation
- Test organization strategies
- Continuous integration architecture

PERFORMANCE ARCHITECTURE:
- Widget optimization patterns
- Memory management strategies
- CPU optimization techniques
- Network optimization patterns
- Image and asset optimization
- Build performance optimization

IMPORTANT INSTRUCTIONS:
1. Use your comprehensive architectural knowledge to design robust systems
2. Follow Flutter and Dart best practices for architecture
3. Design for scalability, maintainability, and testability
4. Consider platform-specific requirements and constraints
5. Plan for performance, security, and user experience
6. Create clear architectural documentation
7. Design flexible and extensible architectures
8. Consider team structure and development workflow

When designing architecture:
- Analyze requirements thoroughly
- Consider non-functional requirements
- Design for change and evolution
- Plan component interactions
- Define clear boundaries and interfaces
- Consider deployment and DevOps requirements
- Plan for monitoring and observability

You have access to Flutter CLI, Dart CLI, and file system tools.
Use these to implement your architectural designs.
"""

    def _get_tools(self) -> List[Dict[str, Any]]:
        """Get tools for architecture design - tools come from the system"""
        return [
            {
                "name": "flutter_cli",
                "description": "Execute Flutter CLI commands",
                "scope": "global"
            },
            {
                "name": "dart_cli",
                "description": "Execute Dart CLI commands",
                "scope": "global"
            },
            {
                "name": "file_system",
                "description": "File system operations",
                "scope": "global"
            }
        ]

    async def analyze_requirements(
        self,
        requirements: str,
        constraints: List[str],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Analyze requirements and identify architectural needs.
        """

        analysis_prompt = f"""
Analyze these Flutter application requirements and constraints:

Requirements:
{requirements}

Constraints:
{constraints}

Project context: {context.__dict__ if context else 'None'}

Provide comprehensive architectural analysis:

1. REQUIREMENTS_BREAKDOWN: Break down functional and non-functional requirements
2. ARCHITECTURAL_DRIVERS: Identify key architectural drivers and quality attributes
3. CONSTRAINTS_ANALYSIS: Analyze technical and business constraints
4. SCALABILITY_REQUIREMENTS: Identify scalability needs and growth patterns
5. PERFORMANCE_REQUIREMENTS: Define performance targets and benchmarks
6. SECURITY_REQUIREMENTS: Identify security needs and compliance requirements
7. INTEGRATION_REQUIREMENTS: Define integration needs with external systems
8. PLATFORM_REQUIREMENTS: Analyze platform-specific requirements
9. TEAM_CONSIDERATIONS: Consider team size, skills, and structure
10. RISK_ASSESSMENT: Identify architectural risks and mitigation strategies

For each requirement, consider:
- Technical complexity and implementation challenges
- Impact on user experience and performance
- Scalability and maintainability implications
- Security and compliance considerations
- Integration and dependency requirements
- Testing and quality assurance needs

Provide a foundation for architectural decision-making.
"""

        return await self.execute(analysis_prompt, context)

    async def design_architecture(
        self,
        requirements_analysis: Dict[str, Any],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Design system architecture using LLM analysis.
        """

        design_prompt = f"""
Design a comprehensive Flutter architecture based on this analysis:
{requirements_analysis}

Project context: {context.__dict__ if context else 'None'}

Create a complete architectural design:

1. ARCHITECTURE_OVERVIEW: High-level architecture vision and principles
2. ARCHITECTURE_PATTERN: Choose and justify the main architectural pattern
3. LAYER_DESIGN: Define application layers and their responsibilities
4. STATE_MANAGEMENT: Design state management architecture
5. DATA_ARCHITECTURE: Design data flow and storage architecture
6. NAVIGATION_ARCHITECTURE: Design navigation and routing architecture
7. COMPONENT_DESIGN: Define key components and their interactions
8. INTEGRATION_DESIGN: Design external system integrations
9. SECURITY_DESIGN: Design security architecture and patterns
10. TESTING_ARCHITECTURE: Design testing strategy and structure
11. FOLDER_STRUCTURE: Define project folder organization
12. TECHNOLOGY_STACK: Recommend technology stack and packages

For each architectural decision:
- Provide clear rationale and justification
- Consider alternatives and trade-offs
- Address scalability and performance implications
- Consider maintenance and evolution requirements
- Include implementation guidelines

Generate a complete architectural blueprint that developers can follow.
"""

        design_result = await self.execute(design_prompt, context)

        if not design_result.success:
            return design_result

        # Extract architectural components from response
        architecture_files = self._extract_architecture_files_from_response(design_result.output)

        created_files = []

        # Create architecture documentation and template files
        for arch_file in architecture_files:
            result = await self.file_system.write_file(
                path=arch_file['path'],
                content=arch_file['content'],
                create_dirs=True
            )

            if result.get('success'):
                created_files.append(arch_file['path'])
                self.logger.info(f"Created architecture file: {arch_file['path']}")

        return ExecutionResult(
            success=True,
            agent_name=self.name,
            task_id=f"design_architecture_{len(self.execution_history)}",
            output={
                'architecture_design': design_result.output,
                'created_files': created_files,
                'architecture_files': architecture_files
            },
            created_files=created_files,
            next_steps=[
                "Review architectural design",
                "Validate architecture with stakeholders",
                "Create implementation plan",
                "Set up project structure",
                "Begin implementation following architecture"
            ]
        )

    async def choose_technology_stack(
        self,
        requirements: Dict[str, Any],
        constraints: List[str],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Choose appropriate technology stack.
        """

        tech_stack_prompt = f"""
Choose an optimal Flutter technology stack for these requirements:
{requirements}

Constraints: {constraints}
Project context: {context.__dict__ if context else 'None'}

Provide technology stack recommendations:

1. STACK_ANALYSIS: Analyze technology requirements and options
2. FLUTTER_VERSION: Recommend Flutter version and upgrade path
3. DART_VERSION: Recommend Dart version and language features
4. STATE_MANAGEMENT: Recommend state management solution
5. NETWORKING: Recommend networking and API libraries
6. DATABASE: Recommend local and remote database solutions
7. AUTHENTICATION: Recommend authentication and security libraries
8. UI_LIBRARIES: Recommend UI component libraries and packages
9. TESTING_LIBRARIES: Recommend testing frameworks and tools
10. DEVELOPMENT_TOOLS: Recommend development and debugging tools
11. CI_CD_TOOLS: Recommend continuous integration and deployment tools
12. MONITORING: Recommend monitoring and analytics tools

For each technology choice:
- Provide clear justification and benefits
- Consider alternatives and trade-offs
- Address compatibility and maintenance concerns
- Include implementation guidance
- Consider team expertise and learning curve

Generate a complete technology stack with implementation roadmap.
"""

        return await self.execute(tech_stack_prompt, context)

    async def define_interfaces(
        self,
        architecture: Dict[str, Any],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Define component interfaces and APIs.
        """

        interfaces_prompt = f"""
Define comprehensive interfaces and APIs for this architecture:
{architecture}

Project context: {context.__dict__ if context else 'None'}

Create interface definitions:

1. INTERFACE_ANALYSIS: Analyze component interaction requirements
2. API_DESIGN: Design internal API interfaces
3. DATA_CONTRACTS: Define data models and contracts
4. SERVICE_INTERFACES: Define service layer interfaces
5. REPOSITORY_INTERFACES: Define data access interfaces
6. EXTERNAL_APIS: Define external system integration interfaces
7. EVENT_INTERFACES: Define event and messaging interfaces
8. PLUGIN_INTERFACES: Define plugin and extension interfaces
9. TESTING_INTERFACES: Define testing abstractions and mocks
10. DOCUMENTATION: Create comprehensive interface documentation

For each interface:
- Define clear contracts and responsibilities
- Specify input/output parameters and types
- Include error handling and validation
- Consider versioning and evolution
- Provide usage examples and guidelines

Generate complete interface definitions with Dart code.
"""

        return await self.execute(interfaces_prompt, context)

    async def create_technical_specification(
        self,
        architecture: Dict[str, Any],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Create detailed technical specification.
        """

        spec_prompt = f"""
Create a comprehensive technical specification for this architecture:
{architecture}

Project context: {context.__dict__ if context else 'None'}

Generate detailed technical specification:

1. SYSTEM_OVERVIEW: High-level system description and goals
2. ARCHITECTURE_DETAILS: Detailed architectural design and patterns
3. COMPONENT_SPECIFICATIONS: Detailed component specifications
4. DATA_MODEL: Complete data model and schema definitions
5. API_SPECIFICATIONS: Detailed API specifications and contracts
6. SECURITY_SPECIFICATIONS: Security requirements and implementations
7. PERFORMANCE_SPECIFICATIONS: Performance requirements and benchmarks
8. DEPLOYMENT_SPECIFICATIONS: Deployment and infrastructure requirements
9. TESTING_SPECIFICATIONS: Testing strategy and requirements
10. MAINTENANCE_SPECIFICATIONS: Maintenance and support requirements

Include:
- Detailed technical diagrams and flows
- Implementation guidelines and best practices
- Code examples and templates
- Configuration and setup instructions
- Troubleshooting and debugging guides

Create production-ready technical documentation.
"""

        return await self.execute(spec_prompt, context)

    async def review_architecture(
        self,
        architecture: Dict[str, Any],
        review_criteria: List[str],
        context: Optional[TaskContext] = None
    ) -> ExecutionResult:
        """
        Review and validate architecture.
        """

        review_prompt = f"""
Review this Flutter architecture against these criteria:
{review_criteria}

Architecture to review:
{architecture}

Project context: {context.__dict__ if context else 'None'}

Provide comprehensive architectural review:

1. REVIEW_SUMMARY: Overall architecture assessment
2. STRENGTHS: Identify architectural strengths and benefits
3. WEAKNESSES: Identify potential issues and concerns
4. SCALABILITY_REVIEW: Assess scalability and performance implications
5. MAINTAINABILITY_REVIEW: Assess maintainability and evolution capabilities
6. SECURITY_REVIEW: Assess security architecture and potential vulnerabilities
7. TESTABILITY_REVIEW: Assess testing strategy and testability
8. RISK_ASSESSMENT: Identify architectural risks and mitigation strategies
9. RECOMMENDATIONS: Provide specific improvement recommendations
10. ACTION_ITEMS: Prioritized action items for architecture improvement

For each review area:
- Provide specific examples and evidence
- Compare against Flutter best practices
- Consider industry standards and patterns
- Assess alignment with project requirements
- Provide actionable recommendations

Generate a thorough architecture review report.
"""

        return await self.execute(review_prompt, context)

    # Helper methods
    def _extract_architecture_files_from_response(self, response: str) -> List[Dict[str, str]]:
        """Extract architecture files from LLM response"""
        files = []

        lines = response.split('\n')
        current_file = None
        current_content = []

        for line in lines:
            if line.strip().startswith('ARCH_FILE:') or line.strip().startswith('doc/'):
                if current_file:
                    files.append({
                        'path': current_file,
                        'content': '\n'.join(current_content)
                    })

                current_file = line.split(':', 1)[1].strip() if ':' in line else line.strip()
                current_content = []
            elif current_file and line.strip():
                current_content.append(line)

        if current_file:
            files.append({
                'path': current_file,
                'content': '\n'.join(current_content)
            })

        return files
