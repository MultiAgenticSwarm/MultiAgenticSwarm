# Collaboration Patterns

Reusable, composable patterns for multi-agent collaboration.

## Quick Start

```python
from multiagenticswarm.patterns import SupervisorPattern

# Create a pattern
pattern = SupervisorPattern()

# Build graph topology
topology = pattern.build_topology(
    agents=["worker1", "worker2", "worker3"],
    supervisor_name="boss"
)

# Create router
router = pattern.create_router(
    supervisor_name="boss",
    routing_strategy="round_robin"
)

print(f"Nodes: {topology.nodes}")
print(f"Edges: {topology.edges}")
```

## Available Patterns

| Pattern | Description | Use Case |
|---------|-------------|----------|
| **Supervisor** | Central coordinator delegates and collects | Task delegation, coordination |
| **Parallel** | Independent parallel execution with join | Distributed processing, concurrent tasks |
| **Sequential** | Linear pipeline execution | Step-by-step workflows, pipelines |
| **Consensus** | Democratic voting and aggregation | Multi-perspective decisions |
| **Competitive** | Quality-driven selection by judge | Tournament-style evaluation |

## Features

✅ **5 Built-in Patterns** - Ready-to-use collaboration patterns  
✅ **Pattern Composition** - Combine patterns into complex workflows  
✅ **Pattern Detection** - Automatically identify pattern types  
✅ **Custom Patterns** - Extend with your own patterns  
✅ **Pattern Registry** - Central management and discovery  
✅ **Fully Tested** - Comprehensive test suite (28 tests)  
✅ **Well Documented** - Complete API docs and examples  

## Installation

The patterns library is included with MultiAgenticSwarm:

```bash
pip install multiagenticswarm
```

## Examples

See [`examples/patterns_demo.py`](../examples/patterns_demo.py) for comprehensive usage examples.

Run examples:
```bash
python -m examples.patterns_demo
```

## Documentation

Full documentation: [`docs/PATTERNS.md`](../docs/PATTERNS.md)

## Testing

Run tests:
```bash
pytest tests/test_patterns.py -v
```

## Architecture

```
patterns/
├── __init__.py          # Package exports and registry setup
├── base.py              # Base classes, registry, detection
├── supervisor.py        # Supervisor pattern
├── parallel.py          # Parallel pattern
├── sequential.py        # Sequential pattern
├── consensus.py         # Consensus pattern
├── competitive.py       # Competitive pattern
└── composite.py         # Pattern composition
```

## Contributing

1. Create pattern class inheriting from `CollaborationPattern`
2. Implement `_create_metadata()`, `build_topology()`, `create_router()`
3. Register in `__init__.py`
4. Add tests and examples
5. Update documentation

## License

See LICENSE file in repository root.
