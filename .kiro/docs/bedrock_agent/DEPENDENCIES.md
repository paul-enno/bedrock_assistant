# Bedrock Agent Dependencies

## Required Dependencies

### Core Dependencies

1. **boto3==1.39.9**
   - AWS SDK for Python
   - Used for all AWS Bedrock API calls
   - Provides client creation and API interaction

2. **botocore==1.39.9**
   - Core functionality for boto3
   - Low-level AWS service access
   - Required by boto3

3. **strands-agents==1.26.0**
   - Strands AI agent framework
   - Provides Agent class and model integrations
   - Handles conversation management

### Memory Dependencies

4. **strands-agents-tools[mem0_memory]==0.1.19**
   - Community tools package for Strands
   - Provides mem0_memory tool for long-term semantic memory
   - Includes mem0 library and dependencies

5. **faiss-cpu==1.9.0**
   - Facebook AI Similarity Search library
   - Required by mem0 for vector similarity search
   - Enables semantic memory retrieval

## Why faiss-cpu?

### What is FAISS?

FAISS (Facebook AI Similarity Search) is a library developed by Meta AI Research for efficient similarity search and clustering of dense vectors.

### Why Mem0 Needs It

Mem0 uses FAISS to:

1. **Store Memory Embeddings**
   - Converts text memories into vector embeddings
   - Stores vectors in FAISS index for fast retrieval

2. **Semantic Search**
   - Finds similar memories based on meaning
   - Uses vector similarity instead of keyword matching

3. **Efficient Retrieval**
   - Fast nearest neighbor search
   - Scales well with large memory collections

### CPU vs GPU Version

- **faiss-cpu**: CPU-only version (what we use)
  - Easier to install
  - No GPU required
  - Sufficient for most use cases
  - Works on all platforms

- **faiss-gpu**: GPU-accelerated version
  - Requires CUDA-capable GPU
  - Faster for very large datasets
  - More complex installation
  - Not needed for typical Home Assistant usage

## Dependency Check

The integration checks for both dependencies at startup:

```python
# Check for mem0_memory tool
try:
    from strands_tools import mem0_memory
    
    # Check for faiss
    try:
        import faiss
        MEM0_AVAILABLE = True
    except ImportError:
        # faiss-cpu not installed
        MEM0_AVAILABLE = False
except ImportError:
    # strands-agents-tools not installed
    MEM0_AVAILABLE = False
```

## Installation

### Automatic Installation

When you install the integration, Home Assistant will automatically install all dependencies from `manifest.json`:

```bash
pip install boto3==1.39.9
pip install botocore==1.39.9
pip install strands-agents==1.26.0
pip install 'strands-agents-tools[mem0_memory]==0.1.19'
pip install faiss-cpu==1.9.0
```

### Manual Installation

If automatic installation fails, install manually:

```bash
# Core dependencies
pip install boto3==1.39.9 botocore==1.39.9 strands-agents==1.26.0

# Memory dependencies
pip install 'strands-agents-tools[mem0_memory]==0.1.19'
pip install faiss-cpu==1.9.0
```

### Verify Installation

Check if all dependencies are installed:

```bash
pip list | grep -E "boto3|botocore|strands|faiss"
```

Expected output:
```
boto3                     1.39.9
botocore                  1.39.9
faiss-cpu                 1.9.0
strands-agents            1.26.0
strands-agents-tools      0.1.19
```

## Troubleshooting

### faiss-cpu Installation Issues

#### Issue: "No matching distribution found"

**Cause**: Platform not supported or Python version incompatible

**Solution**:
1. Check Python version (requires 3.8+):
   ```bash
   python --version
   ```

2. Update pip:
   ```bash
   pip install --upgrade pip
   ```

3. Try installing from conda (if using Anaconda):
   ```bash
   conda install -c conda-forge faiss-cpu
   ```

#### Issue: "Building wheel failed"

**Cause**: Missing build dependencies

