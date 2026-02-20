# Mem0 Memory Configuration Guide

## Overview

The Bedrock Agent integration uses Mem0 for long-term semantic memory. Mem0 requires two models from AWS Bedrock:
1. **Embedder Model**: For creating vector embeddings of memories
2. **LLM Model**: For processing and understanding memory operations

## Default Configuration

By default, the integration uses:
- **Embedder**: `amazon.titan-embed-text-v1` (widely available, cost-effective)
- **LLM**: **Same model as your main agent configuration** (ensures consistency and availability)

This means if you configure the integration to use Claude 3.5 Sonnet, Mem0 will also use Claude 3.5 Sonnet for memory operations.

## Benefits of Using the Same Model

- ✅ **Guaranteed Availability**: If the model works for your agent, it works for memory
- ✅ **Consistency**: Same model behavior across all operations
- ✅ **Simplified Configuration**: No need to manage separate model settings
- ✅ **Cost Predictability**: All operations use the same pricing tier

## Model Availability Issues

If you see errors like:
```
The provided model identifier is invalid
```

This means the default models are not available in your AWS region or not enabled in your account.

## Solution 1: Enable Model Access in AWS Console

1. Go to [AWS Bedrock Console](https://console.aws.amazon.com/bedrock)
2. Navigate to "Model access" in the left sidebar
3. Click "Manage model access"
4. Enable access to:
   - Amazon Titan Embeddings G1 - Text (`amazon.titan-embed-text-v1`)
   - Anthropic Claude 3 Haiku (`anthropic.claude-3-haiku-20240307-v1:0`)
5. Wait a few minutes for access to be granted

## Solution 2: Override Default Models

You can override the default models by setting environment variables in your Home Assistant configuration.

### Using configuration.yaml

Add to your `configuration.yaml`:

```yaml
# Mem0 Model Configuration
homeassistant:
  customize:
    # Set environment variables for Mem0
    environment:
      MEM0_EMBEDDER_MODEL: "amazon.titan-embed-text-v1"
      MEM0_LLM_MODEL: "anthropic.claude-3-haiku-20240307-v1:0"
```

### Using Docker/Container

If running Home Assistant in Docker, add environment variables:

```bash
docker run -d \
  -e MEM0_EMBEDDER_MODEL="amazon.titan-embed-text-v1" \
  -e MEM0_LLM_MODEL="anthropic.claude-3-haiku-20240307-v1:0" \
  ...
```

Or in `docker-compose.yml`:

```yaml
services:
  homeassistant:
    environment:
      - MEM0_EMBEDDER_MODEL=amazon.titan-embed-text-v1
      - MEM0_LLM_MODEL=anthropic.claude-3-haiku-20240307-v1:0
```

## Available Models by Region

### Embedder Models (Choose One)

| Model ID | Name | Availability |
|----------|------|--------------|
| `amazon.titan-embed-text-v1` | Titan Embeddings G1 - Text | Most regions |
| `amazon.titan-embed-text-v2:0` | Titan Text Embeddings v2 | Newer regions |
| `cohere.embed-english-v3` | Cohere Embed English | Select regions |
| `cohere.embed-multilingual-v3` | Cohere Embed Multilingual | Select regions |

### LLM Models (Choose One)

| Model ID | Name | Availability |
|----------|------|--------------|
| `anthropic.claude-3-haiku-20240307-v1:0` | Claude 3 Haiku | Most regions |
| `anthropic.claude-3-5-haiku-20241022-v1:0` | Claude 3.5 Haiku | Newer regions |
| `anthropic.claude-instant-v1` | Claude Instant | Most regions |
| `amazon.titan-text-lite-v1` | Titan Text Lite | Most regions |
| `amazon.titan-text-express-v1` | Titan Text Express | Most regions |

## Checking Model Availability

To check which models are available in your region:

1. Go to [AWS Bedrock Console](https://console.aws.amazon.com/bedrock)
2. Navigate to "Foundation models"
3. Check the "Available" column for models in your region
4. Note the exact model IDs (shown in the details)

## Region-Specific Recommendations

### US East (us-east-1)
```yaml
MEM0_EMBEDDER_MODEL: "amazon.titan-embed-text-v1"
MEM0_LLM_MODEL: "anthropic.claude-3-haiku-20240307-v1:0"
```

### US West (us-west-2)
```yaml
MEM0_EMBEDDER_MODEL: "amazon.titan-embed-text-v1"
MEM0_LLM_MODEL: "anthropic.claude-3-haiku-20240307-v1:0"
```

### EU (eu-west-1)
```yaml
MEM0_EMBEDDER_MODEL: "amazon.titan-embed-text-v1"
MEM0_LLM_MODEL: "anthropic.claude-3-haiku-20240307-v1:0"
```

### Asia Pacific (ap-southeast-1)
```yaml
MEM0_EMBEDDER_MODEL: "amazon.titan-embed-text-v1"
MEM0_LLM_MODEL: "anthropic.claude-instant-v1"
```

## Troubleshooting

### Error: "Model not found"
- Verify the model ID is correct (check AWS console)
- Ensure model access is enabled in your AWS account
- Check that the model is available in your region

### Error: "Access denied"
- Enable model access in AWS Bedrock console
- Wait 5-10 minutes after enabling access
- Verify your AWS credentials have Bedrock permissions

### Error: "Throttling"
- You're hitting API rate limits
- Consider using a lighter model (e.g., Claude Instant instead of Claude 3)
- Reduce memory operations frequency

## Performance Considerations

### Embedder Models
- **Titan Embed v1**: Fast, cost-effective, good quality
- **Titan Embed v2**: Better quality, slightly slower
- **Cohere**: Excellent quality, higher cost

### LLM Models
- **Claude 3 Haiku**: Fast, cost-effective, good quality
- **Claude 3.5 Haiku**: Better quality, slightly higher cost
- **Claude Instant**: Very fast, lower cost, good for simple operations
- **Titan Text**: Cost-effective, good for basic operations

## Cost Optimization

To minimize costs:
1. Use Titan Embed v1 for embeddings (lowest cost)
2. Use Claude Instant or Titan Text Lite for LLM (lower cost)
3. Disable memory if not needed
4. Use memory selectively for important conversations

## Disabling Memory

If you encounter persistent issues or want to disable memory:

1. Go to Settings → Devices & Services
2. Find your Bedrock Agent integration
3. Click "Configure"
4. Uncheck "Enable Long-term Memory"
5. Click "Submit"

The agent will continue to work with short-term and persistent storage, just without semantic memory.

## Getting Help

If you continue to have issues:
1. Enable debug logging:
   ```yaml
   logger:
     default: info
     logs:
       homeassistant.components.bedrock_agent: debug
       mem0: debug
   ```
2. Check Home Assistant logs for detailed error messages
3. Report issues on [GitHub](https://github.com/your-repo/issues) with:
   - Your AWS region
   - Model IDs you're trying to use
   - Full error message from logs
