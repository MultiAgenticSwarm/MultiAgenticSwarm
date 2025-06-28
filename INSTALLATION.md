# MultiAgenticSwarm Installation Guide

## 🚀 Quick Start

MultiAgenticSwarm is now available as a pip package! You can install it in multiple ways:

### Method 1: Install from PyPI (Recommended)
```bash
pip install multiagenticswarm
```

### Method 2: Install from GitHub
```bash
pip install git+https://github.com/yourusername/multiagenticswarm.git
```

### Method 3: Install from Local Build
```bash
# Clone the repository
git clone https://github.com/yourusername/multiagenticswarm.git
cd multiagenticswarm

# Build the package
python -m build

# Install the built package
pip install dist/multiagenticswarm-0.1.0-py3-none-any.whl
```

## 📦 Usage

### Basic Import
```python
import multiagenticswarm as mas

# Or import specific components
from multiagenticswarm import Agent, Tool, Task, System
```

### Alternative Import Style
```python
# Import as MultiAgenticSwarm if you prefer
import multiagenticswarm as MultiAgenticSwarm

# Create agents
agent = MultiAgenticSwarm.Agent(
    name="MyAgent",
    description="A helpful agent",
    llm_provider="openai"
)
```

### CLI Usage
After installation, you can use the CLI:

```bash
# Show help
multiagenticswarm --help

# Run with configuration
multiagenticswarm --config config.yaml

# Start web interface
multiagenticswarm --mode web --port 8080

# Start API server
multiagenticswarm --mode api --host 0.0.0.0 --port 3000
```

## 🔧 Development Installation

For development, install with all dependencies:

```bash
# Clone the repository
git clone https://github.com/yourusername/multiagenticswarm.git
cd multiagenticswarm

# Install in development mode
pip install -e .[dev]
```

## 📋 Requirements

- Python >= 3.9
- See `pyproject.toml` for full dependency list

## 🧪 Verify Installation

```python
import multiagenticswarm
print(f"Version: {multiagenticswarm.__version__}")
print("Available components:", multiagenticswarm.__all__)
```

## 🚨 Troubleshooting

### Common Issues

1. **Import Error**: Make sure you have Python >= 3.9
2. **Missing Dependencies**: Install with `pip install multiagenticswarm[dev]` for all features
3. **CLI Not Found**: Make sure your pip installation directory is in your PATH

### Environment Variables

Set these environment variables for LLM providers:

```bash
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export AWS_ACCESS_KEY_ID="your-aws-key"
export AWS_SECRET_ACCESS_KEY="your-aws-secret"
```

## 📚 Next Steps

- Check out the [examples](examples/) directory
- Read the [documentation](docs/)
- Run the example: `python -m multiagenticswarm.examples.basic`
