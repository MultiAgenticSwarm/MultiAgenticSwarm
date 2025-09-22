"""
Graph Builder: Builds dynamic workflow graphs from parsed collaboration prompts.

Enhanced version with:
- Advanced pattern support (fan-in, fan-out, pipeline)
- Robust error handling and validation
- State management utilities
- Conditional routing logic
- Graph optimization
- Comprehensive logging
"""

import time
from typing import Dict, Any, List, Optional, Tuple, Callable, Set, Union
from dataclasses import dataclass, field
from enum import Enum
from copy import deepcopy
import uuid
from multiagenticswarm.utils.logger import get_logger
# Try importing StateGraph if available (LangGraph runtime)
try:
    from langgraph.graph import StateGraph
    from langgraph.checkpoint.memory import MemorySaver
except ImportError:
    StateGraph = None
    MemorySaver = None

logger = get_logger(__name__)

GraphSpec = Dict[str, Any]


class NodeType(Enum):
    """Enumeration of supported node types."""
    AGENT = "agent"
    ROUTER = "router"
    AGGREGATOR = "aggregator"
    SPLITTER = "splitter"
    MERGER = "merger"
    CONDITION = "condition"
    LOOP_CONTROL = "loop_control"
    BARRIER = "barrier"  # Synchronization point
    END = "end"
    START = "start"  # Entry point node


class PatternType(Enum):
    """Enumeration of supported workflow patterns."""
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    CONDITIONAL = "conditional"
    LOOP = "loop"
    FAN_OUT = "fan_out"
    FAN_IN = "fan_in"
    PIPELINE = "pipeline"
    MAP_REDUCE = "map_reduce"


@dataclass
class NodeInfo:
    """Information about a graph node."""
    node_type: NodeType
    name: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)
    retry_config: Optional[Dict[str, Any]] = None


@dataclass
class EdgeInfo:
    """Information about a graph edge."""
    from_node: str
    to_node: str
    condition: Optional[str] = None
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Result of graph validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


