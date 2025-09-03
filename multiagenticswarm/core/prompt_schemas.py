DEFAULT_FUNCTION_SCHEMA = {
    "name": "workflow_schema",
    "description": "Schema for structured multi-agent workflows",
    "parameters": {
        "type": "object",
        "properties": {
            "phases": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "pattern": {"type": "string", "enum": ["parallel", "sequential"]},
                        "agents": {"type": "array", "items": {"type": "string"}},
                        "duration": {"type": "string"},
                        "conditions": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["pattern", "agents", "duration", "conditions"]
                }
            },
            "rules": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string"},
                        "condition": {"type": "string"},
                        "action": {"type": "string"}
                    },
                    "required": ["type", "condition", "action"]
                }
            },
            "dependencies": {
                "type": "object",
                "additionalProperties": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "roles": {
                "type": "object",
                "additionalProperties": {"type": "string"}
            }
        },
        "required": ["phases", "rules", "dependencies", "roles"]
    },
    "metadata": {
        "default_provider": "groq",
        "default_model": "llama3-8b-8192",
        "system_prompt": "You are an expert workflow parser... Return ONLY valid JSON."
    }
}
