"""Custom tool module for Strands SDK agent."""

TOOL_SPEC = {
    "name": "process_text",
    "description": "Process text with multiple parameters",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Input text to process"
                },
                "count": {
                    "type": "integer",
                    "description": "Number of times to repeat",
                    "default": 1
                },
                "prefix": {
                    "type": "string",
                    "description": "Prefix to add",
                    "default": ""
                }
            },
            "required": ["text"]
        }
    }
}

def process_text(tool, **kwargs):
    """Process text with configurable parameters."""
    tool_use_id = tool["toolUseId"]
    tool_input = tool["input"]

    text = tool_input.get("text", "")
    count = tool_input.get("count", 1)
    prefix = tool_input.get("prefix", "")

    result = (text + " ") * count
    final_result = f"{prefix}{result.strip()}"

    return {
        "toolUseId": tool_use_id,
        "status": "success",
        "content": [{"text": final_result}]
    }