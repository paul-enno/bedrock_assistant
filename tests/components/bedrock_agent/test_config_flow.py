"""Test the Bedrock Agent config flow."""

from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError, EndpointConnectionError
import pytest

from homeassistant import config_entries
from homeassistant.components.bedrock_agent.const import (
    CONST_ENABLE_HA_CONTROL,
    CONST_ENABLE_MEMORY,
    CONST_KEY_ID,
    CONST_KEY_SECRET,
    CONST_MEMORY_GUIDELINES,
    CONST_MEMORY_STORAGE_PATH,
    CONST_MODEL_ID,
    CONST_PROMPT_CONTEXT,
    CONST_REGION,
    DEFAULT_MEMORY_GUIDELINES,
    DOMAIN,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry


async def test_form(hass: HomeAssistant, mock_boto3_client) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}
    assert result["step_id"] == "user"

    # Step 1: Provide AWS credentials
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONST_KEY_ID: "test_key",
            CONST_KEY_SECRET: "test_secret",
            CONST_REGION: "us-east-1",
            "title": "Test Bedrock",
        },
    )
    
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "modelconfig"

    # Step 2: Configure model
    with patch(
        "homeassistant.components.bedrock_agent.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {
                CONST_MODEL_ID: "anthropic.claude-v2",
                CONST_PROMPT_CONTEXT: "Test prompt",
                CONST_ENABLE_HA_CONTROL: True,
                CONST_ENABLE_MEMORY: False,
                CONST_MEMORY_STORAGE_PATH: "",
            },
        )
        await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["data"] == {
        CONST_KEY_ID: "test_key",
        CONST_KEY_SECRET: "test_secret",
        CONST_REGION: "us-east-1",
        "title": "Test Bedrock",
    }
    assert result3["options"] == {
        CONST_MODEL_ID: "anthropic.claude-v2",
        CONST_PROMPT_CONTEXT: "Test prompt",
        CONST_ENABLE_HA_CONTROL: True,
        CONST_ENABLE_MEMORY: False,
        CONST_MEMORY_STORAGE_PATH: "",
    }
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_invalid_auth(hass: HomeAssistant) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_client = MagicMock()
    mock_client.list_foundation_models.side_effect = ClientError(
        {"Error": {"Code": "UnrecognizedClientException", "Message": "Invalid"}},
        "list_foundation_models",
    )
    # Create a mock exceptions namespace
    mock_exceptions = MagicMock()
    mock_exceptions.ClientError = ClientError
    mock_client.exceptions = mock_exceptions

    with patch(
        "homeassistant.components.bedrock_agent.config_flow.boto3.client",
        return_value=mock_client,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONST_KEY_ID: "test_key",
                CONST_KEY_SECRET: "test_secret",
                CONST_REGION: "us-east-1",
                "title": "Test Bedrock",
            },
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "user"
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_form_cannot_connect(hass: HomeAssistant) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_client = MagicMock()
    mock_client.list_foundation_models.side_effect = EndpointConnectionError(
        endpoint_url="https://test"
    )

    with patch(
        "homeassistant.components.bedrock_agent.config_flow.boto3.client",
        return_value=mock_client,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONST_KEY_ID: "test_key",
                CONST_KEY_SECRET: "test_secret",
                CONST_REGION: "us-east-1",
                "title": "Test Bedrock",
            },
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "user"
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_unknown_error(hass: HomeAssistant) -> None:
    """Test we handle unknown error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_client = MagicMock()
    mock_client.list_foundation_models.side_effect = Exception("Unknown error")
    # Create a mock exceptions namespace
    mock_exceptions = MagicMock()
    mock_exceptions.ClientError = ClientError
    mock_client.exceptions = mock_exceptions

    with patch(
        "homeassistant.components.bedrock_agent.config_flow.boto3.client",
        return_value=mock_client,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONST_KEY_ID: "test_key",
                CONST_KEY_SECRET: "test_secret",
                CONST_REGION: "us-east-1",
                "title": "Test Bedrock",
            },
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "user"
    assert result2["errors"] == {"base": "unknown"}


async def test_options_flow(hass: HomeAssistant, mock_config_entry, mock_boto3_client) -> None:
    """Test options flow with menu."""
    mock_config_entry.add_to_hass(hass)

    # Step 1: Init shows menu
    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "init"
    assert "aws_config" in result["menu_options"]
    assert "ai_config" in result["menu_options"]
    assert "memory_config" in result["menu_options"]
    assert "tools_config" in result["menu_options"]


async def test_options_flow_aws_config(
    hass: HomeAssistant, mock_config_entry, mock_boto3_client
) -> None:
    """Test AWS configuration in options flow."""
    mock_config_entry.add_to_hass(hass)

    # Navigate to AWS config
    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"next_step_id": "aws_config"},
    )

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "aws_config"

    # Configure AWS settings
    with patch(
        "homeassistant.components.bedrock_agent.async_setup_entry",
        return_value=True,
    ):
        result3 = await hass.config_entries.options.async_configure(
            result2["flow_id"],
            user_input={
                CONST_REGION: "eu-west-1",
                CONST_KEY_ID: "new_test_key",
                CONST_KEY_SECRET: "new_test_secret",
            },
        )

    # Should navigate to AI config after reload (to verify/update model)
    assert result3["type"] is FlowResultType.FORM
    assert result3["step_id"] == "ai_config"
    
    # Verify config entry data was updated
    assert mock_config_entry.data[CONST_KEY_ID] == "new_test_key"
    assert mock_config_entry.data[CONST_KEY_SECRET] == "new_test_secret"
    assert mock_config_entry.data[CONST_REGION] == "eu-west-1"


async def test_options_flow_ai_config(
    hass: HomeAssistant, mock_config_entry, mock_boto3_client
) -> None:
    """Test AI configuration in options flow."""
    mock_config_entry.add_to_hass(hass)

    # Navigate to AI config
    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"next_step_id": "ai_config"},
    )

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "ai_config"

    # Configure AI settings - should return to menu
    result3 = await hass.config_entries.options.async_configure(
        result2["flow_id"],
        user_input={
            CONST_MODEL_ID: "anthropic.claude-v2",
            CONST_PROMPT_CONTEXT: "Updated system prompt",
        },
    )

    # Should return to menu, not close
    assert result3["type"] is FlowResultType.MENU
    assert result3["step_id"] == "init"
    
    # Verify options were saved
    assert mock_config_entry.options[CONST_MODEL_ID] == "anthropic.claude-v2"
    assert mock_config_entry.options[CONST_PROMPT_CONTEXT] == "Updated system prompt"


async def test_options_flow_memory_config(
    hass: HomeAssistant, mock_config_entry_with_memory, mock_boto3_client
) -> None:
    """Test memory configuration in options flow."""
    mock_config_entry_with_memory.add_to_hass(hass)

    # Navigate to memory config
    result = await hass.config_entries.options.async_init(mock_config_entry_with_memory.entry_id)
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"next_step_id": "memory_config"},
    )

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "memory_config"

    # Configure memory settings (memory is already enabled, so guidelines field is shown)
    result3 = await hass.config_entries.options.async_configure(
        result2["flow_id"],
        user_input={
            CONST_ENABLE_MEMORY: True,
            CONST_MEMORY_STORAGE_PATH: "/custom/path",
            CONST_MEMORY_GUIDELINES: "Custom guidelines",
        },
    )

    # Should return to menu, not close
    assert result3["type"] is FlowResultType.MENU
    assert result3["step_id"] == "init"
    
    # Verify options were saved
    assert mock_config_entry_with_memory.options[CONST_ENABLE_MEMORY] is True
    assert mock_config_entry_with_memory.options[CONST_MEMORY_STORAGE_PATH] == "/custom/path"
    assert mock_config_entry_with_memory.options[CONST_MEMORY_GUIDELINES] == "Custom guidelines"


async def test_options_flow_tools_config(
    hass: HomeAssistant, mock_config_entry, mock_boto3_client
) -> None:
    """Test tools configuration in options flow."""
    mock_config_entry.add_to_hass(hass)

    # Navigate to tools config
    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"next_step_id": "tools_config"},
    )

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "tools_config"

    # Configure tools settings
    result3 = await hass.config_entries.options.async_configure(
        result2["flow_id"],
        user_input={
            CONST_ENABLE_HA_CONTROL: False,
        },
    )

    # Should return to menu, not close
    assert result3["type"] is FlowResultType.MENU
    assert result3["step_id"] == "init"
    
    # Verify options were saved
    assert mock_config_entry.options[CONST_ENABLE_HA_CONTROL] is False


async def test_options_flow_memory_disabled(
    hass: HomeAssistant, mock_config_entry, mock_boto3_client
) -> None:
    """Test memory config with memory disabled doesn't show guidelines."""
    mock_config_entry.add_to_hass(hass)

    # Navigate to memory config
    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"next_step_id": "memory_config"},
    )

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "memory_config"

    # Memory is disabled in mock_config_entry by default
    # Memory guidelines field should not be in the schema
    schema_keys = [str(key) for key in result2["data_schema"].schema.keys()]
    assert CONST_MEMORY_GUIDELINES not in schema_keys


async def test_options_flow_memory_enabled_shows_guidelines(
    hass: HomeAssistant, mock_config_entry_with_memory, mock_boto3_client
) -> None:
    """Test memory config with memory enabled shows guidelines field."""
    mock_config_entry_with_memory.add_to_hass(hass)

    # Navigate to memory config
    result = await hass.config_entries.options.async_init(
        mock_config_entry_with_memory.entry_id
    )
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"next_step_id": "memory_config"},
    )

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "memory_config"

    # Memory is enabled, guidelines field should be in the schema
    schema_keys = [str(key) for key in result2["data_schema"].schema.keys()]
    assert any(CONST_MEMORY_GUIDELINES in key for key in schema_keys)
