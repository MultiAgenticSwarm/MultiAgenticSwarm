import os
import json
from typing import Optional, Dict, Any
from multiagenticswarm.core.prompt_schemas import DEFAULT_FUNCTION_SCHEMA


class LLMWorkflowConfig:
    """Configuration holder for workflow parsing and LLM interaction."""

    def __init__(
        self,
        schema: Dict[str, Any] = DEFAULT_FUNCTION_SCHEMA,
        example_input: Optional[str] = None,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        system_prompt: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        self.schema = schema
        metadata = schema.get("metadata", {})

        # Provider/model
        self.provider = provider or metadata.get("default_provider", "groq")
        self.model_name = model_name or metadata.get("default_model", "llama3-8b-8192")

        # System prompt
        self._explicit_system_prompt = system_prompt or metadata.get("system_prompt")

        # Example input
        self.example_input = example_input or "Agent A and Agent B work in parallel, then Agent C reviews both outputs."

        # API key
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        if not self.api_key:
            raise RuntimeError("Missing LLM API key")

        self.log_level = os.getenv("MAS_LOG_LEVEL", "INFO")

    @property
    def system_prompt(self) -> str:
        if self._explicit_system_prompt:
            return self._explicit_system_prompt

        schema_json = json.dumps(self.schema.get("parameters", {}), indent=2)
        return f"""
You are an expert workflow parser for multi-agent collaboration systems.


Return ONLY a JSON with the exact structure below. Do NOT add explanations or extra fields.

Structure:
{{
  "phases": [
    {{
      "pattern": "parallel" | "sequential",
      "agents": ["Agent Names"],
      "duration": "until_complete",
      "conditions": ["optional conditions"]
    }}
  ],
  "rules": [
    {{
      "type": "conditional_loop",
      "condition": "condition description",
      "action": "what to do when condition occurs"
    }}
  ],
  "dependencies": {{
    "Agent Name": ["Dependent Agents"]
  }},
  "roles": {{
    "Agent Name": "Role description"
  }},
  "notes": "Optional notes about assumptions or missing info"
}}

Example (this is how I want you to give me output JSON and also see the object names carefully):
Input: "UI and Backend agents work in parallel, then QA agent reviews both outputs. If issues found, relevant agent fixes them"
Output:
{{
  "phases": [
    {{
      "pattern": "parallel",
      "agents": ["UI", "Backend"],
      "duration": "until_complete"
    }},
    {{
      "pattern": "sequential",
      "agents": ["QA"],
      "conditions": ["all_previous_complete"]
    }}
  ],
  "rules": [
    {{
      "type": "conditional_loop",
      "condition": "issues_found",
      "action": "return_to_relevant_agent"
    }}
  ],
  "dependencies": {{
    "QA": ["UI", "Backend"]
  }},
  "roles": {{
    "UI": "Interface development",
    "Backend": "API and data",
    "QA": "Quality validation"
  }}
}}
should not include the text or anything that violates the json format.
Keep it ensure that you are strickly following the default functional schema as it is base schema for prompt parser .
keep the names as in default function scheme like phases, rules, dependencies, roles and notes.
Return ONLY valid JSON.

"""