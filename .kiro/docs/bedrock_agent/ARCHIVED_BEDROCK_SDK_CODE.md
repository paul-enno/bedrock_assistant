# Archived Bedrock SDK Code

This file contains the original Bedrock SDK implementation that was replaced by the Strands SDK.
This code is preserved for potential future revival or reference.

## Overview

The original implementation supported:
- Direct Bedrock Agent invocation via `bedrock-agent-runtime` SDK
- Knowledge Base integration  
- Agent ID and Alias ID configuration

This was replaced with Strands SDK which provides:
- Better tool integration
- Memory management with Mem0
- Simplified agent management

## Archived Code

### Constants (from const.py)

```python
CONST_KNOWLEDGEBASE_ID: Final = "knowledgebase_id"
CONST_AGENT_ID: Final = "agent_id"
CONST_AGENT_ALIAS_ID: Final = "agent_alias_id"
```

### AWS Client Factory Method (from aws_client.py)

```python
async def create_bedrock_agent_client(self) -> Any:
    """Create a Bedrock Agent Runtime client."""
    return await self.hass.async_add_executor_job(
        partial(
            boto3.client,
            service_name="bedrock-agent-runtime",
            region_name=self.region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        )
    )
```

### Agent Methods (from agent.py)

```python
# In __init__:
# Initialize bedrock agent client (for custom agents) - will be awaited later
self._bedrock_agent_client = None

async def async_call_bedrock_agent(
    self, user_input: agent_manager.ConversationInput, question: str
) -> str:
    """Call a custom Bedrock Agent."""
    config_agent_id = self.entry.options.get(CONST_AGENT_ID) or ""
    config_agent_alias_id = (
        self.entry.options.get(CONST_AGENT_ALIAS_ID) or "TSTALIASID"
    )

    # Lazy initialize the bedrock agent client
    if self._bedrock_agent_client is None:
        self._bedrock_agent_client = (
            await self.aws_factory.create_bedrock_agent_client()
        )

    bedrock_agent_client = self._bedrock_agent_client

    bedrock_agent_response = await self.hass.async_add_executor_job(
        partial(
            bedrock_agent_client.invoke_agent,
            agentId=config_agent_id,
            agentAliasId=config_agent_alias_id,
            sessionId=user_input.conversation_id,
            inputText=question,
        ),
    )

    completion = ""
    for event in bedrock_agent_response.get("completion"):
        chunk = event["chunk"]
        completion = completion + chunk["bytes"].decode()

    return completion

# In async_call_bedrock:
config_agent_id = self.entry.options.get(CONST_AGENT_ID) or ""

if config_agent_id != "":
    return await self.async_call_bedrock_agent(user_input, question)
```

### Config Flow Functions (from config_flow.py)

```python
async def get_knowledgebases_selectOptionDict(
    hass: HomeAssistant, data: dict[str, Any]
) -> Sequence[selector.SelectOptionDict]:
    """Return available knowledgebases."""

    bedrock_agent = boto3.client(
        service_name="bedrock-agent",
        region_name=data.get(CONST_REGION),
        aws_access_key_id=data.get(CONST_KEY_ID),
        aws_secret_access_key=data.get(CONST_KEY_SECRET),
    )

    response = await hass.async_add_executor_job(bedrock_agent.list_knowledge_bases)
    knowledgebases = response.get("knowledgeBaseSummaries")
    knowledgebases_list = [
        selector.SelectOptionDict(
            {"value": k.get("knowledgeBaseId"), "label": k.get("name")}
        )
        for k in knowledgebases
    ]
    knowledgebases_list.insert(
        0, selector.SelectOptionDict({"value": "", "label": "None"})
    )

    return knowledgebases_list


async def get_agents_selectOptionDict(
    hass: HomeAssistant, data: dict[str, Any]
) -> Sequence[selector.SelectOptionDict]:
    """Return available agents."""

    bedrock_agent = boto3.client(
        service_name="bedrock-agent",
        region_name=data.get(CONST_REGION),
        aws_access_key_id=data.get(CONST_KEY_ID),
        aws_secret_access_key=data.get(CONST_KEY_SECRET),
    )

    response = await hass.async_add_executor_job(bedrock_agent.list_agents)
    agents = response.get("agentSummaries")
    agents_list = [
        selector.SelectOptionDict(
            {"value": a.get("agentId"), "label": a.get("agentName")}
        )
        for a in agents
    ]
    agents_list.insert(0, selector.SelectOptionDict({"value": "", "label": "None"}))

    return agents_list
```

## Date Archived

February 18, 2026
