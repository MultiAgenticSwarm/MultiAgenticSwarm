# MultiAgenticSwarm Development Guide

**CRITICAL**: Always follow these instructions first before using additional search or context gathering. Only fallback to external resources if the information here is incomplete or found to be in error.

## Working Effectively

MultiAgenticSwarm is a Python-based multi-agent orchestration system built on LangGraph. It provides dynamic configuration, hierarchical tool sharing, and intelligent collaboration patterns between AI agents.

### Essential Setup Commands

**ALWAYS run these commands in order for first-time setup:**

```bash
# Install development dependencies - NEVER CANCEL: Takes 1.5-2 minutes
make install-dev
```

**TIMEOUT REQUIREMENTS:**
- **NEVER CANCEL** installation commands - network dependencies can take 2+ minutes
- Use timeout of 5+ minutes for `make install-dev` to handle network delays
- Installation may appear hung but will complete - wait for full completion

### Core Development Commands

**Validated working commands with measured timings:**

```bash
# Run tests - Takes ~15 seconds, 378 tests, 47% coverage
make test

# Run tests with coverage - Takes ~17 seconds, generates HTML/XML reports  
make test-coverage

# Format code - Takes ~4 seconds, fixes all formatting issues
make format

# Run linting - Takes ~2 seconds, shows style issues (many expected in development)
make lint

# Run security checks - Takes ~1 second, shows 6 warnings (expected in development)
make security

# Build package - Network dependent, set 5+ minute timeout
make build

# Clean artifacts
make clean

# Full development cycle - format, lint, test
make dev

# Complete validation like CI - Takes 2+ minutes, NEVER CANCEL
make validate
```

**CRITICAL TIMEOUT WARNINGS:**
- **NEVER CANCEL** `make install-dev` - Takes up to 2 minutes, often appears hung
- **NEVER CANCEL** `make validate` - Takes 2+ minutes for full CI-like validation
- **NEVER CANCEL** `make build` - Network dependent, can take 3+ minutes
- Set explicit timeouts of 300+ seconds for installation/build commands
- Set timeouts of 60+ seconds for test/validation commands

## Validation Scenarios

**ALWAYS test these scenarios after making changes:**

### Basic System Functionality
```bash
# Test basic import and system creation
python -c "
import multiagenticswarm as mas
from multiagenticswarm.core.system import System

# Test system creation (should work without errors)
system = System()
print('✓ System creation successful')
print('System has tools:', len(system.tools))
print('Tool executor available:', system.tool_executor is not None)
"
```

### CLI Testing
```bash
# Test CLI help (should show usage information)
python -m multiagenticswarm --help

# Test CLI modes
python -m multiagenticswarm --mode cli --help
```

### Example Execution
```bash
# Run working logging demo - Takes ~5 seconds
python examples/logging_demo.py

# Main example has a known trigger bug - avoid using it for validation
# python example.py  # DO NOT USE - has Trigger bug
```

### Complete Functional Test
```bash
# Test full system functionality (agents, tools, system integration)
python -c "
# Full functionality test
import multiagenticswarm as mas
from multiagenticswarm.core.system import System
from multiagenticswarm.core.agent import Agent
from multiagenticswarm.core.base_tool import FunctionTool

print('=== MultiAgenticSwarm Full Functionality Test ===')

# 1. Create system
print('1. Creating system...')
system = System()
print(f'✓ System created with {len(system.tools)} default tools')

# 2. Create a simple agent  
print('2. Creating agent...')
agent = Agent(
    name='TestAgent',
    description='A test agent',
    system_prompt='You are a helpful test agent.'
)
print(f'✓ Agent created: {agent.name}')

# 3. Add agent to system
print('3. Adding agent to system...')
system.register_agent(agent)
print(f'✓ System now has {len(system.agents)} agent(s)')

# 4. Create and register a simple tool
print('4. Creating tool...')
def simple_calc(x: int, y: int) -> int:
    return x + y

tool = FunctionTool(
    name='calculator',
    func=simple_calc,
    description='Simple calculator'
)
tool.set_global()  # Make it available globally
system.register_tool(tool)
print(f'✓ Tool registered, system has {len(system.tools)} tools')

print('✅ All basic functionality working correctly!')
print('🎉 MultiAgenticSwarm is ready for development work!')
"
```

### Import and Module Testing
```bash
# Test all core module imports
python -c "
from multiagenticswarm import Agent, Tool, Task, System
from multiagenticswarm.core import agent, system, tool_executor
print('✓ All imports successful')
"
```

## Project Structure

### Key Directories
- **`multiagenticswarm/`** - Main package source
  - **`core/`** - Core system components (agents, tools, tasks, system)
  - **`llm/`** - LLM provider integrations (OpenAI, Anthropic, AWS)
  - **`tools/`** - Built-in tools (terminal, collaboration)
  - **`utils/`** - Logging and utilities
- **`tests/`** - Comprehensive test suite (378 tests)
- **`examples/`** - Example scripts and demos
- **`docs/`** - Architecture and API documentation

