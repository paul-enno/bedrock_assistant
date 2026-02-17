"""Wrapper for strands.Agent to make it easier to test and implement."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any

from botocore.exceptions import ClientError
from strands import Agent
from strands.models import BedrockModel

from homeassistant.exceptions import HomeAssistantError

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
            user_id: User ID for memory isolation
        """
        self.hass = hass
        self.aws_factory = aws_factory
        self.system_prompt = system_prompt
        self.session_id = session_id
        self.storage_dir = storage_dir
        self.model_id = model_id
        self.enable_memory = enable_memory and MEM0_AVAILABLE
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

    def _get_enhanced_system_prompt(self, user_id: str | None = None) -> str:
        """Get system prompt enhanced with memory instructions.
        
        Args:
            user_id: Optional user ID to include in memory instructions
            
        Returns:
            Enhanced system prompt with memory instructions
        """
        base_prompt = self.system_prompt or ""
        
        if not self.enable_memory:
            return base_prompt
        
        # Use provided user_id or fall back to wrapper's user_id
        effective_user_id = user_id or self.user_id
        
        memory_instructions = f"""

You have access to a long-term memory system that persists across conversations. Use the memory tool to:
- Store important information about the user (preferences, facts, context)
- Retrieve relevant memories to provide personalized responses
- Remember user preferences and past interactions

IMPORTANT: When using the memory tool, always use user_id="{effective_user_id}" to ensure memories are stored and retrieved for the correct user.

When users share important information, proactively store it in memory. When answering questions, retrieve relevant memories to provide contextual, personalized responses."""
        
        return base_prompt + memory_instructions

    def get_agent_with_memory(self, conversation_id: str, user_id: str) -> Agent:
        """Get or create an agent with mem0 memory for a specific conversation.
        
        With mem0, the agent has access to long-term semantic memory that:
        - Persists across all conversations for this user
        - Automatically stores and retrieves relevant information
        - Provides semantic search based on meaning, not just keywords
        
        Args:
            conversation_id: Unique identifier for the conversation (used for caching)
            user_id: Home Assistant user ID for memory isolation
            
        Returns:
            Agent instance with mem0_memory tool configured for this user
        """
        # Create cache key combining conversation and user
        cache_key = f"{conversation_id}_{user_id}"
        
        # Return cached agent if it exists
        if cache_key in self._agent_cache:
            _LOGGER.debug("Using cached agent for conversation: %s, user: %s", conversation_id, user_id)
            return self._agent_cache[cache_key]

        # Create new agent with mem0 memory tool
        _LOGGER.debug(
            "Creating new agent with mem0 memory for user: %s, conversation: %s",
            user_id,
            conversation_id
        )
        
        bedrock_model = self._create_bedrock_model()

        # Create agent with enhanced system prompt that includes user_id context
        system_prompt = self._get_enhanced_system_prompt(user_id)
        
        agent = Agent(
            model=bedrock_model,
            tools=self.tools,  # Includes mem0_memory if available
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
                agent = self.get_agent_with_memory(conversation_id, effective_user_id)
                _LOGGER.debug(
                    "Using agent with mem0 memory for user: %s, conversation: %s",
                    effective_user_id,
                    conversation_id
                )
            else:
                # Create default agent without memory if not cached
                if self.agent is None:
                    bedrock_model = self._create_bedrock_model()
                    self.agent = Agent(
                        model=bedrock_model,
                        system_prompt=self.system_prompt,
                        callback_handler=None,
                    )
                agent = self.agent
                _LOGGER.debug("Using agent without memory")
            
            response = await self.hass.async_add_executor_job(agent, prompt)
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
