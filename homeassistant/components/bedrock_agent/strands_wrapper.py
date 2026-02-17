"""Wrapper for strands.Agent to make it easier to test and implement."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from botocore.exceptions import ClientError
from strands import Agent
from strands.models import BedrockModel
from strands.session.file_session_manager import FileSessionManager

from homeassistant.exceptions import HomeAssistantError

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.llm import API, LLMContext

    from .aws_client import AWSClientFactory

# Configure the root strands logger
logging.getLogger("strands").setLevel(logging.ERROR)

_LOGGER = logging.getLogger(__name__)


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
    ) -> None:
        """Initialize the wrapper."""
        self.hass = hass
        self.aws_factory = aws_factory
        self.system_prompt = system_prompt
        self.session_id = session_id
        self.storage_dir = storage_dir

        self.tools = []
        self.apis = apis
        self.api_instances = {}
        self.llm_context = None
        self.modules = {}

        self.agent = self.get_agent(model_id, True, True)


    def get_agent(
        self, model_id: str, with_session: bool, with_system_prompt: bool
    ) -> Agent:
        """Initialize Agent with specified configuration."""
        # Create a boto3 session
        session = self.aws_factory.create_boto3_session()

        # Create a Bedrock model with the custom session
        bedrock_model = BedrockModel(
            model_id=model_id,
            boto_session=session,
            streaming=False,
        )

        # Build agent kwargs
        agent_kwargs: dict[str, Any] = {
            "model": bedrock_model,
            "callback_handler": None,
        }

        if with_session:
            session_id = self.session_id or "default-session"
            agent_kwargs["session_manager"] = FileSessionManager(
                session_id=session_id, storage_dir=self.storage_dir
            )

        if with_system_prompt:
            agent_kwargs["system_prompt"] = self.system_prompt

        return Agent(**agent_kwargs)

    async def generate_response(
        self, prompt: Any, llm_context: LLMContext | None = None
    ) -> str:
        """Generate a response from the agent."""
        try:
            response = await self.hass.async_add_executor_job(self.agent, prompt)
            return str(response)
        except ClientError as error:
            raise HomeAssistantError(
                f"Amazon Bedrock Error: `{error.response.get('Error').get('Message')}`"
            ) from error

    async def async_call_llm(self, prompt: str, llm_context: LLMContext) -> str:
        """Call the agent with the given prompt."""
        _LOGGER.debug("Calling LLM with prompt: %s", prompt)
        return await self.generate_response(prompt, llm_context)