### Important Files
- **`pyproject.toml`** - Package configuration and dependencies
- **`Makefile`** - Development commands (ALWAYS use these)
- **`.pre-commit-config.yaml`** - Code quality hooks
- **`example.py`** - Main example (HAS TRIGGER BUG - avoid for validation)
- **`examples/logging_demo.py`** - Working demo for testing

## Build and Testing

### Dependencies
**Core runtime dependencies:**
- LangGraph ≥0.2.0 (orchestration engine)  
- LangChain ≥0.2.0 (agent framework)
- LangChain providers (OpenAI, Anthropic, AWS)
- Pydantic ≥2.0.0 (data validation)
- AsyncIO-MQTT (event system)

**Development dependencies:** ~50 packages including pytest, black, isort, flake8, mypy, bandit

### Build Process
```bash
# Complete development setup - NEVER CANCEL: 2+ minutes
make setup-dev  # Installs dependencies + pre-commit hooks

# Clean build - Use when build issues occur
make clean
make build
```

### Test Execution
```bash
# Basic tests - 15 seconds, 378 tests
make test

# Coverage tests - 17 seconds, generates htmlcov/ directory
make test-coverage

# Performance tests - If performance issues suspected
make test-performance  # May not work without specific setup
```

## Code Quality

### Pre-commit Validation
**ALWAYS run before committing:**
```bash
# Format code first (required)
make format

# Then run linting (will show issues but should not fail build)
make lint

# Run security checks (6 warnings expected)
make security
```

### Expected Linting Issues
- **Style warnings**: Many W293, E501, D-series warnings expected (work in progress)  
- **Security warnings**: 6 bandit warnings expected in development code
- **Type issues**: mypy continues on error (partially implemented)
- **Format issues**: Fixed automatically by `make format`
- **Exit code 1/2**: `make lint` and `make dev` exit with error codes due to style issues - this is expected and not a failure

**NOTE**: `make dev` will exit with error code due to linting issues, but this is expected behavior. The format and test steps will complete successfully.

### CI/CD Validation
```bash
# Run full CI-like validation - NEVER CANCEL: 2+ minutes
make validate

# Alternative: run individual steps
make clean
make install-dev  # 2+ minutes
make format       # 4 seconds
make lint         # 2 seconds  
make test         # 15 seconds
make build        # 3+ minutes
```

## Common Issues and Solutions

### Installation Problems
- **Network timeouts**: Retry `make install-dev`, can take multiple attempts
- **Permission errors**: Commands install to user directory automatically
- **Missing build tools**: Install build dependencies: `pip install build`

### Test Failures
- **3 skipped tests expected**: Complex async mocking tests skip safely
- **4 warnings expected**: RuntimeWarning from async mocks, safe to ignore
- **Coverage 47%**: Expected coverage level, not a failure

### Build Issues  
- **Network timeouts during build**: Common, retry with longer timeout
- **Missing dependencies**: Run `make install-dev` first
- **Permission issues**: Build uses user directory, should not require sudo

### Running the Application
```bash
# Basic system creation (logging setup automatic)
python -c "from multiagenticswarm.core.system import System; System()"

# Web interface mode (if needed)
python -m multiagenticswarm --mode web --port 8000

# API server mode
python -m multiagenticswarm --mode api --port 8000
```

## Environment Requirements

- **Python**: 3.9+ (tested on 3.9-3.12)
- **OS**: Linux, Windows, macOS (CI tests on all)
- **Memory**: ~100MB baseline for basic operations
- **Network**: Required for LLM provider API calls
- **Disk**: ~500MB for full development environment

## Key Architecture Components

### Agents
- **Agent**: Individual AI agents with specific roles and LLM providers
- **System**: Orchestrates multiple agents and manages their interactions
- **Memory**: Working memory, episodic memory, and conversation history

### Tools  
- **BaseTool**: Foundation for all tools with execution tracking
- **ToolExecutor**: Centralized tool execution with permissions
- **Tool Scopes**: Local, shared, and global tool access levels

### Tasks and Collaboration
- **Task**: Individual work units with status tracking
- **Collaboration**: Multi-agent workflow coordination
- **Automations**: Event-driven automated workflows

## Development Best Practices

1. **ALWAYS run `make format` before committing** - Fixes formatting issues
2. **Run `make test` frequently** - Fast feedback on changes (15 seconds)
3. **Use `make dev` for quick validation** - Combines format, lint, test
4. **Never cancel long-running builds** - Can take 3+ minutes, be patient
5. **Test import functionality** - Ensure changes don't break basic imports
6. **Run logging demo for functional validation** - `python examples/logging_demo.py`
7. **Use validated commands only** - All commands in this guide are tested
8. **Set appropriate timeouts** - Installation: 300s+, Tests: 60s+, Builds: 300s+

**Remember**: This is a complex multi-agent system. Always validate that basic system creation works after making changes, and use the working examples (logging_demo.py) rather than the buggy main example.py.