**Solution** (Linux):
```bash
# Ubuntu/Debian
sudo apt-get install build-essential python3-dev

# CentOS/RHEL
sudo yum install gcc gcc-c++ python3-devel
```

**Solution** (macOS):
```bash
xcode-select --install
```

#### Issue: "ImportError: DLL load failed" (Windows)

**Cause**: Missing Visual C++ redistributables

**Solution**:
1. Download and install [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)
2. Restart and try again

### Memory Not Available

If memory is not working, check the service:

```yaml
service: bedrock_agent.get_memory_stats
```

**If mem0_available is false**, check the error field:

```json
{
  "mem0_available": false,
  "error": "faiss-cpu not available. Install with: pip install faiss-cpu"
}
```

**Check logs** for specific error:
```
WARNING: mem0_memory tool not available. Install with: pip install 'strands-agents-tools[mem0_memory]'
WARNING: mem0_memory tool requires faiss-cpu. Install with: pip install faiss-cpu
```

### Dependency Conflicts

If you encounter version conflicts:

1. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```

2. **Install in clean environment**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Check for conflicts**:
   ```bash
   pip check
   ```

## Platform-Specific Notes

### Linux

- Usually installs without issues
- May need build tools for compilation
- Works on ARM (Raspberry Pi) with some compilation time

### macOS

- Intel Macs: Works perfectly
- Apple Silicon (M1/M2): May need Rosetta 2 or native ARM build
- Xcode command line tools may be required

### Windows

- Requires Visual C++ redistributables
- Pre-built wheels available for most Python versions
- May need Windows SDK for some versions

### Docker/Container

If running in Docker, add to Dockerfile:

```dockerfile
RUN pip install boto3==1.39.9 \
    botocore==1.39.9 \
    strands-agents==1.26.0 \
    'strands-agents-tools[mem0_memory]==0.1.19' \
    faiss-cpu==1.9.0
```

## Graceful Degradation

The integration handles missing dependencies gracefully:

### If faiss-cpu is missing:
- ❌ Memory disabled
- ✅ Agent still works without memory
- ⚠️ Warning logged
- ℹ️ Error message in memory stats

### If strands-agents-tools is missing:
- ❌ Memory disabled
- ✅ Agent still works without memory
- ⚠️ Warning logged
- ℹ️ Error message in memory stats

### If boto3/botocore is missing:
- ❌ Integration fails to load
- ❌ Config entry setup fails
- 🛑 Critical error - integration cannot function

## Version Compatibility

### Python Version
- **Minimum**: Python 3.8
- **Recommended**: Python 3.11+
- **Tested**: Python 3.11, 3.12, 3.13

### Home Assistant Version
- **Minimum**: 2024.1.0
- **Recommended**: Latest stable
- **Tested**: 2024.1.0+

### Dependency Versions

| Package | Version | Notes |
|---------|---------|-------|
| boto3 | 1.39.9 | Pinned for stability |
| botocore | 1.39.9 | Must match boto3 |
| strands-agents | 1.26.0 | Latest stable |
| strands-agents-tools | 0.1.19 | Latest with mem0 |
| faiss-cpu | 1.9.0 | Latest stable |

## Future Considerations

### Potential Upgrades

1. **faiss-gpu support**: For users with GPU acceleration
2. **Alternative vector stores**: Support for other similarity search libraries
3. **Optional dependencies**: Make memory completely optional
4. **Lighter alternatives**: Explore lighter vector search options

### Monitoring

Keep an eye on:
- New strands-agents releases
- Mem0 updates
- FAISS improvements
- Security patches

## Resources

- **FAISS Documentation**: https://github.com/facebookresearch/faiss
- **Mem0 Documentation**: https://docs.mem0.ai
- **Strands Tools**: https://github.com/strands-agents/tools
- **Boto3 Documentation**: https://boto3.amazonaws.com/v1/documentation/api/latest/index.html
