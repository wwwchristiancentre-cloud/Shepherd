# Shepherd Performance Configuration Guide

## Overview

Shepherd supports multiple performance configurations depending on your hardware and use case. This guide covers all available options for optimizing transcription performance.

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Virtual Env   │    │   Global Python │    │   System GPU    │
│   (venv311)     │    │   Installation  │    │   (NVIDIA)      │
│                 │    │                 │    │                 │
│ • FastAPI       │    │ • PyTorch CUDA  │    │ • GTX 1080      │
│ • OpenAI Whisper│    │   (if installed │    │ • RTX series     │
│ • Project deps  │    │    globally)    │    │ • MX series      │
│ • SQLite        │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Shepherd App   │
                    │ • Transcription │
                    │ • Project Mgmt │
                    │ • Local Storage│
                    └─────────────────┘
```

## Configuration Options

### Option 1: CPU-Only Mode (Recommended Default)

**Best For:**
- Most church installations
- Any hardware (no GPU required)
- Reliable operation
- Zero configuration

**Setup:**
```bash
# Activate virtual environment
venv311\Scripts\activate

# Install dependencies (PyTorch CPU version installed automatically)
pip install torch>=2.0.0 numpy>=1.21.0  # CPU version
pip install --no-deps openai-whisper
```

**Performance:**
- Model load time: ~5-10 seconds
- 45-minute sermon: ~1-2 minutes
- Memory usage: 4-8GB RAM
- Reliability: 100% (works everywhere)

### Option 2: GPU Acceleration (High Performance)

**Best For:**
- Large churches with frequent transcription needs
- Users with NVIDIA GPUs
- High-volume media production

**Requirements:**
- NVIDIA GPU with CUDA support (10-series or newer)
- CUDA drivers installed (13.0+ preferred)
- 4GB+ VRAM recommended

**Setup:**
```bash
# Step 1: Install GPU PyTorch globally (outside venv)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126

# Step 2: Verify CUDA
python -c "import torch; print('CUDA available:', torch.cuda.is_available())"

# Step 3: Run backend outside venv for GPU access
uvicorn backend.app.main:app --reload
```

**Performance:**
- Model load time: ~2-5 seconds
- 45-minute sermon: ~10-30 seconds (10x faster!)
- Memory usage: 6-12GB VRAM + system RAM
- Compatibility: NVIDIA GPUs only

### Option 3: Hybrid Mode (Advanced)

**Best For:**
- Development teams
- Users wanting both isolation and performance
- Enterprise deployments

**Setup:**
```
Global Python Installation:
├── PyTorch CUDA (installed globally)
├── CUDA libraries
└── System Python environment

Virtual Environment (venv311):
├── FastAPI, Whisper, project dependencies
├── Isolated project packages
└── Uses global PyTorch when run globally
```

**Configuration:**
```bash
# Global PyTorch (GPU)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126

# Project venv (isolated)
python -m venv venv311
venv311\Scripts\activate
pip install fastapi openai-whisper numba

# Run modes:
# GPU: uvicorn backend.app.main:app (global Python)
# CPU: venv311\Scripts\activate; uvicorn backend.app.main:app (venv Python)
```

## Model Management

### Automatic Downloads

Shepherd downloads Whisper models automatically:
- **Medium model**: ~1.5GB (balance of speed/accuracy)
- **Storage location**: `./backend/models/` (default)
- **Network required**: First transcription only

### Custom Model Locations

For advanced users:

```bash
# Environment variable (highest priority)
export WHISPER_MODEL_ROOT=/custom/path/models

# Or modify Whisper service
model = whisper.load_model("medium", download_root="/custom/path/models")
```

### Available Models

| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| `tiny` | 39MB | ⚡⚡⚡⚡⚡ | ⭐⭐ | Testing only |
| `base` | 147MB | ⚡⚡⚡⚡ | ⭐⭐⭐ | Draft work |
| `small` | 463MB | ⚡⚡⚡ | ⭐⭐⭐⭐ | Good balance |
| `medium` | 1.5GB | ⚡⚡ | ⭐⭐⭐⭐⭐ | Production use |
| `large` | 2.9GB | ⚡ | ⭐⭐⭐⭐⭐⭐ | Maximum accuracy |

## Performance Comparison

### Hardware Requirements by Model

| Model Size | CPU RAM | GPU VRAM | SSD Space |
|------------|---------|----------|----------|
| tiny | 2GB | 1GB | 100MB |
| base | 4GB | 2GB | 300MB |
| small | 8GB | 4GB | 1GB |
| medium | 8GB | 6GB | 3GB |
| large | 16GB | 12GB | 6GB |

### Transcription Speed Benchmarks

| Hardware/Model | tiny | base | small | medium | large |
|----------------|------|-------|-------|--------|-------|
| CPU i5-8500 | 2s | 4s | 10s | 30s | 90s |
| CPU i7-10700K | 1s | 2s | 6s | 18s | 55s |
| GTX 1080 | <1s | <1s | 2s | 8s | 25s |
| RTX 3070 | <1s | <1s | 1s | 4s | 12s |
| RTX 4070 | <1s | <1s | <1s | 3s | 9s |

*Per-minute of audio, estimated times

## Troubleshooting Performance Issues

### CPU Issues

**Problem:** Transcriptions take too long on CPU
**Solution:**
- Use 'small' model instead of 'medium' for 3x speedup
- Ensure 8GB+ RAM available
- Check system cooling (CPUs throttle when hot)

### GPU Issues

**Problem:** "CUDA is not available" despite GPU
**Solution:**
```bash
# Check CUDA drivers
nvidia-smi

# Verify PyTorch CUDA
python -c "import torch; print('CUDA:', torch.cuda.is_available(), '| Count:', torch.cuda.device_count())"

# Reinstall if needed
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
```

**Problem:** GPU memory errors
**Solution:**
- Reduce model size (medium → small → base)
- Close other GPU-intensive applications
- Restart system to clear GPU memory

### Model Download Issues

**Problem:** Model downloads fail or are slow
**Solution:**
```bash
# Pre-download manually
python -c "
import whisper
model = whisper.load_model('medium', download_root='./backend/models')
print('Model ready!')
"

# Or use different model
model = whisper.load_model('small')  # Smaller/faster to download
```

## Optimized Production Setup

For church production environments:

### Recommended Configuration
```
Hardware: Desktop PC with NVIDIA GPU
Model: medium (balance)
PyTorch: CUDA globally installed
Deployment: Hybrid mode (venv + global GPU)
Backup: CPU fallback available
```

### Startup Script (Windows)
```batch
@echo off
echo Shepherd Production Startup
echo ======================

REM Check if GPU is available
python -c "import torch; exit(0 if torch.cuda.is_available() else 1)" >nul 2>&1
if %errorlevel% == 0 (
    echo GPU mode: AVAILABLE - starting with CUDA...
    uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
) else (
    echo GPU mode: UNAVAILABLE - starting with CPU...
    venv311\Scripts\activate && uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
)
```

### Monitoring Performance
```python
# Add to backend for performance tracking
import time
import psutil
import torch

def get_system_stats():
    stats = {
        'cpu_usage': psutil.cpu_percent(),
        'memory_used': psutil.virtual_memory().percent,
        'gpu_available': torch.cuda.is_available()
    }
    if torch.cuda.is_available():
        stats['gpu_memory'] = torch.cuda.get_device_properties(0).total_memory
        stats['gpu_memory_used'] = torch.cuda.memory_allocated(0)
    return stats
```

This comprehensive setup allows Shepherd to scale from single-user church installations to enterprise media production environments while maintaining optimal performance for each use case.
