# Flutter Music App - Multi-Agent Collaboration Demo

This demo showcases how **collaboration prompts** guide agent behavior and task delegation in the MultiAgenticSwarm framework. The key feature is that **you define how agents should collaborate**, and they adapt their working style accordingly.

## 🎯 What This Demo Demonstrates

### ✅ **User-Defined Collaboration Patterns**
- Agents read collaboration instructions from configuration
- Task delegation adapts based on collaboration style
- Different prompts lead to different agent behaviors

### ✅ **Real LLM Integration**
- All agents use Anthropic Claude for code generation
- No hardcoded Flutter code - everything generated via LLM calls
- Agents understand collaboration context when generating code

### ✅ **Functional Flutter App Creation**
- Agents generate a complete, working Flutter music streaming app
- Proper project structure with screens, services, and models
- Material Design 3 implementation

### ✅ **Progress Tracking & Communication**
- Centralized progress board for all agent communication
- Real-time collaboration and interface sharing
- Audit trail of all agent interactions

## 🚀 Quick Start

### View Available Collaboration Patterns
```bash
python demo_collaboration.py help
```

### Test Different Collaboration Styles

**Sequential Development** (Data → Audio → UI):
```bash
python demo_collaboration.py sequential
```

**Parallel Development** (All agents work simultaneously):
```bash
python demo_collaboration.py parallel
```

**Intensive Collaboration** (Constant code sharing and review):
```bash
python demo_collaboration.py pair_programming
```

**Custom Collaboration Style**:
```bash
python demo_collaboration.py "UI agent leads, others assist and follow"
```

## 📋 How Collaboration Prompts Work

### 1. **Prompt Definition**
You define how agents should work together:

```yaml
collaboration_prompt: |
  Agents should work in strict sequential order:
  1. Data Agent builds complete foundation first
  2. Audio Agent implements features second
  3. UI Agent creates interface last

  Rules: Each agent waits for previous to complete fully
```

### 2. **Intelligent Task Delegation**
The system analyzes your prompt and creates appropriate phases:

```
🤝 Delegating Tasks Based on Collaboration Prompt...
   📊 Task delegation strategy: prompt-based
   👥 Agent assignments based on collaboration rules
   • Data_Agent: 6 tasks (data models, state mgmt, storage)
   • Audio_Agent: 6 tasks (audio service, streaming, controls)
   • UI_Agent: 6 tasks (screens, navigation, theme)
```

### 3. **Agent Adaptation**
Agents adapt their behavior to follow collaboration rules:
- **Sequential**: Agents wait for previous completion
- **Parallel**: All agents start immediately
- **Collaborative**: Intensive code sharing and review

## 🎵 Flutter Music App Output

The agents collaboratively generate a complete Flutter music streaming app:

```
flutter_music_app_workspace/
├── lib/
│   ├── main.dart                    # App entry point
│   ├── models/
│   │   ├── track.dart              # Music track model
│   │   ├── playlist.dart           # Playlist model
│   │   └── user_preferences.dart   # Settings model
│   ├── services/
│   │   ├── audio_service.dart      # Core audio playback
│   │   ├── streaming_service.dart  # Music streaming
│   │   └── storage_service.dart    # Local data storage
│   ├── screens/
│   │   ├── home_screen.dart        # Main music browser
│   │   ├── player_screen.dart      # Now playing
│   │   └── search_screen.dart      # Music search
│   ├── widgets/
│   │   ├── player_controls.dart    # Audio controls
│   │   └── track_tile.dart         # Track display
│   └── utils/
│       ├── theme.dart              # Material Design 3
│       └── app_router.dart         # Navigation
└── pubspec.yaml                     # Dependencies
```

## 🔧 Example Collaboration Prompts

### Data-First Approach
```
"Data Agent builds complete architecture first, then Audio Agent implements services, finally UI Agent creates polished interface"
```

### UI-Led Development
```
"UI Agent creates mockups and interfaces first, other agents implement backend to match UI requirements"
```

### Competitive Development
```
"Each agent tries to implement as many features as possible, overlap encouraged to compare approaches"
```

### Pair Programming Style
```
"Agents work in pairs with intensive code review - UI+Data pair on integration, Audio reviews all code"
```

## 📊 Monitoring Collaboration

### Progress Board Updates
```
📋 Recent Team Activity:
- Flutter_Data_Agent: Created Track and Playlist models
- Flutter_Audio_Agent: Shared AudioService interface
- Flutter_UI_Agent: Implemented Material Design 3 theme
- Flutter_Data_Agent: Requesting help with state management
- Flutter_Audio_Agent: Providing state management code example
```

### Real-Time Phase Execution
```
🔄 Phase 1: Data Architecture & Setup...
   Type: Sequential
   Agents: Flutter_Data_Agent
   ✅ Flutter_Data_Agent: completed - 4 deliverables

🎵 Phase 2: Core Services & Audio...
   Type: Sequential
   Agents: Flutter_Audio_Agent
   ✅ Flutter_Audio_Agent: completed - 3 deliverables
```

## 🎯 Key Benefits

1. **Flexible Collaboration**: Define any collaboration style you want
2. **Real AI Code Generation**: No templates - actual LLM-generated Flutter code
3. **Intelligent Delegation**: Automatic task distribution based on prompt
4. **Complete Deliverables**: Functional Flutter app as output
5. **Audit Trail**: Full record of agent collaboration and decisions

## 🧪 Try It Yourself

1. **Start with a preset pattern**: `python demo_collaboration.py sequential`
2. **Try a custom style**: `python demo_collaboration.py "your collaboration idea"`
3. **Check the generated app**: Look in `flutter_music_app_workspace/`
4. **Review collaboration logs**: Check the progress board JSON file

The agents will adapt to **any** collaboration style you define!
