# Mem0 AWS Credentials Configuration

## Overview

Mem0 requires AWS credentials to access Bedrock for embeddings and LLM operations. The Bedrock Agent integration automatically configures these credentials for you.

## Automatic Configuration

When you enable memory, the integration automatically:

1. **Sets AWS Credentials**: Uses your Bedrock Agent config entry credentials
2. **Configures Providers**: Sets mem0 to use AWS Bedrock
3. **Selects Models**: Chooses appropriate Bedrock models for embeddings and LLM

**No manual configuration needed!**

## How It Works

### Credential Flow

```
Bedrock Agent Config Entry
    ↓
AWS Access Key ID
AWS Secret Access Key  
AWS Region
    ↓
Environment Variables
    ↓
Mem0 Client
    ↓
AWS Bedrock API
```

### Environment Variables Set

The integration sets these environment variables for mem0:

```python
AWS_ACCESS_KEY_ID = "your_access_key"
AWS_SECRET_ACCESS_KEY = "your_secret_key"
AWS_REGION = "us-west-2"  # or your configured region

MEM0_EMBEDDER_PROVIDER = "aws_bedrock"
MEM0_EMBEDDER_MODEL = "amazon.titan-embed-text-v2:0"
MEM0_LLM_PROVIDER = "aws_bedrock"
MEM0_LLM_MODEL = "anthropic.claude-3-5-haiku-20241022-v1:0"
```

### When Credentials Are Set

Credentials are configured:
- ✅ During wrapper initialization
- ✅ Before mem0_memory tool is added
- ✅ Only if memory is enabled
- ✅ Only if not already set (respects existing env vars)

## Models Used

### Embeddings Model

**amazon.titan-embed-text-v2:0**
- Converts text to 1024-dimensional vectors
- Used for semantic search
- Cost: ~$0.0001 per 1000 tokens
- Fast and efficient

### LLM Model

**anthropic.claude-3-5-haiku-20241022-v1:0**
- Processes and extracts memories
- Identifies important information
- Cost: ~$0.001 per 1000 tokens
- Fast inference

## AWS Permissions Required

Your AWS credentials need these Bedrock permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": [
        "arn:aws:bedrock:*::foundation-model/amazon.titan-embed-text-v2:0",
        "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-5-haiku-20241022-v1:0"
      ]
    }
  ]
}
```

**Note**: These are the same permissions needed for the Bedrock Agent, so if your agent works, mem0 will work too!

## Model Access

Ensure you have enabled model access in Bedrock console:

1. Open [AWS Bedrock Console](https://console.aws.amazon.com/bedrock)
2. Navigate to "Model access"
3. Enable:
   - Amazon Titan Embeddings G1 - Text v2
   - Claude 3.5 Haiku

## Troubleshooting

### Error: "Could not connect to the endpoint URL"

**Cause**: AWS credentials not set or invalid

**Solution**:
1. Verify your Bedrock Agent config entry has valid credentials
2. Check logs for credential configuration messages
3. Ensure AWS region is correct

### Error: "AccessDeniedException"

**Cause**: Credentials don't have permission to invoke models

**Solution**:
1. Check IAM permissions for your AWS user/role
2. Ensure `bedrock:InvokeModel` permission is granted
3. Verify model access is enabled in Bedrock console

### Error: "ValidationException: The provided model identifier is invalid"

**Cause**: Model not available in your region

**Solution**:
1. Check model availability in your region
2. Use a region where both models are available (us-west-2, us-east-1)
3. Or override with environment variables:
   ```bash
   export MEM0_EMBEDDER_MODEL="your-preferred-embedding-model"
   export MEM0_LLM_MODEL="your-preferred-llm-model"
   ```

### Error: "ResourceNotFoundException: Could not resolve the foundation model"

**Cause**: Model access not enabled in Bedrock console

**Solution**:
1. Open Bedrock console
2. Enable model access for Titan Embeddings and Claude 3.5 Haiku
3. Wait a few minutes for access to propagate

## Custom Configuration

### Override Default Models

You can override the default models by setting environment variables before starting Home Assistant:

```bash
# Use different embedding model
export MEM0_EMBEDDER_MODEL="cohere.embed-english-v3"

# Use different LLM model
export MEM0_LLM_MODEL="anthropic.claude-3-sonnet-20240229-v1:0"

# Start Home Assistant
hass
```

### Use Different Provider

If you want to use a different provider (not Bedrock):

```bash
# Use OpenAI for embeddings
export MEM0_EMBEDDER_PROVIDER="openai"
export MEM0_EMBEDDER_MODEL="text-embedding-3-small"
export OPENAI_API_KEY="your-openai-key"

