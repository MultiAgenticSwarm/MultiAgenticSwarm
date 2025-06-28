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

# Create agents with different LLMs
agent1 = Agent("DataAnalyst", 
               system_prompt="You are a data analyst",
               llm_provider="openai",
               llm_model="gpt-4")

agent2 = Agent("ActionExecutor",
               system_prompt="You execute actions",
               llm_provider="anthropic", 
               llm_model="claude-3.5-sonnet")

# Create tools with different sharing levels
local_tool = Tool("DataFetcher", 
                  func=lambda query: fetch_data(query))
local_tool.set_local(agent1)

shared_tool = Tool("DataProcessor",
                   func=lambda data: process(data))
shared_tool.set_shared(agent1, agent2)

global_tool = Tool("Logger", 
                   func=lambda msg: print(f"LOG: {msg}"))
global_tool.set_global()

# Create collaborative tasks
task = Task("AnalyzeAndAct", steps=[
    {"agent": agent1, "tool": "DataFetcher", "input": "get latest data"},
    {"agent": agent2, "tool": "DataProcessor", "input": "process data"},
    {"agent": agent2, "tool": "Logger", "input": "task completed"}
])

# Build and run system
system = System()
system.register_agents(agent1, agent2)
system.register_tools(local_tool, shared_tool, global_tool)
system.register_tasks(task)

if __name__ == "__main__":
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