import pytest
from multiagenticswarm.core.prompt_parser import parse_collaboration_prompt


def test_parse_collaboration_prompt_structure():
    prompt = "UI and Backend agents work in parallel, then QA agent reviews both outputs. If issues found, relevant agent fixes them."
    
    result = parse_collaboration_prompt(prompt)

    # Check top-level structure
    assert isinstance(result, dict)
    assert "phases" in result
    assert isinstance(result["phases"], list)
    assert len(result["phases"]) > 0

    # Check phase structure
    phase = result["phases"][0]
    assert "pattern" in phase
    assert "agents" in phase
    assert isinstance(phase["agents"], list)
    assert all(isinstance(agent, str) for agent in phase["agents"])

    # Ensure at least 2 agents are parsed
    assert len(phase["agents"]) >= 2

    # Ensure pattern is one of the allowed types
    assert phase["pattern"] in ["sequential", "parallel", "conditional"]
