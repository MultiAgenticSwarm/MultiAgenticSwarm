import pytest
import json
import asyncio
from multiagenticswarm.core.prompt_parser import PromptParser, BaseLLM
from config.settings import LLMWorkflowConfig


class DummyLLM(BaseLLM):
    async def generate(self, messages):
        return json.dumps({
            "phases": [
                {"pattern": "parallel", "agents": ["UI", "Backend"], "duration": "until_complete"},
                {"pattern": "sequential", "agents": ["QA"], "conditions": ["all_previous_complete"]}
            ],
            "rules": [{"type": "conditional_loop", "condition": "issues_found", "action": "return_to_relevant_agent"}],
            "dependencies": {"QA": ["UI", "Backend"]},
            "roles": {"UI": "Interface development", "Backend": "API and data", "QA": "Quality validation"}
        })


@pytest.mark.asyncio
async def test_prompt_parser_returns_valid_json():
    config = LLMWorkflowConfig(api_key="dummy-key")
    parser = PromptParser(DummyLLM(), config)

    result = await parser.parse("UI and Backend work in parallel, QA validates.")
    
    assert isinstance(result, dict)
    assert "phases" in result
    assert isinstance(result["phases"], list)
    assert result["phases"][0]["pattern"] in ["parallel", "sequential"]
    assert all(isinstance(agent, str) for agent in result["phases"][0]["agents"])
