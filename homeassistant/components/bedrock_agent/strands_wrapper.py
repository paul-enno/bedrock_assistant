"""Wrapper for strands.Agent to make it easier to test and implement."""

import logging
import os
from typing import Any

import boto3
from botocore.exceptions import ClientError
from strands import Agent
from strands.models import BedrockModel
from strands.session.file_session_manager import FileSessionManager
from strands_tools import mem0_memory

import custom_tool
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.llm import API, LLMContext

# Configure the root strands logger
logging.getLogger("strands").setLevel(logging.DEBUG)

_LOGGER = logging.getLogger(__name__)

class StrandsAgentWrapper:
    """Wrapper for strands.Agent to make it easier to test and implement."""

    @classmethod
    async def create(
        cls,
        hass: HomeAssistant,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        region_name: str,
        model_id: str,
        apis: list[API],
        system_prompt: str | None = ""
    ) -> "StrandsAgentWrapper":
        """Create and initialize the wrapper."""
        instance = cls.__new__(cls)
        await instance._async_init(
            hass, aws_access_key_id, aws_secret_access_key,
            region_name, model_id, apis, system_prompt
        )
        return instance

    async def _async_init(
        self,
        hass: HomeAssistant,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        region_name: str,
        model_id: str,
        apis: list[API],
        system_prompt: str | None = ""
    ) -> None:
        """Initialize the wrapper."""
        self.hass = hass
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.region_name = region_name
        self.system_prompt = system_prompt

        self.tools = []
        self.apis = apis
        self.api_instances = {}
        self.llm_context = None
        self.modules = {}

        self.agent = await self.get_agent(model_id, True, True)


    async def get_agent(self,
        model_id: str,
        withSession: bool,
        withSystemPrompt: bool) -> Agent:
        """Initalize Agent."""

        # Create a boto3 session
        session = boto3.Session(
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name
        )

        # Create a Bedrock model with the custom session
        bedrock_model = BedrockModel(
            model_id=model_id,
            boto_session=session,
            streaming=False,
        )

        # SSE_URL = "http://localhost/mcp_server/sse"
        # SSE_HEADERS =  {
        #     "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI0N2EwZTZhNGVmMTM0OGU2YWJjMGU5MDI0NTA4ZTJkNSIsImlhdCI6MTc1NDMxOTYxMSwiZXhwIjoyMDY5Njc5NjExfQ.oZFvtcPgI1o7O36i9T451XwXQ4yPIAhYc8AlHnPPpzw"
        # }

        # sse_mcp_client = MCPClient(lambda: sse_client(SSE_URL, headers=SSE_HEADERS))
        # sse_mcp_client.

        # try:
        #     mcp_tools = sse_mcp_client.list_tools_sync()

        # except Exception as error:
        #     _LOGGER.debug("Error MCPClient: %s", error)
        # finally:
        #     _LOGGER.debug("Closing MCPClient")

        # os.environ["KNOWLEDGE_BASE_ID"] = "DS6LIXCQTG"
        # os.environ["OPENSEARCH_HOST"] = "localhost"
        os.environ["AWS_REGION"] = self.region_name
        os.environ["AWS_ACCESS_KEY_ID"] = self.aws_access_key_id
        os.environ["AWS_SECRET_ACCESS_KEY"] = self.aws_secret_access_key

        # memory_config = {
        #     "embedder": {"provider": "aws_bedrock", "config": {"model": "amazon.titan-embed-text-v2:0"}},
        #     "llm": {
        #         "provider": "aws_bedrock",
        #         "config": {
        #             "model": "anthropic.claude-3-5-haiku-20241022-v1:0",
        #             "temperature": 0.1,
        #             "max_tokens": 2000,
        #         },
        #     },
        #     "graph_store": {
        #         "provider": "neo4j",
        #         "config": {
        #             "url": "neo4j://localhost:7687",
        #             "username": "neo4j",
        #             "password": "enno1234"
        #         }
        #     },
        #     # "vector_store": {}
        #     # "vector_store": {
        #     #     "provider": "opensearch",
        #     #     "config": {
        #     #         "port": 9200,
        #     #         "collection_name": "mem0_memories",
        #     #         "host": os.environ.get("OPENSEARCH_HOST"),
        #     #         "embedding_model_dims": 1024,
        #     #         "connection_class": RequestsHttpConnection,
        #     #         "pool_maxsize": 20,
        #     #         "use_ssl": False,
        #     #         "verify_certs": False,
        #     #         "http_auth": ("admin", "atBiqA7y@dkz")
        #     #     },
        #     # },
        # }

        # memory = await self.hass.async_add_executor_job(partial(mem0_memory.Mem0ServiceClient, memory_config))
        # tools = [memory]

        # tools = [mem0_memory, custom_tool]
        tools = [custom_tool]

        session_manager = FileSessionManager(session_id="enno-123", storage_dir="/tmp/strands")  # noqa: S108
        if(withSession and withSystemPrompt):
            return Agent(tools=tools, model=bedrock_model, session_manager=session_manager, system_prompt=self.system_prompt, callback_handler=None)
        if(withSession):
            return Agent(model=bedrock_model, session_manager=session_manager, callback_handler=None)
        if(withSystemPrompt):
            return Agent(model=bedrock_model, system_prompt=self.system_prompt, callback_handler=None)

        return Agent(model=bedrock_model, callback_handler=None)

    async def generate_response(self, prompt: Any, llm_context: LLMContext | None = None) -> str:
        """Generate a response from the agent."""
        try:
            response = await self.hass.async_add_executor_job(self.agent, prompt)
            # return response.__str__()
            return str(response)
        except ClientError as error:
            raise HomeAssistantError(
                f"Amazon Bedrock Error: `{error.response.get('Error').get('Message')}`"
            ) from error

    async def async_call_llm(self, prompt: str, llm_context: LLMContext) -> str:
        """Call the agent with the given prompt."""
        _LOGGER.debug("Calling LLM with prompt: %s", prompt)
        try:
            response = await self.hass.async_add_executor_job(self.agent, prompt)
            # return response.__str__()
            return str(response)
        except ClientError as error:
            raise HomeAssistantError(
                f"Amazon Bedrock Error: `{error.response.get('Error').get('Message')}`"
            ) from error
