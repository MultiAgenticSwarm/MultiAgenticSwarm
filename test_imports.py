#!/usr/bin/env python3
"""
Simple demonstration of MultiAgenticSwarm import styles.
This shows different ways users can import and use the package.
"""

print("🔍 Testing MultiAgenticSwarm Package Import Styles\n")

# Method 1: Import the whole package with alias
print("📦 Method 1: Import as alias")
try:
    import multiagenticswarm as mas
    print(f"✅ Successfully imported MultiAgenticSwarm v{mas.__version__}")
    print(f"   Available components: {len(mas.__all__)} items")
    
    # Create an agent using the alias
    agent = mas.Agent(
        name="TestAgent",
        description="Test agent for import demo",
        system_prompt="You are a helpful test agent.",
        llm_provider="openai",
        llm_model="gpt-3.5-turbo"
    )
    print(f"✅ Created agent: {agent.name}")
    
except Exception as e:
    print(f"❌ Error with Method 1: {e}")

print()

# Method 2: Import specific components
print("📦 Method 2: Import specific components")
try:
    from multiagenticswarm import Agent, Tool, System
    print("✅ Successfully imported Agent, Tool, System")
    
    # Create components using direct imports
    agent2 = Agent(
        name="DirectAgent",
        description="Agent created with direct import",
        system_prompt="You are directly imported.",
        llm_provider="openai",
        llm_model="gpt-3.5-turbo"
    )
    
    system = System()
    system.register_agents(agent2)
    print(f"✅ Created system with {len(system.agents)} agent(s)")
    
except Exception as e:
    print(f"❌ Error with Method 2: {e}")

print()

# Method 3: Show CLI availability
print("📦 Method 3: CLI Command")
try:
    import subprocess
    result = subprocess.run(['multiagenticswarm', '--help'], 
                          capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        print("✅ CLI command 'multiagenticswarm' is available")
        print("   Usage: multiagenticswarm --help")
    else:
        print("❌ CLI command failed")
except Exception as e:
    print(f"❌ Error testing CLI: {e}")

print()

# Method 4: Show package info
print("📦 Method 4: Package Information")
try:
    import multiagenticswarm
    print(f"✅ Package: {multiagenticswarm.__name__}")
    print(f"   Version: {multiagenticswarm.__version__}")
    print(f"   Author: {multiagenticswarm.__author__}")
    print(f"   All exports: {multiagenticswarm.__all__}")
    
except Exception as e:
    print(f"❌ Error getting package info: {e}")

print("\n🎉 MultiAgenticSwarm package import test completed!")
print("\n💡 Usage Examples:")
print("   import multiagenticswarm as mas")
print("   from multiagenticswarm import Agent, System")
print("   multiagenticswarm --config myconfig.yaml")