class GraphBuilder:
    def clean_spec_edges(self, spec: GraphSpec) -> None:
        """Remove 'metadata' from all edge dicts in the graph spec."""
        for edge in spec.get("edges", []):
            if "metadata" in edge:
                del edge["metadata"]
    """Enhanced workflow graph builder with advanced patterns and validation."""

    def __init__(self, 
                 executor_registry: Optional[Dict[str, Callable]] = None,
                 default_checkpointer: bool = True,
                 enable_optimization: bool = True):
        """
        Initialize the GraphBuilder.
        
        Args:
            executor_registry: mapping of agent_name -> callable executor
            default_checkpointer: whether to use memory checkpointer by default
            enable_optimization: whether to enable graph optimizations
        """
        self.executor_registry = executor_registry or {}
        self.default_checkpointer = default_checkpointer
        self.enable_optimization = enable_optimization
        self._pattern_handlers = self._init_pattern_handlers()
        
    def _init_pattern_handlers(self) -> Dict[PatternType, Callable]:
        """Initialize pattern-specific handlers."""
        return {
            PatternType.PARALLEL: self._add_parallel_phase,
            PatternType.SEQUENTIAL: self._add_sequential_phase,
            PatternType.CONDITIONAL: self._add_conditional_phase,
            PatternType.LOOP: self._add_loop_phase,
            PatternType.FAN_OUT: self._add_fan_out_phase,
            PatternType.FAN_IN: self._add_fan_in_phase,
            PatternType.PIPELINE: self._add_pipeline_phase,
            PatternType.MAP_REDUCE: self._add_map_reduce_phase,
        }

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    def build_spec(self, parsed_prompt: Dict[str, Any]) -> GraphSpec:
        """
        Build a GraphSpec from parsed JSON-like structure.
        Supports all workflow patterns with enhanced validation.
        """
        try:
            logger.info(f"Building graph spec from parsed prompt with {len(parsed_prompt.get('phases', []))} phases")
            spec = self._init_spec(parsed_prompt)
            prev_node = spec["entry"]

            # Process phases
            for idx, phase in enumerate(parsed_prompt.get("phases", [])):
                pattern_str = phase.get("pattern", "sequential")
                try:
                    pattern = PatternType(pattern_str)
                except ValueError:
                    logger.error(f"Unsupported pattern: {pattern_str}")
                    raise ValueError(f"Unsupported pattern: {pattern_str}")
                agents = phase.get("agents", [])
                if not agents:
                    logger.warning(f"Phase {idx} has no agents")
                    continue
                handler = self._pattern_handlers[pattern]
                prev_node = handler(spec, agents, prev_node, idx, phase)
                logger.debug(f"Added phase {idx} with pattern {pattern_str}, next node: {prev_node}")

            # Apply rules and dependencies
            self._apply_rules(spec, parsed_prompt.get("rules", []))
            self._apply_dependencies(spec, parsed_prompt.get("dependencies", {}))

            # Ensure END node exists
            if "END" not in spec["nodes"]:
                spec["nodes"]["END"] = {
                    "type": NodeType.END.value,   # use enum instead of "terminal"
                    "meta": {"role": "Workflow complete"}
                }


            # Connect all dead-end nodes to END
            nodes = set(spec["nodes"].keys())
            outgoing = {edge["from"] for edge in spec["edges"]}
            dead_ends = nodes - outgoing
            for node in dead_ends:
                if node != "END":
                    spec["edges"].append({"from": node, "to": "END", "condition": None})

            # Apply optimizations if enabled
            if self.enable_optimization:
                spec = self._optimize_spec(spec)

            self.clean_spec_edges(spec)
            logger.info(f"Successfully built graph spec with {len(spec['nodes'])} nodes and {len(spec['edges'])} edges")
            return spec
        except Exception as e:
            logger.error(f"Failed to build graph spec: {e}")
            raise

    def validate_spec(self, spec: GraphSpec) -> ValidationResult:
        """
        Comprehensive validation of GraphSpec structure.
        """
        try:
            result = ValidationResult(is_valid=True)
            
            # Basic structure validation
            if not isinstance(spec, dict):
                result.errors.append("Spec must be a dictionary")
                result.is_valid = False
                return result
            
            required_keys = ["nodes", "edges", "entry"]
            for key in required_keys:
                if key not in spec:
                    result.errors.append(f"Missing required key: {key}")
                    result.is_valid = False
            
            if not result.is_valid:
                return result
            
            # Validate entry point
            entry = spec["entry"]
            if entry not in spec["nodes"]:
                result.errors.append(f"Entry node '{entry}' not found in nodes")
                result.is_valid = False
            
            # Validate nodes
            node_names = set(spec["nodes"].keys())
            for node_name, node_info in spec["nodes"].items():
                if not isinstance(node_info, dict):
                    result.errors.append(f"Node '{node_name}' info must be a dictionary")
                    continue
                
                if "type" not in node_info:
                    result.errors.append(f"Node '{node_name}' missing type")
                    continue
                
                try:
                    NodeType(node_info["type"])
                except ValueError:
                    result.warnings.append(f"Unknown node type '{node_info['type']}' for node '{node_name}'")
            
            # Validate edges
            for i, edge in enumerate(spec["edges"]):
                if not isinstance(edge, dict):
                    result.errors.append(f"Edge {i} must be a dictionary")
                    continue
                
                required_edge_keys = ["from", "to"]
                for key in required_edge_keys:
                    if key not in edge:
                        result.errors.append(f"Edge {i} missing required key: {key}")
                        continue
                
                from_node = edge["from"]
                to_node = edge["to"]
                
                if from_node not in node_names:
                    result.errors.append(f"Edge {i}: from node '{from_node}' not found")
                if to_node not in node_names:
                    result.errors.append(f"Edge {i}: to node '{to_node}' not found")
            
            # Advanced validations
            self._validate_connectivity(spec, result)
            self._validate_cycles(spec, result)
            self._validate_patterns(spec, result)
            
            result.is_valid = len(result.errors) == 0
            
            logger.info(f"Validation complete: valid={result.is_valid}, "
                       f"errors={len(result.errors)}, warnings={len(result.warnings)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Validation exception: {e}"]
            )

    def materialize(self, spec: GraphSpec, checkpointer: Optional[Any] = None) -> Any:
            """
            Turn GraphSpec into a LangGraph StateGraph with enhanced features.
            Adds fail-fast assertions and debug prints to catch dicts/non-hashable types.
            """
            if StateGraph is None:
                raise ImportError("LangGraph not available. Cannot materialize graph.")

            # Debug print: full spec before materialization
            logger.info(f"Full graph spec before materialization: {spec}")

            # Fail-fast: check node names
            for node_name in spec.get("nodes", {}).keys():
                if not isinstance(node_name, str):
                    logger.error(f"FAIL-FAST: Node name is not a string: {node_name} (type: {type(node_name)})")
                    raise TypeError(f"FAIL-FAST: Node name must be a string, got {type(node_name)}: {node_name}")
                if isinstance(node_name, dict):
                    logger.error(f"FAIL-FAST: Node name is a dict: {node_name}")
                    raise TypeError(f"FAIL-FAST: Node name cannot be a dict: {node_name}")

            # Fail-fast: check edge targets
            for edge in spec.get("edges", []):
                from_node = edge.get("from")
                to_node = edge.get("to")
                if not isinstance(from_node, str):
                    logger.error(f"FAIL-FAST: Edge 'from' node is not a string: {from_node} (type: {type(from_node)})")
                    raise TypeError(f"FAIL-FAST: Edge 'from' node must be a string, got {type(from_node)}: {from_node}")
                if not isinstance(to_node, str):
                    logger.error(f"FAIL-FAST: Edge 'to' node is not a string: {to_node} (type: {type(to_node)})")
                    raise TypeError(f"FAIL-FAST: Edge 'to' node must be a string, got {type(to_node)}: {to_node}")
                if isinstance(from_node, dict) or isinstance(to_node, dict):
                    logger.error(f"FAIL-FAST: Edge 'from' or 'to' node is a dict: from={from_node}, to={to_node}")
                    raise TypeError(f"FAIL-FAST: Edge 'from' or 'to' node cannot be a dict: from={from_node}, to={to_node}")

            # Fail-fast: check executors
            for node_name, node_info in spec.get("nodes", {}).items():
                executor = self._create_enhanced_executor(node_name, node_info, spec)
                if not callable(executor):
                    logger.error(f"FAIL-FAST: Executor for node {node_name} is not callable: {executor} (type: {type(executor)})")
                    raise TypeError(f"FAIL-FAST: Executor for node {node_name} must be callable, got {type(executor)}: {executor}")
                if isinstance(executor, dict):
                    logger.error(f"FAIL-FAST: Executor for node {node_name} is a dict: {executor}")
                    raise TypeError(f"FAIL-FAST: Executor for node {node_name} cannot be a dict: {executor}")

            try:
                logger.info("Materializing graph spec to LangGraph StateGraph")

                # Validate before materialization
                validation = self.validate_spec(spec)
                if not validation.is_valid:
                    raise ValueError(f"Cannot materialize invalid spec. Errors: {validation.errors}")

                # Create state schema (enhanced for multi-agent use)
                state_schema = self._create_state_schema(spec)
                graph = StateGraph(state_schema)

                # Debug print: all node names and their types
                logger.info(f"Node names and types before adding to LangGraph:")
                for node_name in spec["nodes"].keys():
                    logger.info(f"  node_name={node_name} type={type(node_name)}")

                # Add nodes with enhanced executors
                for node_name, node_info in spec["nodes"].items():
                    executor = self._create_enhanced_executor(node_name, node_info, spec)
                    logger.info(f"Adding node to LangGraph: name={node_name} (type: {type(node_name)}), executor={executor} (type: {type(executor)})")
                    graph.add_node(node_name, executor)

                # Add edges with conditional logic
                self._add_edges_to_graph(graph, spec)

                # Set entry point
                graph.set_entry_point(spec["entry"])

                # Add checkpointer if specified
                if checkpointer is None and self.default_checkpointer and MemorySaver:
                    checkpointer = MemorySaver()

                # Compile the graph
                compiled_graph = graph.compile(checkpointer=checkpointer)

                logger.info("Successfully materialized graph")
                return compiled_graph

            except Exception as e:
                logger.error(f"Failed to materialize graph: {e}")
                raise

    def get_execution_plan(self, spec: GraphSpec) -> List[Dict[str, Any]]:
        """
        Generate an execution plan from the graph spec.
        Useful for debugging and visualization.
        """
        try:
            plan = []
            visited = set()
            
            def traverse(node_name: str, depth: int = 0):
                if node_name in visited:
                    return
                
                visited.add(node_name)
                node_info = spec["nodes"].get(node_name, {})
                
                plan.append({
                    "step": len(plan) + 1,
                    "node": node_name,
                    "type": node_info.get("type", "unknown"),
                    "depth": depth,
                    "metadata": node_info.get("meta", {})
                })
                
                # Find next nodes
                next_nodes = [edge["to"] for edge in spec["edges"] 
                             if edge["from"] == node_name]
                
                for next_node in next_nodes:
                    traverse(next_node, depth + 1)
            
            traverse(spec["entry"])
            return plan
            
        except Exception as e:
            logger.error(f"Failed to generate execution plan: {e}")
            return []

    # ---------------------------------------------------------------------
    # Enhanced Pattern Handlers
    # ---------------------------------------------------------------------

    def _add_parallel_phase(self, spec: GraphSpec, agents: List[str], 
                          prev_node: str, phase_idx: int, phase: Dict[str, Any]) -> str:
        """Enhanced parallel processing with barrier synchronization."""
        router = f"router_parallel_{phase_idx}"
        spec["nodes"][router] = {
            "type": NodeType.ROUTER.value, 
            "meta": {"pattern": "parallel", "phase": phase_idx}
        }
        spec["edges"].append({"from": prev_node, "to": router, "condition": None})

        # Add all agents
        for agent in agents:
            self._add_agent_node(spec, agent, phase.get("roles", {}).get(agent))
            spec["edges"].append({"from": router, "to": agent, "condition": None})

        # Add barrier for synchronization
        barrier = f"barrier_parallel_{phase_idx}"
        spec["nodes"][barrier] = {
            "type": NodeType.BARRIER.value,
            "meta": {"agents": agents, "sync_type": "all"}
        }
        
        for agent in agents:
            spec["edges"].append({"from": agent, "to": barrier, "condition": None})

        return barrier

    def _add_sequential_phase(self, spec: GraphSpec, agents: List[str],
                          prev_node: str, phase_idx: int, phase: Dict[str, Any]) -> str:
        """Enhanced sequential processing starting with Start node instead of router."""

        # ✅ Create Start node for first phase
        if phase_idx == 0:
            print("Adding Start node for first phase")
            start_node = "Start"
            if start_node not in spec["nodes"]:
                spec["nodes"][start_node] = {
                    "type": NodeType.START.value,
                    "meta": {"role": "workflow entry"}
                }

            # connect Start → first agent directly
            prev = start_node
        else:
            # for later phases, still create router
            router = f"router_sequential_{phase_idx}"
            if router not in spec["nodes"]:
                spec["nodes"][router] = {
                    "type": NodeType.ROUTER.value,
                    "meta": {"pattern": "sequential", "phase": phase_idx}
                }
            if prev_node and prev_node != router:
                spec["edges"].append({"from": prev_node, "to": router, "condition": None})
            prev = router

        # ✅ Loop through agents in the phase
        for i, agent in enumerate(agents):
            # add agent node
            self._add_agent_node(spec, agent, phase.get("roles", {}).get(agent))

            # retry config
            retry_config = phase.get("retry", {}).get(agent)
            if retry_config:
                spec["nodes"][agent]["meta"]["retry"] = retry_config

            # connect prev → agent
            spec["edges"].append({"from": prev, "to": agent, "condition": None})
            prev = agent

        return prev




    def _add_conditional_phase(self, spec: GraphSpec, agents: List[str], 
                             prev_node: str, phase_idx: int, phase: Dict[str, Any]) -> str:
        """Enhanced conditional branching with complex conditions."""
        router = f"router_conditional_{phase_idx}"
        spec["nodes"][router] = {
            "type": NodeType.CONDITION.value, 
            "meta": {
                "pattern": "conditional",
                "decision_logic": phase.get("decision_logic", "first_match")
            }
        }
        spec["edges"].append({"from": prev_node, "to": router, "condition": None})
        
        conditions = phase.get("conditions", [])
        default_agent = phase.get("default_agent")
        
        for i, agent in enumerate(agents):
            self._add_agent_node(spec, agent)
            condition = conditions[i] if i < len(conditions) else None
            spec["edges"].append({
                "from": router, 
                "to": agent, 
                "condition": condition,
                "metadata": {"priority": i}
            })
        
        # Add default path if specified
        if default_agent and default_agent in agents:
            spec["edges"].append({
                "from": router, 
                "to": default_agent, 
                "condition": "default"
            })
        
        # Merge results
        merger = f"merger_conditional_{phase_idx}"
        spec["nodes"][merger] = {
            "type": NodeType.MERGER.value,
            "meta": {"agents": agents, "merge_strategy": phase.get("merge_strategy", "first")}
        }
        
        for agent in agents:
            spec["edges"].append({"from": agent, "to": merger, "condition": None})
        
        return merger

    def _add_loop_phase(self, spec: GraphSpec, agents: List[str], 
                       prev_node: str, phase_idx: int, phase: Dict[str, Any]) -> str:
        """Enhanced loop with termination conditions and iteration limits."""
        loop_control = f"loop_control_{phase_idx}"
        spec["nodes"][loop_control] = {
            "type": NodeType.LOOP_CONTROL.value,
            "meta": {
                "max_iterations": phase.get("max_iterations", 10),
                "termination_conditions": phase.get("termination_conditions", []),
                "iteration_count": 0
            }
        }
        spec["edges"].append({"from": prev_node, "to": loop_control, "condition": None})
        
        # Create loop body
        loop_body = f"loop_body_{phase_idx}"
        if len(agents) == 1:
            loop_body = agents[0]
            self._add_agent_node(spec, agents[0])
        else:
            # Multiple agents in loop - use parallel execution
            loop_body = self._add_parallel_phase(spec, agents, loop_control, 
                                               f"{phase_idx}_loop_body", phase)
        
        # Add loop edges
        spec["edges"].append({
            "from": loop_control, 
            "to": loop_body, 
            "condition": "continue_loop"
        })
        spec["edges"].append({
            "from": loop_body, 
            "to": loop_control, 
            "condition": None
        })
        
        return loop_control

    def _add_fan_out_phase(self, spec: GraphSpec, agents: List[str], 
                          prev_node: str, phase_idx: int, phase: Dict[str, Any]) -> str:
        """Fan-out pattern: split data/tasks across multiple agents."""
        splitter = f"splitter_{phase_idx}"
        spec["nodes"][splitter] = {
            "type": NodeType.SPLITTER.value,
            "meta": {
                "split_strategy": phase.get("split_strategy", "round_robin"),
                "target_agents": agents
            }
        }
        spec["edges"].append({"from": prev_node, "to": splitter, "condition": None})
        
        for agent in agents:
            self._add_agent_node(spec, agent)
            spec["edges"].append({"from": splitter, "to": agent, "condition": None})
        
        return agents[-1]  # Return last agent as continuation point

    def _add_fan_in_phase(self, spec: GraphSpec, agents: List[str], 
                         prev_node: str, phase_idx: int, phase: Dict[str, Any]) -> str:
        """Fan-in pattern: collect results from multiple sources."""
        # Assume prev_node represents multiple sources
        aggregator = f"aggregator_fan_in_{phase_idx}"
        spec["nodes"][aggregator] = {
            "type": NodeType.AGGREGATOR.value,
            "meta": {
                "aggregation_strategy": phase.get("aggregation_strategy", "merge_all"),
                "source_agents": agents
            }
        }
        
        for agent in agents:
            if agent in spec["nodes"]:
                spec["edges"].append({"from": agent, "to": aggregator, "condition": None})
        
        return aggregator

    def _add_pipeline_phase(self, spec: GraphSpec, agents: List[str], 
                           prev_node: str, phase_idx: int, phase: Dict[str, Any]) -> str:
        """Pipeline pattern: sequential processing with data transformation."""
        prev = prev_node
        transformations = phase.get("transformations", {})
        
        for i, agent in enumerate(agents):
            self._add_agent_node(spec, agent)
            
            # Add transformation metadata
            transform = transformations.get(agent, {})
            if transform:
                spec["nodes"][agent]["meta"]["transformation"] = transform
            
            spec["edges"].append({"from": prev, "to": agent, "condition": None})
            prev = agent
        
        return prev

    def _add_map_reduce_phase(self, spec: GraphSpec, agents: List[str], 
                             prev_node: str, phase_idx: int, phase: Dict[str, Any]) -> str:
        """Map-Reduce pattern: parallel processing followed by aggregation."""
        # Map phase
        map_node = self._add_parallel_phase(spec, agents, prev_node, 
                                          f"{phase_idx}_map", phase)
        
        # Reduce phase
        reduce_agents = phase.get("reduce_agents", ["reducer"])
        reduce_node = self._add_sequential_phase(spec, reduce_agents, map_node, 
                                               f"{phase_idx}_reduce", phase)
        
        return reduce_node

    # ---------------------------------------------------------------------
    # Enhanced Validation Methods
    # ---------------------------------------------------------------------

    def _validate_connectivity(self, spec: GraphSpec, result: ValidationResult):
        """Validate graph connectivity."""
        nodes = set(spec["nodes"].keys())
        
        # Check for unreachable nodes
        reachable = set()
        stack = [spec["entry"]]
        
        while stack:
            current = stack.pop()
            if current in reachable:
                continue
            reachable.add(current)
            
            next_nodes = [edge["to"] for edge in spec["edges"] 
                         if edge["from"] == current]
            stack.extend(next_nodes)
        
        unreachable = nodes - reachable
        if unreachable:
            result.warnings.extend([f"Unreachable node: {node}" for node in unreachable])
        
        # Check for dead ends (nodes with no outgoing edges)
        outgoing = {edge["from"] for edge in spec["edges"]}
        dead_ends = nodes - outgoing
        if dead_ends and len(dead_ends) > 1:  # Allow one final node
            result.suggestions.extend([f"Dead end node: {node}" for node in dead_ends])

    def _validate_cycles(self, spec: GraphSpec, result: ValidationResult):
        """Detect cycles in the graph."""
        visited = set()
        rec_stack = set()
        
        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)
            
            next_nodes = [edge["to"] for edge in spec["edges"] 
                         if edge["from"] == node]
            
            for next_node in next_nodes:
                if next_node not in visited:
                    if has_cycle(next_node):
                        return True
                elif next_node in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in spec["nodes"]:
            if node not in visited:
                if has_cycle(node):
                    result.warnings.append(f"Cycle detected involving node: {node}")

    def _validate_patterns(self, spec: GraphSpec, result: ValidationResult):
        """Validate pattern-specific constraints."""
        # Check for proper aggregator/barrier usage
        for node_name, node_info in spec["nodes"].items():
            node_type = node_info.get("type")
            
            if node_type == NodeType.AGGREGATOR.value:
                expected_agents = node_info.get("meta", {}).get("agents", [])
                incoming = [edge["from"] for edge in spec["edges"] 
                           if edge["to"] == node_name]
                
                if len(incoming) < len(expected_agents):
                    result.warnings.append(
                        f"Aggregator {node_name} expects {len(expected_agents)} "
                        f"inputs but has {len(incoming)}"
                    )

    # ---------------------------------------------------------------------
    # Enhanced Helper Methods
    # ---------------------------------------------------------------------

    def _init_spec(self, parsed: Dict[str, Any]) -> GraphSpec:
        """Initialize spec with Start as the entry node."""
        spec: GraphSpec = {
            "nodes": {}, 
            "edges": [], 
            "entry": "Start",
            "meta": {
                "created_at": uuid.uuid4().hex,
                "source": parsed.get("source", "unknown"),
                "version": "2.0",
                "patterns": []
            }
        }

        # Add Start node as the entry
        spec["nodes"]["Start"] = {
            "type": NodeType.START.value,
            "meta": {"role": "workflow entry"}
        }

        return spec


    def _add_agent_node(self, spec: GraphSpec, agent_name: str, 
                       role: Optional[str] = None, **kwargs):
        """Add an agent node with enhanced metadata."""
        if agent_name not in spec["nodes"]:
            spec["nodes"][agent_name] = {
                "type": NodeType.AGENT.value,
                "meta": {
                    "role": role,
                    "agent_id": agent_name,
                    **kwargs
                }
            }

    def _optimize_spec(self, spec: GraphSpec) -> GraphSpec:
        """Apply graph optimizations."""
        try:
            logger.debug("Applying graph optimizations")
            optimized_spec = deepcopy(spec)
            
            # Remove redundant nodes
            self._remove_redundant_routers(optimized_spec)
            
            # Merge sequential single-path segments
            self._merge_sequential_paths(optimized_spec)
            
            logger.debug("Graph optimizations completed")
            return optimized_spec
            
        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            return spec  # Return original if optimization fails

    def _remove_redundant_routers(self, spec: GraphSpec):
        """Remove routers that just pass through to a single node."""
        to_remove = []
        
        for node_name, node_info in spec["nodes"].items():
            if node_info.get("type") == NodeType.ROUTER.value:
                outgoing = [edge for edge in spec["edges"] if edge["from"] == node_name]
                
                # If router has only one outgoing edge with no condition
                if len(outgoing) == 1 and not outgoing[0].get("condition"):
                    # Redirect incoming edges to target
                    incoming = [edge for edge in spec["edges"] if edge["to"] == node_name]
                    target = outgoing[0]["to"]
                    
                    # Update edges
                    for edge in incoming:
                        edge["to"] = target
                    
                    # Mark for removal
                    to_remove.append((node_name, outgoing[0]))
        
        # Remove redundant nodes and edges
        for node_name, edge in to_remove:
            if node_name in spec["nodes"]:
                del spec["nodes"][node_name]
            if edge in spec["edges"]:
                spec["edges"].remove(edge)

    def _merge_sequential_paths(self, spec: GraphSpec):
        """Merge simple sequential paths where possible."""
        # This is a complex optimization - implement based on specific needs
        pass

    def _create_state_schema(self, spec: GraphSpec):
        """Create an appropriate state schema for the graph as a TypedDict."""
        from typing import TypedDict, List, Dict, Any, Optional
        class StateSchema(TypedDict, total=False):
            messages: List[Any]
            current_agent: str
            agent_outputs: Dict[str, Any]
            iteration_count: int
            metadata: Dict[str, Any]
            errors: List[Any]
            status: str
        return StateSchema

    def _create_enhanced_executor(self, node_name: str, node_info: Dict[str, Any], 
                                spec: GraphSpec) -> Callable:
        """Create enhanced executors with error handling and retry logic."""
        node_type = node_info.get("type")
        meta = node_info.get("meta", {})
        
        # Get custom executor from registry
        if node_name in self.executor_registry:
            base_executor = self.executor_registry[node_name]
        else:
            base_executor = self._get_default_executor(node_type, node_name, meta)
        
        # Wrap with enhancement
        def enhanced_executor(state: Dict[str, Any]) -> Dict[str, Any]:
            try:
                logger.debug(f"Executing node: {node_name} (type: {node_type})")
                
                # Add node context to state
                state = state.copy()
                state["current_agent"] = node_name
                state["metadata"] = state.get("metadata", {})
                state["metadata"]["current_node"] = {
                    "name": node_name,
                    "type": node_type,
                    "meta": meta
                }
                
                # Execute with retry if configured
                retry_config = meta.get("retry", {})
                if retry_config:
                    return self._execute_with_retry(base_executor, state, retry_config)
                else:
                    return base_executor(state)
                    
            except Exception as e:
                logger.error(f"Execution failed for node {node_name}: {e}")
                state["errors"] = state.get("errors", [])
                state["errors"].append({
                    "node": node_name,
                    "error": str(e),
                    "type": type(e).__name__
                })
                state["status"] = "error"
                return state
        
        return enhanced_executor

    def _execute_with_retry(self, executor: Callable, state: Dict[str, Any], 
                          retry_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute with retry logic."""
        max_retries = retry_config.get("max_retries", 3)
        delay = retry_config.get("delay", 1)
        
        for attempt in range(max_retries + 1):
            try:
                return executor(state)
            except Exception as e:
                if attempt == max_retries:
                    raise
                logger.warning(f"Retry {attempt + 1}/{max_retries} failed: {e}")
                time.sleep(delay * (2 ** attempt))  # Exponential backoff
        
        return state

    def _get_default_executor(self, node_type: str, node_name: str, 
                            meta: Dict[str, Any]) -> Callable:
        """Get default executor based on node type."""
        if node_type == NodeType.AGENT.value:
            return self._default_agent_executor(node_name, meta)
        elif node_type == NodeType.ROUTER.value:
            return self._router_executor(node_name, meta)
        elif node_type == NodeType.AGGREGATOR.value:
            return self._aggregator_executor(node_name, meta)
        elif node_type == NodeType.BARRIER.value:
            return self._barrier_executor(node_name, meta)
        elif node_type == NodeType.CONDITION.value:
            return self._condition_executor(node_name, meta)
        else:
            return self._noop_executor(node_name)

    def _add_edges_to_graph(self, graph: Any, spec: GraphSpec):
        """Add edges to LangGraph with conditional logic and strict type checks."""
        edge_groups = {}
        # Debug print: all edge 'from' and 'to' values and their types
        logger.info("Edge 'from' and 'to' values before adding to LangGraph:")
        for edge in spec["edges"]:
            from_node = edge["from"]
            to_node = edge["to"]
            logger.info(f"  edge from={from_node} (type={type(from_node)}) to={to_node} (type={type(to_node)})")
            # Strict type checks
            if not isinstance(from_node, str):
                logger.error(f"Edge 'from' node is not a string: {from_node} (type: {type(from_node)})")
                raise TypeError(f"Edge 'from' node must be a string, got {type(from_node)}: {from_node}")
            if not isinstance(to_node, str):
                logger.error(f"Edge 'to' node is not a string: {to_node} (type: {type(to_node)})")
                raise TypeError(f"Edge 'to' node must be a string, got {type(to_node)}: {to_node}")
            edge_copy = {k: v for k, v in edge.items() if k in ["from", "to", "condition"]}
            edge_copy["from"] = from_node
            edge_copy["to"] = to_node
            if from_node not in edge_groups:
                edge_groups[from_node] = []
            edge_groups[from_node].append(edge_copy)

        for from_node, edges in edge_groups.items():
            if not isinstance(from_node, str):
                logger.error(f"Edge group 'from' node is not a string: {from_node} (type: {type(from_node)})")
                raise TypeError(f"Edge group 'from' node must be a string, got {type(from_node)}: {from_node}")
            for edge in edges:
                to_val = edge["to"]
                if not isinstance(to_val, str):
                    logger.error(f"Edge group 'to' node is not a string: {to_val} (type: {type(to_val)})")
                    raise TypeError(f"Edge group 'to' node must be a string, got {type(to_val)}: {to_val}")
                logger.info(f"Adding edge: from {from_node} to {to_val} (condition: {edge.get('condition')})")
            if len(edges) == 1 and not edges[0].get("condition"):
                graph.add_edge(from_node, edges[0]["to"])
            else:
                def create_router(edges_list):
                    def router_func(state: Dict[str, Any]) -> str:
                        for edge in edges_list:
                            condition = edge.get("condition")
                            to_val = edge["to"]
                            if not isinstance(to_val, str):
                                logger.error(f"Router target is not a string: {to_val} (type: {type(to_val)})")
                                raise TypeError(f"Router target must be a string, got {type(to_val)}: {to_val}")
                            if condition is None or self._evaluate_condition(condition, state):
                                return to_val
                        to_val = edges_list[0]["to"] if edges_list else from_node
                        if not isinstance(to_val, str):
                            logger.error(f"Router default target is not a string: {to_val} (type: {type(to_val)})")
                            raise TypeError(f"Router default target must be a string, got {type(to_val)}: {to_val}")
                        return to_val
                    return router_func

                targets = []
                for edge in edges:
                    to_val = edge["to"]
                    if not isinstance(to_val, str):
                        logger.error(f"Target for conditional edge is not a string: {to_val} (type: {type(to_val)})")
                        raise TypeError(f"Target for conditional edge must be a string, got {type(to_val)}: {to_val}")
                    targets.append(to_val)

                if hasattr(graph, 'add_conditional_edges'):
                    logger.info(f"Adding conditional edges from {from_node} to {targets}")
                    graph.add_conditional_edges(from_node, create_router(edges), targets)
                else:
                    for edge in edges:
                        graph.add_edge(from_node, edge["to"])

    def _evaluate_condition(self, condition: str, state: Dict[str, Any]) -> bool:
        """Evaluate a condition string against the current state."""
        try:
            if condition == "default":
                return True
            elif condition == "continue_loop":
                iteration_count = state.get("metadata", {}).get("iteration_count", 0)
                max_iterations = state.get("metadata", {}).get("max_iterations", 10)
                return iteration_count < max_iterations
            elif condition.startswith("state."):
                # Simple state-based conditions like "state.confidence > 0.8"
                # This is a simplified evaluator - extend as needed
                parts = condition.split(".")
                value = state
                for part in parts[1:]:  # Skip 'state'
                    if "[" in part and "]" in part:
                        # Handle array access like "agents[0]"
                        key, index = part.split("[")
                        index = int(index.rstrip("]"))
                        value = value.get(key, [])[index]
                    else:
                        value = value.get(part, None)
                
                # For now, return True if value exists
                return value is not None
            else:
                # Custom condition evaluation
                return self._custom_condition_evaluator(condition, state)
        except Exception as e:
            logger.warning(f"Condition evaluation failed for '{condition}': {e}")
            return False

    def _custom_condition_evaluator(self, condition: str, state: Dict[str, Any]) -> bool:
        """Override this method to implement custom condition logic."""
        # Default implementation - always true
        logger.debug(f"Using default condition evaluator for: {condition}")
        return True

    # ---------------------------------------------------------------------
    # Enhanced Executors
    # ---------------------------------------------------------------------

    def _default_agent_executor(self, agent_name: str, meta: Dict[str, Any]) -> Callable:
        """Default agent executor with enhanced capabilities."""
        def executor(state: Dict[str, Any]) -> Dict[str, Any]:
            logger.debug(f"[Agent:{agent_name}] Executing with role: {meta.get('role', 'unknown')}")
            
            # Initialize agent outputs if not present
            if "agent_outputs" not in state:
                state["agent_outputs"] = {}
            
            # Simulate agent processing
            result = {
                "agent": agent_name,
                "role": meta.get("role"),
                "status": "completed",
                "output": f"Output from {agent_name}",
                "timestamp": time.time()
            }
            
            state["agent_outputs"][agent_name] = result
            state["status"] = "running"
            
            # Apply any transformations if specified
            transformation = meta.get("transformation")
            if transformation:
                state = self._apply_transformation(state, transformation)
            
            return state
        
        return executor

    def _router_executor(self, name: str, meta: Dict[str, Any]) -> Callable:
        """Enhanced router executor with intelligent routing."""
        def executor(state: Dict[str, Any]) -> Dict[str, Any]:
            logger.debug(f"[Router:{name}] Routing with pattern: {meta.get('pattern', 'default')}")
            
            pattern = meta.get("pattern", "default")
            
            if pattern == "parallel":
                # Set up parallel execution context
                state["execution_mode"] = "parallel"
                state["parallel_tasks"] = meta.get("target_agents", [])
            elif pattern == "conditional":
                # Set up conditional routing context
                state["execution_mode"] = "conditional"
                state["decision_pending"] = True
            
            state["status"] = "routing"
            return state
        
        return executor

    def _aggregator_executor(self, name: str, meta: Dict[str, Any]) -> Callable:
        """Enhanced aggregator with multiple strategies."""
        def executor(state: Dict[str, Any]) -> Dict[str, Any]:
            agents = meta.get("agents", [])
            strategy = meta.get("aggregation_strategy", "merge_all")
            
            logger.debug(f"[Aggregator:{name}] Aggregating from {len(agents)} agents using {strategy}")
            
            agent_outputs = state.get("agent_outputs", {})
            
            if strategy == "merge_all":
                # Combine all outputs
                combined_output = {}
                for agent in agents:
                    if agent in agent_outputs:
                        combined_output[agent] = agent_outputs[agent]
                
                state["aggregated_result"] = combined_output
                
            elif strategy == "best_score":
                # Select output with highest score
                best_output = None
                best_score = -1
                
                for agent in agents:
                    if agent in agent_outputs:
                        output = agent_outputs[agent]
                        score = output.get("confidence", 0) if isinstance(output, dict) else 0
                        if score > best_score:
                            best_score = score
                            best_output = output
                
                state["aggregated_result"] = best_output
                
            elif strategy == "consensus":
                # Implement consensus logic
                state["aggregated_result"] = self._consensus_aggregation(agent_outputs, agents)
            
            state["status"] = "aggregated"
            return state
        
        return executor

    def _barrier_executor(self, name: str, meta: Dict[str, Any]) -> Callable:
        """Barrier executor for synchronization."""
        def executor(state: Dict[str, Any]) -> Dict[str, Any]:
            agents = meta.get("agents", [])
            sync_type = meta.get("sync_type", "all")
            
            logger.debug(f"[Barrier:{name}] Synchronizing {len(agents)} agents ({sync_type})")
            
            agent_outputs = state.get("agent_outputs", {})
            
            if sync_type == "all":
                # Wait for all agents to complete
                completed = [agent for agent in agents if agent in agent_outputs]
                if len(completed) == len(agents):
                    state["sync_status"] = "all_complete"
                else:
                    state["sync_status"] = f"waiting_for_{len(agents) - len(completed)}"
            
            elif sync_type == "any":
                # Proceed when any agent completes
                if any(agent in agent_outputs for agent in agents):
                    state["sync_status"] = "any_complete"
                else:
                    state["sync_status"] = "waiting_for_any"
            
            state["status"] = "synchronized"
            return state
        
        return executor

    def _condition_executor(self, name: str, meta: Dict[str, Any]) -> Callable:
        """Condition executor for decision making."""
        def executor(state: Dict[str, Any]) -> Dict[str, Any]:
            decision_logic = meta.get("decision_logic", "first_match")
            
            logger.debug(f"[Condition:{name}] Making decision using {decision_logic}")
            
            if decision_logic == "first_match":
                # Return first matching condition
                state["decision_result"] = "first_match"
            elif decision_logic == "best_confidence":
                # Choose path with highest confidence
                agent_outputs = state.get("agent_outputs", {})
                best_confidence = 0
                best_path = None
                
                for agent, output in agent_outputs.items():
                    if isinstance(output, dict):
                        confidence = output.get("confidence", 0)
                        if confidence > best_confidence:
                            best_confidence = confidence
                            best_path = agent
                
                state["decision_result"] = best_path or "default"
            
            state["status"] = "decided"
            return state
        
        return executor

    def _noop_executor(self, name: str) -> Callable:
        """No-operation executor."""
        def executor(state: Dict[str, Any]) -> Dict[str, Any]:
            logger.debug(f"[NoOp:{name}] Passing through state unchanged")
            return state
        
        return executor

    # ---------------------------------------------------------------------
    # Utility Methods
    # ---------------------------------------------------------------------

    def _apply_transformation(self, state: Dict[str, Any], 
                            transformation: Dict[str, Any]) -> Dict[str, Any]:
        """Apply data transformation based on configuration."""
        transform_type = transformation.get("type", "passthrough")
        
        if transform_type == "passthrough":
            return state
        elif transform_type == "filter":
            # Filter specific fields
            fields = transformation.get("fields", [])
            if fields and "agent_outputs" in state:
                current_agent = state.get("current_agent")
                if current_agent in state["agent_outputs"]:
                    output = state["agent_outputs"][current_agent]
                    if isinstance(output, dict):
                        filtered = {k: v for k, v in output.items() if k in fields}
                        state["agent_outputs"][current_agent] = filtered
        elif transform_type == "map":
            # Apply mapping function
            mapping = transformation.get("mapping", {})
            # Implement mapping logic here
            pass
        
        return state

    def _consensus_aggregation(self, agent_outputs: Dict[str, Any], 
                             agents: List[str]) -> Any:
        """Implement consensus-based aggregation."""
        # Simple majority vote implementation
        votes = {}
        
        for agent in agents:
            if agent in agent_outputs:
                output = agent_outputs[agent]
                if isinstance(output, dict):
                    vote = output.get("decision", "unknown")
                    votes[vote] = votes.get(vote, 0) + 1
        
        if votes:
            # Return most common vote
            return max(votes, key=votes.get)
        
        return None

    def _apply_rules(self, spec: GraphSpec, rules: List[Dict[str, Any]]):
        """Enhanced rule application with more rule types."""
        for rule in rules:
            rule_type = rule.get("type")
            if rule_type == "conditional_loop":
                self._apply_conditional_loop_rule(spec, rule)
            elif rule_type == "retry_on_failure":
                self._apply_retry_rule(spec, rule)
            elif rule_type == "timeout":
                self._apply_timeout_rule(spec, rule)
            elif rule_type == "priority":
                self._apply_priority_rule(spec, rule)
            elif rule_type == "transition":
                # Add transition edge from rule['from'] to rule['to'] with condition
                from_node = rule.get("from")
                to_node = rule.get("to")
                condition = rule.get("condition")
                if from_node and to_node:
                    spec["edges"].append({"from": from_node, "to": to_node, "condition": condition})
            else:
                logger.warning(f"Unknown rule type: {rule_type}")

    def _apply_conditional_loop_rule(self, spec: GraphSpec, rule: Dict[str, Any]):
        """Apply conditional loop rule with enhanced logic."""
        condition = rule.get("condition")
        action = rule.get("action")
        
        if action == "return_to_relevant_agent":
            source_agent = rule.get("source_agent", "QA")
            target_agents = rule.get("target_agents", [])
            
            if not target_agents:
                # Default: link to all other agents
                target_agents = [name for name, node in spec["nodes"].items() 
                               if node.get("type") == NodeType.AGENT.value and name != source_agent]
            
            for target in target_agents:
                if source_agent in spec["nodes"] and target in spec["nodes"]:
                    spec["edges"].append({
                        "from": source_agent, 
                        "to": target, 
                        "condition": condition,
                        "metadata": {"rule_type": "conditional_loop"}
                    })

    def _apply_retry_rule(self, spec: GraphSpec, rule: Dict[str, Any]):
        """Apply retry rule to specific agents."""
        target_agents = rule.get("agents", [])
        retry_config = {
            "max_retries": rule.get("max_retries", 3),
            "delay": rule.get("delay", 1),
            "backoff": rule.get("backoff", "exponential")
        }
        
        for agent in target_agents:
            if agent in spec["nodes"]:
                spec["nodes"][agent]["meta"]["retry"] = retry_config

    def _apply_timeout_rule(self, spec: GraphSpec, rule: Dict[str, Any]):
        """Apply timeout rule to specific agents."""
        target_agents = rule.get("agents", [])
        timeout_seconds = rule.get("timeout", 30)
        
        for agent in target_agents:
            if agent in spec["nodes"]:
                spec["nodes"][agent]["meta"]["timeout"] = timeout_seconds

    def _apply_priority_rule(self, spec: GraphSpec, rule: Dict[str, Any]):
        """Apply priority rule to edges."""
        priorities = rule.get("priorities", {})
        
        for edge in spec["edges"]:
            agent = edge.get("to")
            if agent in priorities:
                edge["metadata"] = edge.get("metadata", {})
                edge["metadata"]["priority"] = priorities[agent]

    def _apply_dependencies(self, spec: GraphSpec, dependencies: Dict[str, List[str]]):
        """Enhanced dependency application with validation."""
        for target, sources in dependencies.items():
            if target not in spec["nodes"]:
                logger.warning(f"Dependency target '{target}' not found in nodes")
                continue
            
            for source in sources:
                if source not in spec["nodes"]:
                    logger.warning(f"Dependency source '{source}' not found in nodes")
                    continue
                
                # Check if edge already exists
                existing = any(edge["from"] == source and edge["to"] == target 
                             for edge in spec["edges"])
                
                if not existing:
                    spec["edges"].append({
                        "from": source, 
                        "to": target, 
                        "condition": None,
                        "metadata": {"type": "dependency"}
                    })

    def export_spec_to_dict(self, spec: GraphSpec) -> Dict[str, Any]:
        """Export spec to a clean dictionary format."""
        return {
            "nodes": spec["nodes"],
            "edges": spec["edges"],
            "entry": spec["entry"],
            "metadata": spec.get("meta", {}),
            "statistics": {
                "node_count": len(spec["nodes"]),
                "edge_count": len(spec["edges"]),
                "agent_count": sum(1 for node in spec["nodes"].values() 
                                 if node.get("type") == NodeType.AGENT.value)
            }
        }