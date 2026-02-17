"""Wrapper for strands.Agent to make it easier to test and implement."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any

from botocore.exceptions import ClientError
from strands import Agent
from strands.models import BedrockModel

from homeassistant.exceptions import HomeAssistantError

from .ha_control_tool import create_ha_control_tool, TOOL_SPEC as HA_CONTROL_TOOL_SPEC

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.llm import API, LLMContext

    from .aws_client import AWSClientFactory

# Configure the root strands logger
logging.getLogger("strands").setLevel(logging.ERROR)

_LOGGER = logging.getLogger(__name__)

# Try to import mem0_memory tool and check dependencies
MEM0_AVAILABLE = False
MEM0_ERROR_MESSAGE = None

try:
    from strands_tools import mem0_memory
    
    # Check if faiss is available (required by mem0)
    try:
        import faiss  # noqa: F401
        MEM0_AVAILABLE = True
    except ImportError:
        MEM0_ERROR_MESSAGE = "faiss-cpu not available. Install with: pip install faiss-cpu"
        _LOGGER.warning(
            "mem0_memory tool requires faiss-cpu. Install with: pip install faiss-cpu"
        )
except ImportError:
    MEM0_ERROR_MESSAGE = "mem0_memory tool not available. Install with: pip install 'strands-agents-tools[mem0_memory]'"
    _LOGGER.warning(
        "mem0_memory tool not available. Install with: pip install 'strands-agents-tools[mem0_memory]'"
    )


class StrandsAgentWrapper:
    """Wrapper for strands.Agent to make it easier to test and implement."""

    def __init__(
        self,
        hass: HomeAssistant,
        aws_factory: AWSClientFactory,
        model_id: str,
        apis: list[API],
        system_prompt: str | None = "",
        session_id: str | None = None,
        storage_dir: str = "/tmp/strands",  # noqa: S108
        enable_memory: bool = True,
        enable_ha_control: bool = True,
        user_id: str | None = None,
    ) -> None:
        """Initialize the wrapper.
        
        Args:
            hass: Home Assistant instance
            aws_factory: AWS client factory
            model_id: Bedrock model ID
            apis: List of Home Assistant APIs
            system_prompt: System prompt for the agent
            session_id: Session ID (deprecated, use conversation_id)
            storage_dir: Storage directory (deprecated with mem0)
            enable_memory: Enable long-term memory with mem0
            enable_ha_control: Enable Home Assistant device control
            user_id: User ID for memory isolation
        """
        self.hass = hass
        self.aws_factory = aws_factory
        self.system_prompt = system_prompt
        self.session_id = session_id
        self.storage_dir = storage_dir
        self.model_id = model_id
        self.enable_memory = enable_memory and MEM0_AVAILABLE
        self.enable_ha_control = enable_ha_control
        self.user_id = user_id or "default_user"

        self.tools = []
        self.apis = apis
        self.api_instances = {}
        self.llm_context = None
        self.modules = {}

        # Configure AWS credentials for mem0 if memory is enabled
        if self.enable_memory:
            self._configure_mem0_credentials()
            self.tools.append(mem0_memory)
            _LOGGER.info("Mem0 memory enabled for long-term semantic memory")
        else:
            if not MEM0_AVAILABLE:
                _LOGGER.warning("Memory disabled: mem0_memory tool not available")

        # Log Home Assistant control status
        if self.enable_ha_control:
            if self.apis:
                _LOGGER.info("Home Assistant control enabled with %d APIs", len(self.apis))
            else:
                _LOGGER.warning("Home Assistant control enabled but no APIs available")
        else:
            _LOGGER.info("Home Assistant control disabled by configuration")

        # Cache of agents per conversation ID
        self._agent_cache: dict[str, Agent] = {}

        # Default agent (created on first use)
        self.agent = None

    def _configure_mem0_credentials(self) -> None:
        """Configure AWS credentials for mem0 via environment variables.
        
        Mem0 uses environment variables for AWS credentials. We set them here
        to ensure mem0 can access Bedrock for embeddings and LLM operations.
        """
        # Set AWS credentials if not already set
        if not os.environ.get("AWS_ACCESS_KEY_ID"):
            os.environ["AWS_ACCESS_KEY_ID"] = self.aws_factory.aws_access_key_id
            _LOGGER.debug("Set AWS_ACCESS_KEY_ID for mem0")
        
        if not os.environ.get("AWS_SECRET_ACCESS_KEY"):
            os.environ["AWS_SECRET_ACCESS_KEY"] = self.aws_factory.aws_secret_access_key
            _LOGGER.debug("Set AWS_SECRET_ACCESS_KEY for mem0")
        
        if not os.environ.get("AWS_REGION"):
            os.environ["AWS_REGION"] = self.aws_factory.region_name
            _LOGGER.debug("Set AWS_REGION for mem0: %s", self.aws_factory.region_name)
        
        # Configure mem0 to use Bedrock for embeddings and LLM
        # These can be overridden by user if they set them explicitly
        if not os.environ.get("MEM0_EMBEDDER_PROVIDER"):
            os.environ["MEM0_EMBEDDER_PROVIDER"] = "aws_bedrock"
        
        if not os.environ.get("MEM0_EMBEDDER_MODEL"):
            os.environ["MEM0_EMBEDDER_MODEL"] = "amazon.titan-embed-text-v2:0"
        
        if not os.environ.get("MEM0_LLM_PROVIDER"):
            os.environ["MEM0_LLM_PROVIDER"] = "aws_bedrock"
        
        if not os.environ.get("MEM0_LLM_MODEL"):
            os.environ["MEM0_LLM_MODEL"] = "anthropic.claude-3-5-haiku-20241022-v1:0"
        
        _LOGGER.info(
            "Configured mem0 with AWS Bedrock: embedder=%s, llm=%s, region=%s",
            os.environ.get("MEM0_EMBEDDER_MODEL"),
            os.environ.get("MEM0_LLM_MODEL"),
            os.environ.get("AWS_REGION")
        )


    def _create_bedrock_model(self) -> BedrockModel:
        """Create a Bedrock model instance."""
        session = self.aws_factory.create_boto3_session()
        return BedrockModel(
            model_id=self.model_id,
            boto_session=session,
            streaming=False,
        )

    def _get_enhanced_system_prompt(self, user_id: str | None = None, has_ha_control: bool = False) -> str:
        """Get system prompt enhanced with memory and HA control instructions.
        
        Args:
            user_id: Optional user ID to include in memory instructions
            has_ha_control: Whether Home Assistant control is available
            
        Returns:
            Enhanced system prompt with memory and HA control instructions
        """
        base_prompt = self.system_prompt or ""
        
        enhancements = []
        
        # Add memory instructions if enabled
        if self.enable_memory:
            effective_user_id = user_id or self.user_id
            enhancements.append(f"""