# Use Anthropic for LLM
export MEM0_LLM_PROVIDER="anthropic"
export MEM0_LLM_MODEL="claude-3-haiku-20240307"
export ANTHROPIC_API_KEY="your-anthropic-key"
```

**Note**: Using non-Bedrock providers requires additional API keys and may incur different costs.

## Security Best Practices

### Credential Storage

- ✅ Credentials stored in Home Assistant config entry (encrypted)
- ✅ Environment variables set at runtime (not persisted)
- ✅ No credentials in logs (debug mode may show region)
- ✅ Credentials isolated per config entry

### IAM Best Practices

1. **Use IAM Roles** (if running on EC2/ECS):
   ```python
   # No credentials needed - uses instance role
   ```

2. **Least Privilege**:
   - Only grant `bedrock:InvokeModel` permission
   - Restrict to specific model ARNs
   - Use resource-based policies

3. **Rotate Credentials**:
   - Rotate AWS access keys regularly
   - Update config entry with new credentials
   - Integration will use new credentials immediately

### Multi-User Environments

Each config entry has isolated credentials:
- ✅ Different users can use different AWS accounts
- ✅ Memory isolated by entry_id
- ✅ No credential sharing between entries

## Cost Management

### Monitor Usage

Track Bedrock usage in AWS Console:
1. Open CloudWatch
2. Navigate to Bedrock metrics
3. Monitor:
   - InvokeModel calls
   - Token usage
   - Costs

### Set Budgets

Create AWS Budget alerts:
1. Open AWS Budgets
2. Create budget for Bedrock
3. Set alerts at thresholds (e.g., $10, $50)

### Optimize Costs

1. **Limit Memory Operations**:
   - Don't store trivial information
   - Use specific queries for retrieval
   - Clear old memories periodically

2. **Use Cheaper Models**:
   ```bash
   export MEM0_LLM_MODEL="anthropic.claude-3-haiku-20240307-v1:0"
   ```

3. **Batch Operations**:
   - Store multiple facts in one memory
   - Retrieve once and cache results

## Verification

### Check Configuration

Use the memory stats service to verify configuration:

```yaml
service: bedrock_agent.get_memory_stats
```

Expected output:
```json
{
  "memory_enabled": true,
  "mem0_available": true,
  "user_id": "your_entry_id",
  "cached_conversations": 0,
  "tools_count": 1
}
```

### Check Logs

Look for configuration messages in logs:

```
INFO: Configured mem0 with AWS Bedrock: embedder=amazon.titan-embed-text-v2:0, llm=anthropic.claude-3-5-haiku-20241022-v1:0, region=us-west-2
INFO: Mem0 memory enabled for long-term semantic memory
```

### Test Memory

Store and retrieve a test memory:

```
User: "Remember that my favorite color is blue"
Agent: [Stores in mem0]

User: "What's my favorite color?"
Agent: "Your favorite color is blue"
```

If this works, credentials are configured correctly!

## Advanced Configuration

### Custom Mem0 Config

For advanced users, you can create a custom mem0 configuration by setting environment variables before starting Home Assistant:

```bash
# Custom vector store path
export MEM0_VECTOR_STORE_PATH="/custom/path/mem0"

# Custom embedding dimensions
export MEM0_EMBEDDING_DIMS="1024"

# Custom LLM parameters
export MEM0_LLM_TEMPERATURE="0.2"
export MEM0_LLM_MAX_TOKENS="3000"
```

### Multiple Regions

If you have multiple Bedrock Agent instances in different regions:

1. Each config entry uses its own region
2. Mem0 will use the region from the config entry
3. Ensure models are available in all regions

### Debugging

Enable debug logging to see credential configuration:

```yaml
logger:
  default: info
  logs:
    homeassistant.components.bedrock_agent: debug
```

Look for:
```
DEBUG: Set AWS_ACCESS_KEY_ID for mem0
DEBUG: Set AWS_SECRET_ACCESS_KEY for mem0
DEBUG: Set AWS_REGION for mem0: us-west-2
```

## Resources

- **AWS Bedrock Pricing**: https://aws.amazon.com/bedrock/pricing/
- **Titan Embeddings**: https://aws.amazon.com/bedrock/titan/
- **Claude Models**: https://aws.amazon.com/bedrock/claude/
- **IAM Best Practices**: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html
- **Mem0 Documentation**: https://docs.mem0.ai
