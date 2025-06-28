# MultiAgenticSwarm Comprehensive Logging

This document explains how to use the comprehensive logging system in MultiAgenticSwarm.

## 🚀 Quick Start

### Basic Setup

```python
import multiagenticswarm as mas
from multiagenticswarm.logging import setup_logging, view_logs, get_summary

# Setup logging (call this once at the beginning)
log_config = setup_logging(
    verbose=True,              # Enable debug logging
    log_directory="./logs",    # Custom log directory
    enable_json_logs=True      # Enable structured JSON logs
)

# Use the system normally - everything gets logged automatically!
system = mas.System(enable_logging=True, verbose=True)
# ... create agents, tools, tasks ...

# View logs after execution
view_logs(lines=50)  # View last 50 log lines
get_summary()        # Get activity summary
```

### Integration with Existing Projects

For existing projects like `flutter_app_builder`:

```python
# At the top of your script:
from multiagenticswarm.logging import setup_logging, view_logs, export_logs

# Setup logging at the beginning
setup_logging(verbose=True, log_directory="./my_project_logs")

# Your existing code remains unchanged!
# The system automatically logs everything

# At the end, view and export logs
view_logs(lines=100)
export_logs("./session_export.json")
```

## 📋 What Gets Logged

The logging system automatically captures:

### 🤖 Agent Activities
- Agent creation and configuration
- Agent actions and decisions
- Agent interactions and collaborations

### 🛠️ Tool Executions
- Tool calls with parameters
- Tool execution results
- Execution time and performance metrics

### 🧠 LLM Interactions
- All requests sent to LLM providers
- Complete responses received
- Token usage and costs
- Provider-specific metadata

### ⚡ System Events
- Task creation and execution
- System state changes
- Error handling and recovery
- Performance metrics

### 🔧 Function Calls
- All function calls with parameters
- Return values and execution time
- Error tracking and stack traces

## 📊 Log Formats

### Text Logs
Human-readable format for quick viewing:
```
2025-06-23 14:15:30 - multiagenticswarm.core.agent - INFO - Agent action: DataAnalyst - process_data
2025-06-23 14:15:31 - multiagenticswarm.llm.openai - INFO - LLM Request to openai/gpt-4
```

### JSON Logs
Structured format for analysis and monitoring:
```json
{
  "timestamp": "2025-06-23T14:15:30.123456",
  "level": "INFO",
  "logger": "multiagenticswarm.core.agent",
  "message": "Agent action: DataAnalyst - process_data",
  "mas_event_type": "agent_action",
  "mas_agent": "DataAnalyst",
  "mas_action": "process_data",
  "mas_session_id": "20250623_141500"
}
```

## 🔍 Viewing and Analyzing Logs

### Quick Viewing
```python
from multiagenticswarm.logging import view_logs, search_logs, get_summary

# View recent activity
view_logs(lines=50)

# Search for specific patterns
search_logs("error")           # Find all errors
search_logs("DataAnalyst")     # Find agent-specific logs
search_logs("openai")          # Find LLM provider logs

# Get overall summary
get_summary()
```

### Detailed Analysis
```python
from multiagenticswarm.logging import (
    get_logs_for_agent, get_logs_for_session, get_llm_logs
)

# Get agent-specific logs
agent_logs = get_logs_for_agent("DataAnalyst")
print(f"DataAnalyst performed {len(agent_logs)} actions")

# Get session-specific logs
session_logs = get_logs_for_session("20250623_141500")

# Get LLM usage analysis
openai_logs = get_llm_logs("openai")
anthropic_logs = get_llm_logs("anthropic")
```

### Export for External Analysis
```python
from multiagenticswarm.logging import export_logs

# Export all logs
export_logs("complete_session.json")

# Export specific agent logs
export_logs("analyst_logs.json", agent_name="DataAnalyst")

# Export specific session
export_logs("session_logs.json", session_id="20250623_141500")
```

## 🔧 Advanced Configuration

### Custom Log Directory
```python
setup_logging(
    log_directory="/path/to/custom/logs",
    max_log_size=50 * 1024 * 1024,  # 50MB per file
    backup_count=10                  # Keep 10 backup files
)
```

### Programmatic Logging
```python
from multiagenticswarm.logging import log_info, log_debug, log_warning, log_error

# Manual logging for custom events
log_info("Processing started", user_id="12345", batch_size=100)
log_debug("Debug information", data={"key": "value"})
log_warning("Performance warning", response_time=5.2)
log_error("Operation failed", error_code=500, details="Network timeout")
```