You have access to a long-term memory system that persists across conversations. Use the memory tool to:
- Store important information about the user (preferences, facts, context)
- Retrieve relevant memories to provide personalized responses
- Remember user preferences and past interactions

IMPORTANT: When using the memory tool, always use user_id="{effective_user_id}" to ensure memories are stored and retrieved for the correct user.

When users share important information, proactively store it in memory. When answering questions, retrieve relevant memories to provide contextual, personalized responses.""")
        
        # Add Home Assistant control instructions if available
        if has_ha_control:
            enhancements.append("""

You have access to Home Assistant smart home control through the homeassistant_control tool.

CRITICAL RULES FOR USING homeassistant_control:
1. The tool requires TWO parameters for most operations:
   - tool_name: The intent name (e.g., "HassTurnOn", "HassGetState")
   - name: The device name (e.g., "kitchen light", "bedroom fan")

2. ALWAYS provide the 'name' parameter when using these intents:
   - HassTurnOn, HassTurnOff, HassToggle
   - HassGetState
   - HassLightSet
   - HassSetPosition
   - HassMediaUnpause, HassMediaPause, HassMediaNext, HassMediaPrevious
   - HassSetVolume

3. Only these intents work WITHOUT a 'name' parameter:
   - GetLiveContext (shows all devices)
   - GetDateTime (shows current time)

