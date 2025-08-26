# multiagenticswarm/core/prompt_schemas.py

DEFAULT_FUNCTION_SCHEMA = {
    "name": "extract_collaboration_workflow",
    "description": "Extract structured workflow info from a natural language collaboration prompt",
    "parameters": {
        "type": "object",
        "properties": {
            "phases": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "enum": ["parallel", "sequential", "conditional", "loop"]
                        },
                        "agents": {"type": "array", "items": {"type": "string"}},
                        "duration": {
                            "type": "string",
                            "enum": ["until_complete", "fixed_time", "conditional", "ongoing"]
                        },
                        "conditions": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["pattern", "agents", "duration"]
                }
            },
            "rules": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["conditional_loop", "dependency", "validation", "retry"]
                        },
                        "condition": {"type": "string"},
                        "action": {"type": "string"}
                    },
                    "required": ["type", "condition", "action"]
                }
            },
            "dependencies": {
                "type": "object",
                "additionalProperties": {"type": "array", "items": {"type": "string"}}
            },
            "roles": {
                "type": "object",
                "additionalProperties": {"type": "string"}
            }
        },
        "required": ["phases", "rules", "dependencies", "roles"]
    }
}

ROLE_MAPPINGS = {
    'ui': 'Interface development and user experience',
    'frontend': 'Frontend development and user interface',
    'backend': 'API development and data processing',
    'qa': 'Quality validation and testing',
    'testing': 'Quality assurance and validation',
    'review': 'Code review and quality control',
    'database': 'Data storage and management',
    'api': 'API development and integration',
    'security': 'Security validation and compliance'
}
