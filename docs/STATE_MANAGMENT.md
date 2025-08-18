# State Management Documentation

## Overview

State management is the core of MultiAgenticSwarm's flexibility. The AgentState TypedDict serves as the single source of truth flowing through all graph nodes.

## AgentState Schema

### File Location
`multiagenticswarm/core/state.py` (To be created)

### Core Schema Definition

The AgentState is a TypedDict that contains all data needed for multi-agent collaboration:

#### Message Management
- **messages**: Conversation history using LangGraph's add_messages reducer
  - Automatically merges new messages
  - Preserves order and metadata
  - Includes human, AI, system, and tool messages

#### Task Management
- **current_task**: Active task description
- **subtasks**: Breakdown of main task
- **task_progress**: Percentage completion per subtask
- **task_metadata**: Additional task context

#### Agent Coordination
- **current_agent**: Currently executing agent ID
- **next_agent**: Next agent to execute
- **agent_outputs**: Results from each agent
- **agent_queue**: Pending agent executions
- **agent_status**: Health/availability per agent

#### Tool Execution
- **tool_calls**: History of tool requests
- **tool_results**: Results from tool executions
- **tool_permissions**: Dynamic permission matrix
- **pending_tools**: Queued tool requests
- **tool_errors**: Failed tool executions

#### Collaboration Context
- **collaboration_prompt**: Natural language instructions
- **coordination_rules**: Extracted rules and constraints
- **agent_roles**: Role assignments per agent
- **workflow_pattern**: Current collaboration pattern
- **decision_points**: Conditional branch points

#### Memory Layers
- **short_term_memory**: Current conversation context
- **working_memory**: Active task information
- **episodic_memory**: Sequence of events
- **shared_memory**: Information visible to all agents
- **private_memory**: Agent-specific information

#### Communication
- **agent_messages**: Inter-agent communications
- **help_requests**: Assistance requests between agents
- **broadcast_messages**: System-wide announcements
- **pending_responses**: Awaiting agent responses

#### Control Flow
- **should_continue**: Whether to proceed with execution
- **requires_human_approval**: Pause for human input
- **interrupt_checkpoint**: Where to pause execution
- **resume_point**: Where to continue after interrupt
- **execution_mode**: Sequential/parallel/supervisor

#### Debugging & Monitoring
- **state_version**: Schema version for compatibility
- **execution_trace**: Step-by-step execution log
- **error_log**: Error messages and stack traces
- **performance_metrics**: Timing and resource usage
- **debug_flags**: Enable detailed logging

## State Reducers

### What Are Reducers?
Reducers are functions that define how to merge state updates, especially important for concurrent modifications.

### Built-in Reducers

#### add_messages
- Provided by LangGraph
- Appends new messages to existing list
- Handles deduplication
- Preserves chronological order

### Custom Reducers

#### merge_agent_outputs
- Combines outputs from multiple agents
- Resolves conflicts based on timestamp
- Preserves all historical outputs

#### aggregate_progress
- Calculates overall progress from subtasks
- Weights tasks by importance
- Handles partial completions

#### resolve_permissions
- Merges permission updates
- Most restrictive permission wins
- Maintains audit trail

## State Lifecycle

### 1. Initialization
- Empty state created with defaults
- Collaboration prompt added
- Initial message added
- Agent roles assigned

### 2. Node Processing
- Node receives state
- Transforms relevant sections
- Returns modified state
- Reducers merge changes

### 3. Checkpointing
- State serialized to dictionary
- Saved to SQLite with metadata
- Checkpoint ID generated
- Previous checkpoint linked

### 4. Recovery
- Checkpoint loaded by ID
- State reconstructed
- Graph position restored
- Execution resumes

## State Access Patterns

### Read Patterns

#### Full State Access
Nodes that need complete visibility (routers, supervisors)

#### Filtered Access
Nodes that only see permitted sections (isolated agents)

#### Historical Access
Nodes that need previous states (learning agents)

### Write Patterns

#### Append-Only
Messages, logs, traces (never overwritten)

#### Last-Write-Wins
Status fields, current agent, progress

#### Merged Updates
Agent outputs, tool results (combined via reducers)

## State Partitioning

### Global State
Accessible to all nodes:
- Messages
- Current task
- Workflow pattern

### Shared State
Accessible to specific groups:
- Team-specific context
- Shared tools results
- Group communications

### Private State
Accessible to single agent:
- Internal reasoning
- Private memory
- Agent-specific config

## State Migration

### Schema Versioning
Each state includes version number for compatibility checking

### Migration Strategies

#### Forward Compatible
New fields have defaults, old graphs continue working

#### Backward Compatible
Old fields maintained, new graphs work with old state

#### Breaking Changes
Require migration function to transform state

### Migration Process
1. Detect version mismatch
2. Load appropriate migration function
3. Transform state to new schema
4. Validate transformed state
5. Continue execution

## State Optimization

### Memory Management
- Large fields stored separately
- Lazy loading for historical data
- Compression for checkpoints
- Cleanup of old checkpoints

### Performance
- Minimal state copying
- Efficient serialization
- Indexed checkpoint storage
- Caching of frequent accesses

## State Debugging

### State Inspector
Tools to examine current state:
- Pretty printing
- Diff between states
- State history browser
- Field-level tracking

### State Validation
- Schema compliance checking
- Constraint validation
- Consistency verification
- Corruption detection

## Error Handling

### State Corruption
- Automatic backup states
- Corruption detection
- Recovery procedures
- Fallback to last good state

### State Conflicts
- Merge conflict resolution
- Manual intervention points
- Conflict logging
- Automatic resolution rules