4. Optional parameters:
   - domain: Device type (e.g., "light", "switch", "fan") - helps identify the right device
   - brightness: For lights, 0-100
   - color: For lights, color name or value

5. SPECIAL CASES:
   - Scenes: Use the scene name directly as a tool if available, OR use HassTurnOn with the full entity_id (e.g., name="scene.ha_new")
   - Scripts: Use the script name directly as a tool if available
   - If a scene/script tool exists with the exact name, prefer using that tool directly

CORRECT EXAMPLES:
✓ homeassistant_control(tool_name="HassTurnOn", name="kitchen light", domain="light")
✓ homeassistant_control(tool_name="HassGetState", name="living room temperature")
✓ homeassistant_control(tool_name="GetLiveContext")
✓ homeassistant_control(tool_name="ha_new") - if ha_new is a scene/script tool
✓ homeassistant_control(tool_name="HassTurnOn", name="scene.ha_new") - activate scene by entity_id

WRONG EXAMPLES:
✗ homeassistant_control(tool_name="HassTurnOn") - Missing 'name' parameter!
✗ homeassistant_control(tool_name="HassTurnOn", domain="light") - Still missing 'name'!

If you get an error about "cannot target all devices", it means you forgot to provide the 'name' parameter.
If you get an error about "Failed to call turn_on", the device might not support that action - try checking available tools with GetLiveContext.""")
        
        return base_prompt + "".join(enhancements)

    async def get_agent_with_memory(self, conversation_id: str, user_id: str, llm_context: LLMContext | None = None) -> Agent:
        """Get or create an agent with mem0 memory for a specific conversation.
        
        With mem0, the agent has access to long-term semantic memory that:
        - Persists across all conversations for this user
        - Automatically stores and retrieves relevant information
        - Provides semantic search based on meaning, not just keywords
        
        Args:
            conversation_id: Unique identifier for the conversation (used for caching)
            user_id: Home Assistant user ID for memory isolation
            llm_context: LLM context for Home Assistant control
            
        Returns:
            Agent instance with mem0_memory tool and HA control configured for this user
        """
        # Create cache key combining conversation and user
        cache_key = f"{conversation_id}_{user_id}"
        
        # Return cached agent if it exists
        if cache_key in self._agent_cache:
            _LOGGER.debug("Using cached agent for conversation: %s, user: %s", conversation_id, user_id)
            return self._agent_cache[cache_key]

        # Create new agent with mem0 memory tool and HA control
        _LOGGER.debug(
            "Creating new agent with mem0 memory and HA control for user: %s, conversation: %s",
            user_id,
            conversation_id
        )
        
        bedrock_model = self._create_bedrock_model()

        # Build tools list
        agent_tools = list(self.tools)  # Start with mem0_memory if enabled
        
        # Add Home Assistant control tool if enabled, APIs available, and llm_context provided
        if self.enable_ha_control and self.apis and llm_context:
            ha_tool = await create_ha_control_tool(self.hass, self.apis, llm_context)
            agent_tools.append(ha_tool)
            _LOGGER.debug("Added Home Assistant control tool to agent")
        
        # Create agent with enhanced system prompt that includes user_id context
        system_prompt = self._get_enhanced_system_prompt(user_id, has_ha_control=bool(self.enable_ha_control and self.apis and llm_context))
        
        agent = Agent(
            model=bedrock_model,
            tools=agent_tools,
            system_prompt=system_prompt,
            callback_handler=None,
        )

        # Cache the agent with combined key
        self._agent_cache[cache_key] = agent
        return agent

    def clear_conversation_cache(self, conversation_id: str) -> None:
        """Clear cached agent for a specific conversation.
        
        Note: This only clears the agent cache, not the mem0 memories.
        Mem0 memories persist across conversations and must be cleared
        using the mem0 API directly if needed.
        
        Args:
            conversation_id: Unique identifier for the conversation to clear
        """
        if conversation_id in self._agent_cache:
            _LOGGER.debug("Clearing agent cache for conversation: %s", conversation_id)
            del self._agent_cache[conversation_id]

    def clear_all_cache(self) -> None:
        """Clear all cached agents.
        
        Note: This only clears the agent cache, not the mem0 memories.
        """
        _LOGGER.debug("Clearing all agent cache")
        self._agent_cache.clear()

    async def generate_response(
        self, 
        prompt: Any, 
        llm_context: LLMContext | None = None, 
        conversation_id: str | None = None,
        context_user_id: str | None = None,
    ) -> str:
        """Generate a response from the agent.
        
        When memory is enabled, the agent will automatically:
        - Store important information from the conversation
        - Retrieve relevant memories to provide context
        - Maintain long-term memory across all conversations
        
        Args:
            prompt: The prompt to send to the agent
            llm_context: Optional LLM context
            conversation_id: Optional conversation ID for agent caching
            context_user_id: Optional user ID from Home Assistant context
            
        Returns:
            The agent's response as a string
        """
        try:
            # Use agent with memory if conversation_id provided and memory enabled
            if conversation_id and self.enable_memory:
                # Use context user_id if available, otherwise fall back to wrapper user_id
                effective_user_id = context_user_id or self.user_id
                agent = await self.get_agent_with_memory(conversation_id, effective_user_id, llm_context)
                _LOGGER.debug(
                    "Using agent with mem0 memory for user: %s, conversation: %s",
                    effective_user_id,
                    conversation_id
                )
            else:
                # Create default agent without memory if not cached
                if self.agent is None:
                    bedrock_model = self._create_bedrock_model()
                    
                    # Build tools list for default agent
                    agent_tools = []
                    if self.enable_ha_control and self.apis and llm_context:
                        ha_tool = await create_ha_control_tool(self.hass, self.apis, llm_context)
                        agent_tools.append(ha_tool)
                    
                    self.agent = Agent(
                        model=bedrock_model,
                        tools=agent_tools,
                        system_prompt=self._get_enhanced_system_prompt(has_ha_control=bool(self.enable_ha_control and self.apis and llm_context)),
                        callback_handler=None,
                    )
                agent = self.agent
                _LOGGER.debug("Using agent without memory")
            
            # Call the agent asynchronously using invoke_async
            # This keeps us in the same event loop as Home Assistant
            response = await agent.invoke_async(prompt)
            return str(response)
        except ClientError as error:
            raise HomeAssistantError(
                f"Amazon Bedrock Error: `{error.response.get('Error').get('Message')}`"
            ) from error

    async def async_call_llm(
        self, 
        prompt: str, 
        llm_context: LLMContext, 
        conversation_id: str | None = None,
        context_user_id: str | None = None,
    ) -> str:
        """Call the agent with the given prompt.
        
        Args:
            prompt: The prompt to send to the agent
            llm_context: LLM context
            conversation_id: Optional conversation ID for agent caching
            context_user_id: Optional user ID from Home Assistant context
            
        Returns:
            The agent's response as a string
        """
        _LOGGER.debug("Calling LLM with prompt: %s", prompt)
        return await self.generate_response(prompt, llm_context, conversation_id, context_user_id)

    def get_memory_stats(self) -> dict[str, Any]:
        """Get memory statistics.
        
        Returns:
            Dictionary with memory statistics
        """
        stats = {
            "memory_enabled": self.enable_memory,
            "mem0_available": MEM0_AVAILABLE,
            "user_id": self.user_id,
            "cached_conversations": len(self._agent_cache),
            "tools_count": len(self.tools),
        }
        
        # Add error message if mem0 is not available
        if not MEM0_AVAILABLE and MEM0_ERROR_MESSAGE:
            stats["error"] = MEM0_ERROR_MESSAGE
        
        return stats
