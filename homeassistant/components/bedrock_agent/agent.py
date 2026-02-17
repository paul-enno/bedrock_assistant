"""Bedrock conversation agent implementation."""

from __future__ import annotations

from functools import partial
import logging
from typing import TYPE_CHECKING, Literal
import uuid

from homeassistant.components import conversation
from homeassistant.components.conversation import agent_manager
from homeassistant.const import MATCH_ALL
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import llm
from homeassistant.helpers.intent import IntentResponse, IntentResponseErrorCode

from .aws_client import AWSClientFactory
from .const import (
    CONST_AGENT_ALIAS_ID,
    CONST_AGENT_ID,
    CONST_KEY_ID,
    CONST_KEY_SECRET,
    CONST_MODEL_ID,
    CONST_MODEL_LIST,
    CONST_PROMPT_CONTEXT,
    CONST_REGION,
)
from .strands_wrapper import StrandsAgentWrapper

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class BedrockAgent(conversation.AbstractConversationAgent):
    """Bedrock conversation agent."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the agent."""
        self.hass = hass
        self.entry = entry
        self.history: dict[str, list[dict]] = {}

        # Create AWS client factory
        self.aws_factory = AWSClientFactory(
            hass=hass,
            aws_access_key_id=entry.data[CONST_KEY_ID],
            aws_secret_access_key=entry.data[CONST_KEY_SECRET],
            region_name=entry.data[CONST_REGION],
        )

        # Initialize bedrock agent client (for custom agents) - will be awaited later
        self._bedrock_agent_client = None

        # Initialize the strands agent wrapper
        self.strands_agent_wrapper = StrandsAgentWrapper(
            hass=self.hass,
            aws_factory=self.aws_factory,
            model_id=self.entry.options[CONST_MODEL_ID],
            apis=llm.async_get_apis(self.hass),
            system_prompt=self.entry.options[CONST_PROMPT_CONTEXT],
            user_id=entry.entry_id,  # Use entry_id as user identifier
        )

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return a list of supported languages."""
        return MATCH_ALL

    @staticmethod
    def supported_models() -> list[str]:
        """Return a list of supported models."""
        return CONST_MODEL_LIST

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
            self._bedrock_agent_client = await self.aws_factory.create_bedrock_agent_client()
        
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

    async def async_call_bedrock(
        self, user_input: agent_manager.ConversationInput
    ) -> str:
        """Return result from Amazon Bedrock."""
        initial_question = user_input.text
        question = self.entry.options[CONST_PROMPT_CONTEXT] + user_input.text

        config_agent_id = self.entry.options.get(CONST_AGENT_ID) or ""

        if config_agent_id != "":
            return await self.async_call_bedrock_agent(user_input, question)

        return await self.strands_agent_wrapper.generate_response(
            initial_question, 
            user_input.as_llm_context(self.entry.domain), 
            user_input.conversation_id,
            user_input.context.user_id,
        )

    async def async_process(
        self,
        user_input: agent_manager.ConversationInput,
    ) -> agent_manager.ConversationResult:
        """Process a sentence."""
        response = IntentResponse(language=user_input.language)

        user_input.conversation_id = user_input.conversation_id or uuid.uuid4().hex

        try:
            answer = await self.async_call_bedrock(user_input)
            response.async_set_speech(answer)
        except HomeAssistantError as error:
            response.async_set_error(
                IntentResponseErrorCode.FAILED_TO_HANDLE, error.args[0]
            )

        return agent_manager.ConversationResult(
            conversation_id=user_input.conversation_id,
            response=response,
        )
