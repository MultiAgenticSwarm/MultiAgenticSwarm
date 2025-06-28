# MultiAgenticSwarm Examples

This directory contains examples demonstrating various features and use cases of the MultiAgenticSwarm.

## 📂 Available Examples

### 🚀 Flutter App Builder (`flutter_app_builder/`)

A comprehensive example showing how to build Flutter applications using multiple specialized agents with shared tools.

**Features Demonstrated:**
- Multi-agent collaboration (Implementation + Testing agents)
- Hierarchical tool sharing (Terminal and FileManager tools)
- Multi-LLM integration (GPT-4 + Claude-3.5-Sonnet)
- Configuration-driven setup
- Real-world development workflow

**Files:**
- `flutter_builder.py` - Full programmatic implementation
- `config_driven_builder.py` - Configuration-based version
- `simple_demo.py` - Simplified demonstration
- `flutter_config.yaml` - YAML configuration file
- `README.md` - Detailed documentation

**Quick Start:**
```bash
cd examples/flutter_app_builder
python simple_demo.py
```

## 🎯 Example Categories

### 🔰 Beginner Examples
- **Flutter App Builder (Simple Demo)** - Basic multi-agent collaboration
- Coming soon: Basic task automation, Simple tool sharing

### 🔧 Intermediate Examples
- **Flutter App Builder (Full Version)** - Complete development workflow
- Coming soon: Data processing pipeline, API integration workflow

### 🚀 Advanced Examples
- **Flutter App Builder (Config-Driven)** - Enterprise configuration patterns
- Coming soon: Multi-team collaboration, Complex automation chains

## 🛠️ Running Examples

### Prerequisites

1. Install the MultiAgenticSwarm:
```bash
pip install multiagenticswarm
```

2. Set up your LLM API keys:
```bash
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
```

### General Pattern

Each example follows this structure:
```
example_name/
├── main_script.py          # Primary implementation
├── config.yaml            # Configuration file (if applicable)
├── simple_demo.py          # Simplified version
├── README.md              # Detailed documentation
└── requirements.txt       # Additional dependencies (if needed)
```

## 📚 Key Concepts Demonstrated

### 🤖 Agent Management
- Creating specialized agents with different LLM providers
- Agent configuration and system prompts
- Memory management and conversation history

### 🔧 Tool System
- **Local Tools**: Available to specific agents only
- **Shared Tools**: Available to multiple designated agents
- **Global Tools**: Available to all agents in the system

### 📋 Task Orchestration
- Sequential task execution
- Parallel processing
- Dependency management
- Collaborative workflows

### ⚙️ Configuration Management
- YAML-based system configuration
- Runtime configuration updates
- Environment-specific settings

### 🔄 Event-Driven Automation
- Trigger-based workflows
- Event handling and processing
- Automated task execution

## 🎨 Use Case Examples

### 📱 Software Development
- **Flutter App Builder**: Mobile app development with testing
- Coming soon: Web app development, API service creation

### 📊 Data Processing
- Coming soon: ETL pipelines, Data analysis workflows, Report generation

### 🏢 Business Automation
- Coming soon: Document processing, Customer service automation, Workflow management

### 🧪 Research & Analysis
- Coming soon: Literature review, Data analysis, Hypothesis testing

## 🔗 Quick Navigation

| Example | Complexity | Use Case | Key Features |
|---------|------------|----------|--------------|
| [Flutter App Builder](flutter_app_builder/) | ⭐⭐⭐ | Mobile Development | Multi-agent, Shared tools, Real workflow |

## 🤝 Contributing Examples

Want to contribute an example? Great! Please follow these guidelines:

1. **Structure**: Follow the standard example structure
2. **Documentation**: Include a comprehensive README.md
3. **Complexity Levels**: Provide both simple and advanced versions
4. **Real-world Relevance**: Demonstrate practical use cases
5. **Best Practices**: Show proper system design patterns

### Template Structure
```
your_example/
├── README.md              # Comprehensive documentation
├── simple_demo.py         # Basic demonstration
├── full_implementation.py # Complete version
├── config.yaml           # Configuration file
└── requirements.txt      # Dependencies
```

## 🚀 Next Steps

After exploring these examples:

1. **Start Simple**: Begin with `simple_demo.py` files
2. **Understand Concepts**: Read the comprehensive versions
3. **Experiment**: Modify examples to fit your use cases
4. **Build Custom**: Create your own multi-agent systems
5. **Share**: Contribute your examples back to the community

## 📖 Additional Resources

- [MultiAgenticSwarm Documentation](../README.md)
- [API Reference](../docs/api/)
- [Best Practices Guide](../docs/best_practices.md)
- [Contributing Guidelines](../CONTRIBUTING.md)

Happy building! 🚀
