# MultiAgenticSwarm

A powerful LangGraph-based multi-agent system with dynamic configuration and hierarchical tool sharing.

## 🚀 Features

- **Dynamic Agent Management**: Create and configure agents at runtime
- **Hierarchical Tool Sharing**: Local, shared, and global tool scopes
- **Multi-LLM Support**: Use different LLM providers for each agent
- **Event-Driven Automation**: Trigger-based workflow execution
- **LangGraph Integration**: Production-grade state management
- **Configuration-Driven**: JSON/YAML-based setup without code changes

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Agents      │    │     Tools       │    │     Tasks       │
│                 │    │                 │    │                 │
│ • Agent1 (GPT)  │◄──►│ • Local Tools   │◄──►│ • Sequences     │
│ • Agent2 (Claude)│   │ • Shared Tools  │    │ • Handoffs      │
│ • Agent3 (Bedrock)│   │ • Global Tools  │    │ • Collaborations│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲                       ▲
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ LangGraph Core  │
                    │                 │
                    │ • State Machine │
                    │ • Workflow Mgmt │
                    │ • Event System  │
                    └─────────────────┘
```

## 🎯 Quick Start

### Installation

```bash
# Install from PyPI (when published)
pip install multiagenticswarm

# Or install from source
pip install git+https://github.com/yourusername/multiagenticswarm.git

# Or build and install locally
git clone https://github.com/yourusername/multiagenticswarm.git
cd multiagenticswarm
python -m build
pip install dist/multiagenticswarm-0.1.0-py3-none-any.whl
```

### Basic Usage

```python
import multiagenticswarm as mas
# Or: from multiagenticswarm import Agent, Tool, Task, System

# Set up comprehensive logging
mas.setup_logging(verbose=True)

# Create agents with different LLMs
agent1 = mas.Agent("DataAnalyst", 
                   system_prompt="You are a data analyst specialized in extracting insights from data",
                   llm_provider="openai",
                   llm_model="gpt-4")

agent2 = mas.Agent("ActionExecutor",
                   system_prompt="You execute actions based on data analysis",
                   llm_provider="anthropic", 
                   llm_model="claude-3.5-sonnet")

# Define actual functions for tools
def fetch_data(query):
    """Fetch data from various sources"""
    return f"Data for query: {query}"

def process_data(data):
    """Process and analyze data"""
    return f"Processed: {data}"

def log_message(msg):
    """Log important messages"""
    print(f"LOG: {msg}")
    return f"Logged: {msg}"

# Create tools with different sharing levels
local_tool = mas.Tool("DataFetcher", 
                      func=fetch_data,
                      description="Fetches data from external sources")
local_tool.set_local(agent1)

shared_tool = mas.Tool("DataProcessor",
                       func=process_data,
                       description="Processes and analyzes data")
shared_tool.set_shared(agent1, agent2)

global_tool = mas.Tool("Logger", 
                       func=log_message,
                       description="Logs messages to console")
global_tool.set_global()

# Create collaborative tasks
task = mas.Task("AnalyzeAndAct", 
                description="Analyze data and execute actions",
                steps=[
                    {"agent": "DataAnalyst", "tool": "DataFetcher", "input": "get latest market data"},
                    {"agent": "DataAnalyst", "tool": "DataProcessor", "input": "analyze trends"},
                    {"agent": "ActionExecutor", "tool": "DataProcessor", "input": "validate results"},
                    {"agent": "ActionExecutor", "tool": "Logger", "input": "task completed successfully"}
                ])

# Create event-driven automation
trigger = mas.Trigger("DataAvailable", 
                      condition=lambda event: event.get("type") == "data_ready")
automation = mas.Automation("AutoAnalyze", trigger=trigger, task=task)

# Build and run system
system = mas.System(enable_logging=True, verbose=True)
system.register_agents(agent1, agent2)
system.register_tools(local_tool, shared_tool, global_tool)
system.register_tasks(task)
system.register_automations(automation)

# Execute the system
if __name__ == "__main__":
    # Run a single task
    result = system.execute_task("AnalyzeAndAct")
    print(f"Task result: {result}")
    
    # Or run the full system with automations
    system.run()
```

### Configuration-Driven Setup

```yaml
# config.yaml
agents:
  - name: "DataAnalyst"
    description: "Analyzes data patterns"
    system_prompt: "You are an expert data analyst"
    llm_provider: "openai"
    llm_model: "gpt-4"
  
  - name: "ActionExecutor" 
    description: "Executes business actions"
    system_prompt: "You execute actions based on analysis"
    llm_provider: "anthropic"
    llm_model: "claude-3.5-sonnet"

tools:
  - name: "DataFetcher"
    description: "Fetches data from APIs"
    scope: "local"
    agents: ["DataAnalyst"]
    
  - name: "DataProcessor"
    description: "Processes and transforms data"
    scope: "shared" 
    agents: ["DataAnalyst", "ActionExecutor"]
    
  - name: "Logger"
    description: "System logger"
    scope: "global"

tasks:
  - name: "AnalyzeAndAct"
    description: "Complete analysis and action workflow"
    steps:
      - agent: "DataAnalyst"
        tool: "DataFetcher" 
        input: "fetch latest sales data"
      - agent: "DataAnalyst"
        tool: "DataProcessor"
        input: "analyze trends"
      - agent: "ActionExecutor"
        tool: "DataProcessor"
        input: "create action plan"
      - agent: "ActionExecutor"
        tool: "Logger"
        input: "workflow completed"

