"""
Common collaboration and workflow patterns for AgentSwarm implementations.
"""

from typing import Dict, Any, List
import asyncio
from .types import CollaborationPattern, WorkflowPattern, TaskContext, ExecutionResult

class SequentialPattern(CollaborationPattern):
    """Execute agents sequentially, passing results between them"""

    async def execute(self, agents: List[Any], task: Dict[str, Any]) -> ExecutionResult:
        """Execute agents in sequence"""
        results = []
        current_context = task.get("context", {})

        for agent in agents:
            # Update task context with previous results
            task_copy = task.copy()
            task_copy["context"] = current_context

            result = await agent.execute(task_copy)
            results.append(result)

            # Update context with successful results
            if result.success:
                current_context.update(result.output)

        # Combine all results
        return ExecutionResult(
            success=all(r.success for r in results),
            agent_name="sequential_pattern",
            task_id=f"sequential_{task.get('id', 'unknown')}",
            output={"results": results, "final_context": current_context},
            execution_time=sum(r.execution_time for r in results)
        )

class ParallelPattern(CollaborationPattern):
    """Execute agents in parallel"""

    async def execute(self, agents: List[Any], task: Dict[str, Any]) -> ExecutionResult:
        """Execute agents in parallel"""

        # Create tasks for all agents
        tasks = [agent.execute(task) for agent in agents]

        # Execute in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        execution_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                execution_results.append(ExecutionResult(
                    success=False,
                    agent_name=agents[i].name,
                    task_id=f"parallel_{task.get('id', 'unknown')}_{i}",
                    error_message=str(result)
                ))
            else:
                execution_results.append(result)

        return ExecutionResult(
            success=all(r.success for r in execution_results),
            agent_name="parallel_pattern",
            task_id=f"parallel_{task.get('id', 'unknown')}",
            output={"results": execution_results},
            execution_time=max(r.execution_time for r in execution_results) if execution_results else 0
        )

class ReviewPattern(CollaborationPattern):
    """Execute primary agent, then review agent, then apply feedback"""

    async def execute(self, agents: List[Any], task: Dict[str, Any]) -> ExecutionResult:
        """Execute with review cycle"""

        if len(agents) < 2:
            raise ValueError("ReviewPattern requires at least 2 agents")

        primary_agent = agents[0]
        review_agent = agents[1]

        # Primary execution
        primary_result = await primary_agent.execute(task)

        if not primary_result.success:
            return primary_result

        # Review task
        review_task = {
            "description": f"Review and provide feedback on: {task.get('description', '')}",
            "context": {
                "original_task": task,
                "primary_result": primary_result.output,
                "review_criteria": task.get("review_criteria", [])
            }
        }

        review_result = await review_agent.execute(review_task)

        # Apply feedback if review suggests improvements
        if review_result.success and review_result.output.get("needs_improvement"):
            improvement_task = {
                "description": f"Improve based on feedback: {review_result.output.get('feedback', '')}",
                "context": {
                    "original_task": task,
                    "primary_result": primary_result.output,
                    "review_feedback": review_result.output
                }
            }

            final_result = await primary_agent.execute(improvement_task)

            return ExecutionResult(
                success=final_result.success,
                agent_name="review_pattern",
                task_id=f"review_{task.get('id', 'unknown')}",
                output={
                    "primary_result": primary_result.output,
                    "review_result": review_result.output,
                    "final_result": final_result.output
                },
                execution_time=primary_result.execution_time + review_result.execution_time + final_result.execution_time
            )

        return ExecutionResult(
            success=True,
            agent_name="review_pattern",
            task_id=f"review_{task.get('id', 'unknown')}",
            output={
                "primary_result": primary_result.output,
                "review_result": review_result.output,
                "review_approved": True
            },
            execution_time=primary_result.execution_time + review_result.execution_time
        )

class DevelopmentWorkflow(WorkflowPattern):
    """Standard development workflow: analyze -> implement -> test -> review"""

    def __init__(self, architect_agent, developer_agent, tester_agent, reviewer_agent):
        self.architect = architect_agent
        self.developer = developer_agent
        self.tester = tester_agent
        self.reviewer = reviewer_agent

    async def run(self, context: TaskContext) -> List[ExecutionResult]:
        """Run the development workflow"""

        results = []

        # 1. Architecture phase
        arch_task = {
            "description": f"Analyze requirements and design architecture for: {context.requirements}",
            "context": context.__dict__
        }

        arch_result = await self.architect.execute(arch_task)
        results.append(arch_result)

        if not arch_result.success:
            return results

        # 2. Development phase
        dev_task = {
            "description": "Implement the designed architecture",
            "context": {
                **context.__dict__,
                "architecture": arch_result.output
            }
        }

        dev_result = await self.developer.execute(dev_task)
        results.append(dev_result)

        if not dev_result.success:
            return results

        # 3. Testing phase
        test_task = {
            "description": "Create and run tests for the implementation",
            "context": {
                **context.__dict__,
                "architecture": arch_result.output,
                "implementation": dev_result.output
            }
        }

        test_result = await self.tester.execute(test_task)
        results.append(test_result)

        # 4. Review phase
        review_task = {
            "description": "Review the complete implementation",
            "context": {
                **context.__dict__,
                "architecture": arch_result.output,
                "implementation": dev_result.output,
                "test_results": test_result.output
            }
        }

        review_result = await self.reviewer.execute(review_task)
        results.append(review_result)

        return results
