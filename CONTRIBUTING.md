# Contributing to MultiAgenticSwarm

We welcome contributions to MultiAgenticSwarm! This document provides guidelines for contributing to the project.

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- Basic knowledge of LLMs and multi-agent systems

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/multiagenticswarm/multiagenticswarm.git
   cd multiagenticswarm
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Run tests to verify setup**
   ```bash
   pytest
   ```

## 🛠️ Development Workflow

### Code Style

We use the following tools for code quality:

- **Black** for code formatting
- **Flake8** for linting
- **MyPy** for type checking

Run these before submitting:

```bash
black multiagenticswarm/
flake8 multiagenticswarm/
mypy multiagenticswarm/
```

### Testing

- Write tests for new features
- Ensure all tests pass before submitting
- Aim for good test coverage

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=multiagenticswarm

# Run specific test file
pytest tests/test_agent.py
```

### Documentation

- Update docstrings for new functions and classes
- Update README.md if adding major features
- Add examples for new functionality

## 📝 Contribution Types

### 🐛 Bug Reports

When reporting bugs, please include:

- Python version and OS
- MultiAgenticSwarm version
- Minimal code example that reproduces the issue
- Expected vs. actual behavior
- Error messages and stack traces

### ✨ Feature Requests

For new features, please:

- Check if it's already planned in issues
- Explain the use case and benefits
- Provide example usage if possible
- Consider backward compatibility

### 🔧 Pull Requests

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow the code style guidelines
   - Add tests for new functionality
   - Update documentation as needed

4. **Test your changes**
   ```bash
   pytest
   black multiagenticswarm/
   flake8 multiagenticswarm/
   ```

5. **Commit with clear messages**
   ```bash
   git commit -m "feat: add hierarchical tool sharing"
   ```

6. **Push and create a pull request**
   ```bash
   git push origin feature/your-feature-name
   ```

### Commit Message Convention

We follow conventional commits:

- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation changes
- `style:` formatting changes
- `refactor:` code refactoring
- `test:` adding tests
- `chore:` maintenance tasks

## 🏗️ Architecture Guidelines

### Core Principles

1. **Modularity**: Keep components loosely coupled
2. **Extensibility**: Make it easy to add new agents, tools, and providers
3. **Type Safety**: Use type hints and validation
4. **Documentation**: Clear docstrings and examples
5. **Testing**: Comprehensive test coverage

### Adding New Components

#### New LLM Provider

1. Create a new provider class in `llm/providers.py`
2. Inherit from `LLMProvider`
3. Implement required methods
4. Add to `PROVIDER_REGISTRY`
5. Add tests and documentation

#### New Tool Type

1. Create tool in `core/tool.py` or as a plugin
2. Follow the Tool interface
3. Support hierarchical sharing
4. Add comprehensive tests

#### New Trigger Type

1. Extend `TriggerType` enum
2. Implement evaluation logic in `Trigger.evaluate()`
3. Add factory function if useful
4. Test thoroughly

## 🧪 Testing Guidelines

### Test Structure

```
tests/
├── __init__.py
├── test_agent.py          # Agent tests
├── test_tool.py           # Tool tests
├── test_task.py           # Task tests
├── test_system.py         # System tests
├── integration/           # Integration tests
└── fixtures/              # Test fixtures
```

### Test Categories

- **Unit Tests**: Test individual components
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete workflows
- **Performance Tests**: Test system performance

### Mock Guidelines

- Mock external dependencies (LLM APIs, databases)
- Use realistic test data
- Test error conditions

## 📋 Code Review Process

### Review Criteria

- Code follows style guidelines
- Tests are comprehensive
- Documentation is clear
- No breaking changes without good reason
- Performance considerations
- Security implications

### Review Process

1. Automated checks must pass
2. At least one maintainer review
3. All feedback addressed
4. Tests pass on multiple Python versions

## 🚢 Release Process

### Versioning

We follow [Semantic Versioning](https://semver.org/):

- `MAJOR.MINOR.PATCH`
- MAJOR: breaking changes
- MINOR: new features (backward compatible)
- PATCH: bug fixes

### Release Steps

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create release tag
4. Build and publish to PyPI
5. Update documentation

## 🤝 Community Guidelines

### Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help newcomers learn
- Collaborate professionally

### Communication

- Use GitHub issues for bugs and features
- Join Discord for real-time discussion
- Tag maintainers for urgent issues
- Provide clear, detailed information

## 📚 Resources

### Documentation

- [API Reference](https://multiagenticswarm.readthedocs.io/api/)
- [User Guide](https://multiagenticswarm.readthedocs.io/guide/)
- [Examples](https://github.com/multiagenticswarm/multiagenticswarm/tree/main/examples)

### Related Projects

- [LangGraph](https://github.com/langchain-ai/langgraph)
- [LangChain](https://github.com/langchain-ai/langchain)
- [CrewAI](https://github.com/joaomdmoura/crewAI)
- [AutoGen](https://github.com/microsoft/autogen)

## ❓ Getting Help

- **Documentation**: Check docs first
- **GitHub Issues**: Search existing issues
- **Discord**: Real-time help and discussion
- **Stack Overflow**: Tag `multiagenticswarm`

## 🙏 Recognition

Contributors will be:

- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Invited to maintainer discussions (major contributors)

Thank you for contributing to MultiAgenticSwarm! 🎉