triggers:
  - name: "OnDataUpdate"
    condition: "event.type == 'data_update'"
    
automations:
  - trigger: "OnDataUpdate"
    task: "AnalyzeAndAct"
```

Then run with:

```python
from multiagenticswarm import System

system = System.from_config("config.yaml")
system.run()
```

## 📚 Examples

We provide several comprehensive examples to get you started:

### 🔰 Simple Example
```bash
python simple_example.py
```
A basic demonstration showing agent collaboration and tool sharing.

### 🚀 Complete Example  
```bash
python complete_example.py
```
Full-featured demonstration showcasing all MultiAgenticSwarm capabilities.

### 🏢 Real-World Example
```bash
python real_world_example.py
```
Production-ready content creation pipeline with multiple agents and automation.

### 📱 Flutter Development Example
```bash
cd examples/flutter/
python create_app_with_llm.py
```
Demonstrates using MultiAgenticSwarm for Flutter app development.

## 🔧 Advanced Features

### Event-Driven Automations

```python
from multiagenticswarm import Trigger, Automation

# Define triggers
email_trigger = Trigger("OnEmailReceived", 
                       condition=lambda event: event.type == "email")

# Create automations
auto_response = Automation(email_trigger, sequence=email_task)
system.register_automations(auto_response)
```

### Custom Tool Development

```python
from multiagenticswarm import Tool

def custom_api_call(endpoint: str, data: dict) -> dict:
    # Your custom logic here
    return {"result": "success"}

api_tool = Tool("CustomAPI", 
               func=custom_api_call,
               description="Calls custom API endpoints")
api_tool.set_shared(agent1, agent2)
```

### Multi-Provider LLM Setup

```python
# Mix different LLM providers in one system
agents = [
    Agent("Cheap", llm_provider="openai", llm_model="gpt-3.5-turbo"),    # Cost-effective
    Agent("Smart", llm_provider="anthropic", llm_model="claude-3.5"),     # High reasoning
    Agent("Fast", llm_provider="together", llm_model="llama-3.1-8b"),     # Speed
    Agent("Enterprise", llm_provider="azure", llm_model="gpt-4"),         # Compliance
]
```

## 🎯 Best Practices

### Agent Design
- **Specialized Roles**: Create agents with specific, well-defined responsibilities
- **Clear Prompts**: Write detailed system prompts that define the agent's expertise
- **Appropriate Models**: Match LLM models to task complexity (GPT-4 for complex reasoning, GPT-3.5 for simple tasks)

### Tool Hierarchy
- **Local Tools**: Use for agent-specific functionality (e.g., specialized APIs)
- **Shared Tools**: Use for collaborative functionality (e.g., data processing)
- **Global Tools**: Use for common utilities (e.g., logging, notifications)

### Task Design
- **Atomic Steps**: Break complex workflows into clear, manageable steps
- **Sequential Flow**: Design logical progression from one agent to another
- **Error Handling**: Include validation and retry mechanisms

### System Architecture
```python
# Recommended pattern for production systems
system = mas.System(enable_logging=True, verbose=True)

# Register components in order
system.register_agents(*agents)      # Agents first
system.register_tools(*tools)        # Then tools  
system.register_tasks(*tasks)        # Then tasks
system.register_automations(*autos)  # Finally automations

# Execute with proper error handling
try:
    result = system.execute_task("TaskName")
    logger.info(f"Task completed: {result}")
except Exception as e:
    logger.error(f"Task failed: {e}")
    # Implement retry or fallback logic
```

## 🛠️ Development

### Running from Source

```bash
git clone https://github.com/multiagenticswarm/multiagenticswarm
cd multiagenticswarm
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black multiagenticswarm/
flake8 multiagenticswarm/
mypy multiagenticswarm/
```

## 📚 Documentation

- **[API Reference](https://multiagenticswarm.readthedocs.io/api/)**
- **[User Guide](https://multiagenticswarm.readthedocs.io/guide/)**
- **[Examples](https://github.com/multiagenticswarm/multiagenticswarm/tree/main/examples)**

## 🏆 Why MultiAgenticSwarm?

| Feature | CrewAI | AutoGen | LangGraph | **MultiAgenticSwarm** |
|---------|--------|---------|-----------|------------------------|
| **Ease of Use** | ✅ Simple | ❌ Complex | ❌ Low-level | ✅ **Simple + Powerful** |
| **Tool Sharing** | ❌ Basic | ❌ Limited | ❌ Manual | ✅ **Hierarchical** |
| **Multi-LLM** | ❌ OpenAI-focused | ✅ Good | ✅ Manual | ✅ **Unified Interface** |
| **Configuration** | ❌ Code-only | ❌ Code-only | ❌ Code-only | ✅ **JSON/YAML** |
| **Event System** | ❌ None | ❌ Basic | ❌ Manual | ✅ **Built-in** |
| **Production Ready** | ❌ Basic | ✅ Research | ✅ Core | ✅ **Enterprise** |

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 🔗 Links

- **GitHub**: https://github.com/multiagenticswarm/multiagenticswarm
- **PyPI**: https://pypi.org/project/multiagenticswarm/
- **Documentation**: https://multiagenticswarm.readthedocs.io
- **Discord**: https://discord.gg/MultiAgenticSwarm