### Using the Logger Directly
```python
from multiagenticswarm.utils.logger import get_logger

logger = get_logger("my_component")

# Log specific event types
logger.log_function_call("my_function", args=(1, 2), kwargs={"option": True})
logger.log_tool_execution("data_processor", "AnalystAgent", {"file": "data.csv"})
logger.log_llm_request("openai", "gpt-4", [{"role": "user", "content": "Hello"}])
```

## 📱 Real-Time Monitoring

### Command Line Monitoring
```bash
# Monitor text logs in real-time
tail -f ./logs/multiagenticswarm_*.log

# Monitor JSON logs with formatting
tail -f ./logs/multiagenticswarm_*.json | jq .

# Filter for specific events
tail -f ./logs/multiagenticswarm_*.json | jq 'select(.mas_event_type == "llm_request")'
```

### Programmatic Monitoring
```python
import time
from multiagenticswarm.logging import get_summary
from multiagenticswarm.utils.logger import get_log_viewer

def monitor_system():
    viewer = get_log_viewer()
    
    while True:
        print("\\n=== System Status ===")
        get_summary()
        
        # Check for recent errors
        recent_logs = viewer.get_latest_logs(10, "json")
        errors = [log for log in recent_logs if "ERROR" in log]
        if errors:
            print(f"⚠️  {len(errors)} recent errors detected!")
        
        time.sleep(30)  # Check every 30 seconds

# Run monitoring
monitor_system()
```

## 🎯 Use Cases

### Development & Debugging
- Track agent decision-making processes
- Debug tool execution issues
- Monitor LLM response quality
- Identify performance bottlenecks

### Production Monitoring
- Monitor system health and performance
- Track resource usage and costs
- Alert on errors and anomalies
- Analyze user interaction patterns

### Analytics & Optimization
- Measure agent effectiveness
- Optimize tool usage patterns
- Analyze LLM provider performance
- Generate usage reports

### Compliance & Auditing
- Complete audit trail of all operations
- Track data processing and decisions
- Monitor access patterns
- Generate compliance reports

## 📈 Performance Impact

The logging system is designed to be lightweight:

- **Asynchronous writes** to minimize blocking
- **Rotating logs** to manage disk space
- **Structured formats** for efficient parsing
- **Configurable verbosity** levels
- **Minimal memory footprint**

Typical overhead: < 1% CPU, < 10MB memory for normal usage.

## 🔐 Security Considerations

- **Sensitive data filtering**: Automatically filters common sensitive patterns
- **Configurable redaction**: Custom filters for domain-specific data
- **Access controls**: Logs inherit filesystem permissions
- **Retention policies**: Configurable log rotation and cleanup

## 🛠️ Troubleshooting

### Logs Not Appearing
```python
# Check logging configuration
from multiagenticswarm.logging import get_config
config = get_config()
print(config)

# Verify log directory permissions
import os
log_dir = config.get('log_directory', './logs')
print(f"Log directory exists: {os.path.exists(log_dir)}")
print(f"Log directory writable: {os.access(log_dir, os.W_OK)}")
```

### Performance Issues
```python
# Reduce logging verbosity
setup_logging(
    verbose=False,              # Disable debug logs
    enable_json_logs=False,     # Disable JSON if not needed
    max_log_size=5 * 1024 * 1024  # Smaller log files
)
```

### Storage Management
```python
# Automatic cleanup of old logs
setup_logging(
    backup_count=3,             # Keep only 3 backup files
    max_log_size=1024 * 1024    # 1MB per file
)
```

## 📚 Examples

See the complete examples in:
- `examples/logging_demo.py` - Basic logging demonstration
- `examples/flutter_app_builder/flutter_app_builder_with_logging.py` - Real-world integration

## 🤝 Contributing

To add custom logging to your components:

1. Import the logger: `from multiagenticswarm.utils.logger import get_logger`
2. Create a logger instance: `logger = get_logger("my_component")`
3. Use appropriate log methods for your events
4. Follow the existing patterns for consistency

## 📞 Support

For questions or issues with logging:
1. Check the troubleshooting section above
2. Examine the example scripts
3. Review the log files for error messages
4. Open an issue with log samples and configuration details
