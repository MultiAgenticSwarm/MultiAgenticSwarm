"""
Enhanced Compiler: Orchestrates building, validating, materializing, compiling and caching
workflow graphs with advanced features and robust error handling.

Enhanced Features:
- Comprehensive validation and error reporting
- Performance monitoring and metrics
- Advanced caching strategies
- Compilation pipeline with hooks
- Resource management and cleanup
- Detailed logging and debugging support
"""

from __future__ import annotations

import json
import time
import threading
import uuid
from typing import Any, Dict, Optional, Tuple, List, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager
from multiagenticswarm.utils.logger import get_logger

from .graph_builder import GraphBuilder, GraphSpec, ValidationResult
from .cache import GraphCache

logger = get_logger(__name__)


class CompilerError(Exception):
    """Base class for compiler errors."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details or {}


class ValidationError(CompilerError):
    """Raised when graph validation fails."""
    pass


class CompilationError(CompilerError):
    """Raised when graph compilation fails."""
    pass


class ExecutionError(CompilerError):
    """Raised when graph execution fails."""
    pass


class CompilationStage(Enum):
    """Stages of the compilation pipeline."""
    NORMALIZE = "normalize"
    CACHE_LOOKUP = "cache_lookup"
    BUILD_SPEC = "build_spec"
    VALIDATE = "validate"
    MATERIALIZE = "materialize"
    COMPILE = "compile"
    CACHE_STORE = "cache_store"
    COMPLETE = "complete"


@dataclass
class CompilationMetrics:
    """Metrics collected during compilation."""
    stage_times: Dict[str, float] = field(default_factory=dict)
    cache_hit: bool = False
    node_count: int = 0
    edge_count: int = 0
    agent_count: int = 0
    validation_warnings: int = 0
    compilation_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    graph_id: str = ""
    compiler_version: str = "v2"
    total_time_ms: float = 0


@dataclass
class CompilationContext:
    """Context object passed through compilation pipeline."""
    parsed_prompt: Dict[str, Any]
    normalized_prompt: Dict[str, Any]
    spec: Optional[GraphSpec] = None
    validation_result: Optional[ValidationResult] = None
    materialized_graph: Any = None
    compiled_graph: Any = None
    metrics: CompilationMetrics = field(default_factory=CompilationMetrics)
    hooks_data: Dict[str, Any] = field(default_factory=dict)


class Compiler:
    """Enhanced compiler with advanced features and monitoring."""

    def __init__(
        self,
        builder: Optional[GraphBuilder] = None,
        cache: Optional[GraphCache] = None,
        checkpointer_cfg: Optional[Dict[str, Any]] = None,
        compiler_version: str = "v2",
        enable_metrics: bool = True,
        validate_on_compile: bool = True,
        optimization_level: int = 1
    ):
        """
        Initialize the enhanced compiler.
        
        Args:
            builder: GraphBuilder instance
            cache: GraphCache instance  
            checkpointer_cfg: Configuration for checkpointers
            compiler_version: Version string for cache invalidation
            enable_metrics: Whether to collect detailed metrics
            validate_on_compile: Whether to validate specs before compilation
            optimization_level: Level of optimizations to apply (0-3)
        """
        self.builder = builder or GraphBuilder()
        self.cache = cache or GraphCache()
        self.checkpointer_cfg = checkpointer_cfg or {}
        self.compiler_version = compiler_version
        self.enable_metrics = enable_metrics
        self.validate_on_compile = validate_on_compile
        self.optimization_level = optimization_level
        
        # Thread-safe compilation tracking
        self._locks: Dict[str, threading.Lock] = {}
        self._global_lock = threading.Lock()
        self._active_compilations: Dict[str, CompilationContext] = {}
        
        # Pipeline hooks for extensibility
        self._before_hooks: Dict[CompilationStage, List[Callable]] = {stage: [] for stage in CompilationStage}
        self._after_hooks: Dict[CompilationStage, List[Callable]] = {stage: [] for stage in CompilationStage}
        
        # Performance tracking
        self._compilation_stats = {
            "total_compilations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "failed_compilations": 0,
            "average_compile_time_ms": 0
        }
        
        logger.info(f"Initialized enhanced compiler v{compiler_version} with optimization level {optimization_level}")

    # -------------------------
    # Public API
    # -------------------------

    def compile(self, parsed_prompt: Dict[str, Any], 
                execution_context: Optional[Dict[str, Any]] = None) -> Tuple[Any, Dict[str, Any]]:
        """
        Compile a parsed prompt into a runnable graph with comprehensive monitoring.
        
        Args:
            parsed_prompt: The parsed collaboration prompt
            execution_context: Additional context for compilation
            
        Returns:
            Tuple of (compiled_graph, metadata)
        """
        context = CompilationContext(
            parsed_prompt=parsed_prompt,
            normalized_prompt={}
        )
        
        if execution_context:
            context.hooks_data.update(execution_context)
        
        start_time = time.time()
        
        try:
            logger.info(f"Starting compilation {context.metrics.compilation_id}")
            
            # Execute compilation pipeline
            self._execute_pipeline(context)
            
            # Update statistics
            context.metrics.total_time_ms = (time.time() - start_time) * 1000
            self._update_compilation_stats(context)
            
            # Prepare metadata
            metadata = self._create_metadata(context)
            
            logger.info(f"Compilation {context.metrics.compilation_id} completed successfully "
                       f"in {context.metrics.total_time_ms:.2f}ms (cache_hit={context.metrics.cache_hit})")
            
            return context.compiled_graph, metadata
            
        except Exception as e:
            self._compilation_stats["failed_compilations"] += 1
            logger.error(f"Compilation {context.metrics.compilation_id} failed: {e}")
            
            if isinstance(e, (ValidationError, CompilationError)):
                raise
            else:
                raise CompilationError(f"Unexpected compilation error: {e}", 
                                     {"compilation_id": context.metrics.compilation_id})

    def compile_and_run(self, parsed_prompt: Dict[str, Any], 
                       initial_state: Optional[Dict[str, Any]] = None,
                       config: Optional[Dict[str, Any]] = None) -> Tuple[Any, Dict[str, Any]]:
        """
        Compile and execute a graph in one call with enhanced error handling.
        Automatically injects a default 'thread_id' if required by LangGraph checkpointer.
        
        Args:
            parsed_prompt: The parsed collaboration prompt
            initial_state: Initial state for graph execution
            config: Execution configuration
        Returns:
            Tuple of (execution_result, combined_metadata)
        """
        try:
            # Compile the graph
            compiled_graph, compile_metadata = self.compile(parsed_prompt)

            # Prepare execution state
            execution_state = initial_state.copy() if initial_state else {}
            execution_config = config.copy() if config else {}

            # Inject thread_id if required by checkpointer
            required_keys = {"thread_id", "checkpoint_ns", "checkpoint_id"}
            state_keys = set(execution_state.keys())
            config_keys = set(execution_config.keys())
            if not (state_keys & required_keys or config_keys & required_keys):
                execution_state["thread_id"] = "default-thread"
                execution_config["thread_id"] = "default-thread"

            # Inject recursion_limit if not present
            if "recursion_limit" not in execution_config:
                execution_config["recursion_limit"] = 100

            # Execute with monitoring
            start_time = time.time()
            result = self._execute_graph(compiled_graph, execution_state, execution_config)
            execution_time_ms = (time.time() - start_time) * 1000

            # Combine metadata
            combined_metadata = compile_metadata.copy()
            combined_metadata.update({
                "executed": True,
                "execution_time_ms": execution_time_ms,
                "total_time_ms": compile_metadata.get("total_time_ms", 0) + execution_time_ms
            })

            logger.info(f"Graph execution completed in {execution_time_ms:.2f}ms")

            return result, combined_metadata

        except Exception as e:
            logger.error(f"Compile and run failed: {e}")
            if isinstance(e, (CompilerError, ValidationError, CompilationError)):
                raise
            else:
                raise ExecutionError(f"Graph execution failed: {e}")

    def get_compilation_stats(self) -> Dict[str, Any]:
        """Get compilation statistics."""
        with self._global_lock:
            stats = self._compilation_stats.copy()
            stats.update({
                "cache_stats": self.cache.get_statistics() if hasattr(self.cache, 'get_statistics') else {},
                "active_compilations": len(self._active_compilations),
                "cached_graphs": self.cache.size() if hasattr(self.cache, 'size') else 0
            })
            return stats

    def clear_cache(self, force: bool = False) -> Dict[str, Any]:
        """
        Clear compilation cache with optional statistics.
        
        Args:
            force: Whether to force clear even with active compilations
            
        Returns:
            Dictionary with clearing statistics
        """
        try:
            with self._global_lock:
                if not force and self._active_compilations:
                    raise CompilerError(
                        f"Cannot clear cache with {len(self._active_compilations)} active compilations. "
                        "Use force=True to override."
                    )
                
                # Get stats before clearing
                cache_size = self.cache.size() if hasattr(self.cache, 'size') else 0
                
                self.cache.clear()
                self._locks.clear()
                
                logger.info(f"Cleared compilation cache ({cache_size} entries)")
                
                return {
                    "cleared_entries": cache_size,
                    "active_compilations_terminated": len(self._active_compilations) if force else 0
                }
                
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            raise CompilerError(f"Cache clearing failed: {e}")

    def add_before_hook(self, stage: CompilationStage, hook: Callable[[CompilationContext], None]):
        """Add a hook to run before a compilation stage."""
        self._before_hooks[stage].append(hook)
        logger.debug(f"Added before hook for stage {stage.value}")

    def add_after_hook(self, stage: CompilationStage, hook: Callable[[CompilationContext], None]):
        """Add a hook to run after a compilation stage."""
        self._after_hooks[stage].append(hook)
        logger.debug(f"Added after hook for stage {stage.value}")

    def validate_prompt(self, parsed_prompt: Dict[str, Any]) -> ValidationResult:
        """Validate a prompt without full compilation."""
        try:
            normalized = self._normalize(parsed_prompt)
            spec = self.builder.build_spec(normalized)
            return self.builder.validate_spec(spec)
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Validation failed: {e}"]
            )

    # -------------------------
    # Pipeline Implementation
    # -------------------------

    def _execute_pipeline(self, context: CompilationContext):
        """Execute the complete compilation pipeline."""
        stages = [
            (CompilationStage.NORMALIZE, self._stage_normalize),
            (CompilationStage.CACHE_LOOKUP, self._stage_cache_lookup),
            (CompilationStage.BUILD_SPEC, self._stage_build_spec),
            (CompilationStage.VALIDATE, self._stage_validate),
            (CompilationStage.MATERIALIZE, self._stage_materialize),
            (CompilationStage.COMPILE, self._stage_compile),
            (CompilationStage.CACHE_STORE, self._stage_cache_store),
        ]
        
        for stage, stage_func in stages:
            if context.compiled_graph is not None and stage in [CompilationStage.BUILD_SPEC, 
                                                              CompilationStage.VALIDATE, 
                                                              CompilationStage.MATERIALIZE, 
                                                              CompilationStage.COMPILE]:
                # Skip these stages if we got a cache hit
                continue
                
            self._execute_stage(context, stage, stage_func)

    def _execute_stage(self, context: CompilationContext, 
                      stage: CompilationStage, stage_func: Callable):
        """Execute a single pipeline stage with hooks and timing."""
        stage_start = time.time()
        
        try:
            # Run before hooks
            for hook in self._before_hooks[stage]:
                try:
                    hook(context)
                except Exception as e:
                    logger.warning(f"Before hook failed for stage {stage.value}: {e}")
            
            # Execute stage
            stage_func(context)
            
            # Run after hooks
            for hook in self._after_hooks[stage]:
                try:
                    hook(context)
                except Exception as e:
                    logger.warning(f"After hook failed for stage {stage.value}: {e}")
            
            # Record timing
            stage_time = (time.time() - stage_start) * 1000
            context.metrics.stage_times[stage.value] = stage_time
            
            logger.debug(f"Stage {stage.value} completed in {stage_time:.2f}ms")
            
        except Exception as e:
            stage_time = (time.time() - stage_start) * 1000
            context.metrics.stage_times[stage.value] = stage_time
            logger.error(f"Stage {stage.value} failed after {stage_time:.2f}ms: {e}")
            raise

    def _stage_normalize(self, context: CompilationContext):
        """Normalize the parsed prompt."""
        context.normalized_prompt = self._normalize(context.parsed_prompt)
        context.metrics.graph_id = self._graph_id_from_prompt(context.normalized_prompt)

    def _stage_cache_lookup(self, context: CompilationContext):
        """Look up compiled graph in cache using a string key."""
        key = self._graph_id_from_prompt(context.normalized_prompt)  # deterministic string key
        try:
            cached_entry = self.cache.get(key)
            if cached_entry is not None:
                # If your cache stores full object with metadata
                if isinstance(cached_entry, dict) and "compiled_graph" in cached_entry:
                    context.compiled_graph = cached_entry["compiled_graph"]
                else:
                    context.compiled_graph = cached_entry
                context.metrics.cache_hit = True
                logger.debug(f"Cache hit for graph {key}")
        except Exception as e:
            logger.warning(f"Cache lookup failed for graph {key}: {e}")

    def _stage_build_spec(self, context: CompilationContext):
        """Build the graph specification."""
        if context.compiled_graph is not None:
            return  # Skip if cache hit
            
        context.spec = self.builder.build_spec(context.normalized_prompt)
        
        # Update metrics
        context.metrics.node_count = len(context.spec.get("nodes", {}))
        context.metrics.edge_count = len(context.spec.get("edges", []))
        context.metrics.agent_count = sum(
            1 for node in context.spec.get("nodes", {}).values()
            if node.get("type") == "agent"
        )

    def _stage_validate(self, context: CompilationContext):
        """Validate the graph specification."""
        if context.compiled_graph is not None or not self.validate_on_compile:
            return
            
        context.validation_result = self.builder.validate_spec(context.spec)
        context.metrics.validation_warnings = len(context.validation_result.warnings)
        
        if not context.validation_result.is_valid:
            raise ValidationError(
                f"Graph validation failed with {len(context.validation_result.errors)} errors",
                {
                    "errors": context.validation_result.errors,
                    "warnings": context.validation_result.warnings,
                    "graph_id": context.metrics.graph_id
                }
            )
        
        if context.validation_result.warnings:
            logger.warning(f"Graph validation completed with {len(context.validation_result.warnings)} warnings")

    def _stage_materialize(self, context: CompilationContext):
        """Materialize the graph specification."""
        if context.compiled_graph is not None:
            return
            
        try:
            # Create checkpointer if configured
            checkpointer = self._create_checkpointer()
            context.materialized_graph = self.builder.materialize(context.spec, checkpointer)
            
        except ImportError as e:
            raise CompilationError(
                f"Graph materialization failed - LangGraph not available: {e}",
                {"graph_id": context.metrics.graph_id}
            )
        except Exception as e:
            raise CompilationError(
                f"Graph materialization failed: {e}",
                {"graph_id": context.metrics.graph_id}
            )

    def _stage_compile(self, context: CompilationContext):
        """Compile the materialized graph."""
        if context.compiled_graph is not None:
            return
            
        try:
            if hasattr(context.materialized_graph, "compile"):
                # Try different compile signatures
                compile_kwargs = {}
                
                if self.checkpointer_cfg:
                    compile_kwargs.update(self.checkpointer_cfg)
                
                try:
                    context.compiled_graph = context.materialized_graph.compile(**compile_kwargs)
                except TypeError:
                    # Fallback to basic compile
                    context.compiled_graph = context.materialized_graph.compile()
            else:
                # Use materialized graph as compiled graph
                context.compiled_graph = context.materialized_graph
                
        except Exception as e:
            raise CompilationError(
                f"Graph compilation failed: {e}",
                {"graph_id": context.metrics.graph_id}
            )

    def _stage_cache_store(self, context: CompilationContext):
        """Store compiled graph in cache using a string key."""
        if context.metrics.cache_hit:
            return  # Already cached, no need to store again

        key = self._graph_id_from_prompt(context.normalized_prompt)  # deterministic string key
        value = {
            "compiled_graph": context.compiled_graph,
            "normalized_prompt": context.normalized_prompt
        }

        try:
            success = self.cache.set(key, value)
            if not success:
                logger.warning(f"Failed to cache compiled graph {key}")
            else:
                logger.debug(f"Compiled graph cached successfully: {key}")
        except Exception as e:
            logger.warning(f"Cache storage failed for graph {key}: {e}")

    # -------------------------
    # Execution Methods
    # -------------------------

    def _execute_graph(self, compiled_graph: Any, initial_state: Dict[str, Any], 
                      config: Dict[str, Any]) -> Any:
        """Execute a compiled graph with error handling."""
        try:
            # Try different execution methods
            if hasattr(compiled_graph, "invoke"):
                return compiled_graph.invoke(initial_state, config=config)
            elif hasattr(compiled_graph, "run"):
                return compiled_graph.run(initial_state, **config)
            elif hasattr(compiled_graph, "execute"):
                return compiled_graph.execute(initial_state, **config)
            elif callable(compiled_graph):
                return compiled_graph(initial_state)
            else:
                logger.warning("Compiled graph has no known execution method")
                return compiled_graph
                
        except Exception as e:
            raise ExecutionError(f"Graph execution failed: {e}")

    def _create_checkpointer(self) -> Optional[Any]:
        """Create a checkpointer based on configuration."""
        if not self.checkpointer_cfg:
            return None
            
        checkpointer_type = self.checkpointer_cfg.get("type", "memory")
        
        try:
            if checkpointer_type == "memory":
                from langgraph.checkpoint.memory import MemorySaver
                return MemorySaver()
            elif checkpointer_type == "sqlite":
                from langgraph.checkpoint.sqlite import SqliteSaver
                db_path = self.checkpointer_cfg.get("db_path", ":memory:")
                return SqliteSaver.from_conn_string(db_path)
            else:
                logger.warning(f"Unknown checkpointer type: {checkpointer_type}")
                return None
                
        except ImportError as e:
            logger.warning(f"Failed to create checkpointer {checkpointer_type}: {e}")
            return None

    # -------------------------
    # Helper Methods
    # -------------------------

    def _normalize(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced normalization with better handling of complex structures."""
        # Deep copy to avoid mutations
        normalized = self._deep_copy_normalize(parsed)
        
        # Remove volatile keys
        volatile_keys = {
            "request_id", "timestamp", "run_id", "nonce", 
            "session_id", "user_id", "trace_id"
        }
        
        self._remove_volatile_keys(normalized, volatile_keys)
        
        # Sort lists for deterministic hashing
        self._sort_lists_recursively(normalized)
        
        # Add compiler version for cache invalidation
        normalized["_compiler_version"] = self.compiler_version
        
        return normalized

    def _deep_copy_normalize(self, obj: Any) -> Any:
        """Deep copy with normalization."""
        if isinstance(obj, dict):
            return {k: self._deep_copy_normalize(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deep_copy_normalize(item) for item in obj]
        elif isinstance(obj, tuple):
            return tuple(self._deep_copy_normalize(item) for item in obj)
        else:
            return obj

    def _remove_volatile_keys(self, obj: Any, volatile_keys: set):
        """Remove volatile keys recursively."""
        if isinstance(obj, dict):
            for key in list(obj.keys()):
                if key in volatile_keys:
                    del obj[key]
                else:
                    self._remove_volatile_keys(obj[key], volatile_keys)
        elif isinstance(obj, list):
            for item in obj:
                self._remove_volatile_keys(item, volatile_keys)

    def _sort_lists_recursively(self, obj: Any):
        """Sort lists recursively for deterministic serialization."""
        if isinstance(obj, dict):
            for value in obj.values():
                self._sort_lists_recursively(value)
        elif isinstance(obj, list):
            # Only sort if all items are strings or numbers
            if all(isinstance(item, (str, int, float)) for item in obj):
                obj.sort()
            else:
                for item in obj:
                    self._sort_lists_recursively(item)

    def _graph_id_from_prompt(self, normalized_prompt: Dict[str, Any]) -> str:
        """Generate a short graph ID from normalized prompt."""
        import hashlib
        serialized = json.dumps(normalized_prompt, sort_keys=True)
        hash_obj = hashlib.sha256(serialized.encode("utf-8"))
        return hash_obj.hexdigest()[:12]

    def _create_metadata(self, context: CompilationContext) -> Dict[str, Any]:
        """Create comprehensive metadata from compilation context."""
        metadata = {
            "compilation_id": context.metrics.compilation_id,
            "graph_id": context.metrics.graph_id,
            "compiler_version": context.metrics.compiler_version,
            "cached": context.metrics.cache_hit,
            "total_time_ms": context.metrics.total_time_ms,
            "stage_times": context.metrics.stage_times,
            "node_count": context.metrics.node_count,
            "edge_count": context.metrics.edge_count,
            "agent_count": context.metrics.agent_count,
            "validation_warnings": context.metrics.validation_warnings,
            "optimization_level": self.optimization_level
        }
        
        # Add validation details if available
        if context.validation_result:
            metadata["validation"] = {
                "valid": context.validation_result.is_valid,
                "error_count": len(context.validation_result.errors),
                "warning_count": len(context.validation_result.warnings),
                "suggestion_count": len(context.validation_result.suggestions)
            }
        
        return metadata

    def _update_compilation_stats(self, context: CompilationContext):
        """Update global compilation statistics."""
        with self._global_lock:
            self._compilation_stats["total_compilations"] += 1
            
            if context.metrics.cache_hit:
                self._compilation_stats["cache_hits"] += 1
            else:
                self._compilation_stats["cache_misses"] += 1
            
            # Update average compile time
            total = self._compilation_stats["total_compilations"]
            current_avg = self._compilation_stats["average_compile_time_ms"]
            new_avg = ((current_avg * (total - 1)) + context.metrics.total_time_ms) / total
            self._compilation_stats["average_compile_time_ms"] = new_avg

    @contextmanager
    def _compilation_lock(self, graph_id: str):
        """Context manager for per-graph compilation locking."""
        # Get or create lock for this graph
        with self._global_lock:
            if graph_id not in self._locks:
                self._locks[graph_id] = threading.Lock()
            lock = self._locks[graph_id]
        
        # Acquire graph-specific lock
        with lock:
            yield

    def __del__(self):
        """Cleanup on destruction."""
        try:
            # Log final statistics
            if hasattr(self, '_compilation_stats'):
                stats = self._compilation_stats
                logger.info(f"Compiler destroyed. Final stats: {stats['total_compilations']} "
                           f"compilations, {stats['cache_hits']} cache hits, "
                           f"avg time: {stats['average_compile_time_ms']:.2f}ms")
        except:
            pass  # Ignore cleanup errors