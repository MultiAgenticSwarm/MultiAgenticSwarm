# multiagenticswarm/core/prompt_parser.py
import json
import os
import re
from typing import Any, Callable, Dict, Optional

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

# Load environment variables
load_dotenv()

# Import schema + role mappings
from prompt_schemas import DEFAULT_FUNCTION_SCHEMA, ROLE_MAPPINGS

print(DEFAULT_FUNCTION_SCHEMA)
print(ROLE_MAPPINGS)


# FUNCTION CALL PROMPT BUILDER
def build_enhanced_function_call_prompt(prompt: str):
    system_content = f"""You are an expert workflow parser for multi-agent collaboration systems.

Your task is to extract structured workflow information from natural language prompts.

IMPORTANT GUIDELINES:
1. **Phases**: Identify collaboration patterns (parallel, sequential, conditional, loop)
2. **Duration**: Use meaningful durations like "until_complete", not generic times
3. **Rules**: Extract conditional logic, feedback loops, and validation rules
4. **Dependencies**: Map which agents depend on others' completion
5. **Roles**: Infer agent responsibilities from context

PATTERN EXAMPLES:
- "A and B work in parallel" → pattern: "parallel"
- "then C reviews" → pattern: "sequential"
- "if issues found, return to relevant agent" → rule: conditional_loop
- "QA reviews both outputs" → dependencies: QA depends on previous agents

SCHEMA TO FOLLOW:
{json.dumps(DEFAULT_FUNCTION_SCHEMA['parameters'], indent=2)}

EXAMPLE INPUT: "UI and Backend agents work in parallel, then QA agent reviews both outputs. If issues found, relevant agent fixes them."

EXAMPLE OUTPUT:
{{
  "phases": [
    {{
      "pattern": "parallel",
      "agents": ["UI", "Backend"],
      "duration": "until_complete",
      "conditions": []
    }},
    {{
      "pattern": "sequential",
      "agents": ["QA"],
      "duration": "until_complete",
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
    "Backend": "API and data processing",
    "QA": "Quality validation and testing"
  }}
}}

Return ONLY valid JSON matching the schema. No explanations."""

    return [
        SystemMessage(content=system_content),
        HumanMessage(content=f"Parse this collaboration prompt: {prompt}"),
    ]


# ENHANCED HEURISTIC PARSER
def heuristic_parse(prompt: str) -> Dict[str, Any]:
    """Enhanced fallback parser with regex + role mappings"""
    agents = re.findall(
        r"\b([A-Z][A-Za-z]*)\s+(?:agent|team|developer)", prompt, re.IGNORECASE
    )
    if not agents:
        agents = re.findall(
            r"\b(frontend|backend|UI|QA|testing|database|api|security)\b",
            prompt,
            re.IGNORECASE,
        )

    agents = [agent.title() for agent in agents]
    phases, dependencies, rules = [], {}, []

    # Parallel detection
    if re.search(
        r"\b(parallel|simultaneously|at the same time)\b", prompt, re.IGNORECASE
    ):
        if len(agents) >= 2:
            phases.append(
                {
                    "pattern": "parallel",
                    "agents": agents[:2],
                    "duration": "until_complete",
                    "conditions": [],
                }
            )

    # Sequential detection
    if re.search(r"\b(then|after|once|following)\b", prompt, re.IGNORECASE):
        remaining_agents = [
            a for a in agents if not phases or a not in phases[0].get("agents", [])
        ]
        if remaining_agents:
            seq_agent = remaining_agents[0]
            phases.append(
                {
                    "pattern": "sequential",
                    "agents": [seq_agent],
                    "duration": "until_complete",
                    "conditions": ["all_previous_complete"],
                }
            )
            dependencies[seq_agent] = (
                phases[0]["agents"]
                if phases and phases[0]["pattern"] == "parallel"
                else []
            )

    # Conditional rules
    if re.search(
        r"\b(if.*issues?.*found|if.*problems?|when.*errors?)\b", prompt, re.IGNORECASE
    ):
        rules.append(
            {
                "type": "conditional_loop",
                "condition": "issues_found",
                "action": "return_to_relevant_agent",
            }
        )

    # Role mapping
    roles = {}
    for agent in agents:
        roles[agent] = ROLE_MAPPINGS.get(
            agent.lower(), f"{agent} development and implementation"
        )

    return {
        "phases": phases,
        "rules": rules,
        "dependencies": dependencies,
        "roles": roles,
    }


# LLM CALLER USING LANGCHAIN + GROQ
def groq_langchain_caller(messages):
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # ✅ now from .env
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set in .env file")

    llm = ChatGroq(
        temperature=0.1, model_name="llama3-8b-8192", api_key=GROQ_API_KEY, verbose=True
    )
    try:
        response = llm.invoke(messages)
        content = response.content.strip()

        # clean JSON
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        result_json = json.loads(content.strip())
        return {"arguments": result_json}
    except Exception as e:
        print(f"[ERROR] LLM call failed: {e}")
        return None


# MAIN PARSING FUNCTION
def parse_collaboration_prompt(
    prompt: str, llm_caller: Optional[Callable] = None
) -> Dict[str, Any]:
    if llm_caller:
        try:
            messages = build_enhanced_function_call_prompt(prompt)
            result = llm_caller(messages)
            if result and "arguments" in result:
                args = result["arguments"]
                if all(k in args for k in ["phases", "rules", "dependencies", "roles"]):
                    return args
                print("[WARN] LLM result missing fields, fallback used")
        except Exception as e:
            print(f"[WARN] LLM parsing failed: {e}")

    print("[INFO] Using heuristic parser")
    return heuristic_parse(prompt)


# VALIDATION FUNCTION
def validate_workflow_spec(spec: Dict[str, Any]) -> bool:
    required_keys = ["phases", "rules", "dependencies", "roles"]
    if not all(k in spec for k in required_keys):
        return False
    for phase in spec["phases"]:
        if not all(k in phase for k in ["pattern", "agents", "duration"]):
            return False
        if phase["pattern"] not in ["parallel", "sequential", "conditional", "loop"]:
            return False
    return True


# TEST HARNESS
if __name__ == "__main__":
    # Use only one test prompt
    prompt = "UI and Backend agents work in parallel, then QA agent reviews both outputs. If issues found, relevant agent fixes them."

    print(f"\n=== TEST ===\nInput: {prompt}")

    spec = parse_collaboration_prompt(prompt, llm_caller=groq_langchain_caller)

    # Print output
    print(json.dumps(spec, indent=2))
    print("✅ Valid" if validate_workflow_spec(spec) else "❌ Invalid")

    # Save output to file
    output_file = "workflow_output.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2)

    print(f"\nJSON output saved to {output_file}")
