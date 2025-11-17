#!/usr/bin/env python3
"""
Test script to verify global Shepherd environment setup
Run this after installing dependencies globally
"""

import sys
import torch
import platform

def test_global_setup():
    print("🔍 GLOBAL ENVIRONMENT DIAGNOSTICS")
    print("=" * 50)

    # System info
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print()

    # GPU/CUDA status
    print("🎮 GPU & CUDA STATUS:")
    print(f"  PyTorch CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"  CUDA version: {torch.version.cuda}")
        print(f"  Device count: {torch.cuda.device_count()}")
        print(f"  Device name: {torch.cuda.get_device_name(0)}")
    else:
        print("  ❌ CUDA not available - PyTorch installed without GPU support")
    print(f"  PyTorch location: {torch.__file__}")
    print()

    # Package availability
    print("📦 PACKAGE AVAILABILITY:")
    packages = [
        'fastapi',
        'whisper',
        'numba',
        'uvicorn',
        'aiosqlite',
        'pydantic',
        'python_multipart'
    ]

    available = 0
    total = len(packages)

    for pkg in packages:
        try:
            __import__(pkg)
            print(f"  ✅ {pkg}")
            available += 1
        except ImportError:
            print(f"  ❌ {pkg} (missing)")

    print(f"\n📊 PACKAGES: {available}/{total} available globally")
    print()

    # Whisper model test
    print("🤖 WHISPER MODEL STATUS:")
    try:
        import whisper
        print("  ✅ Whisper library available")

        # Test existing model
        model_path = "./backend/models/medium.pt"
        import os
        if os.path.exists(model_path):
            size_mb = os.path.getsize(model_path) / (1024**2)
            print(f"  📁 Model cached: {size_mb:.1f} MB")
        else:
            print("  ⚠️  Model file not found - needs downloading")
    except ImportError:
        print("  ❌ Whisper not available")

    print()
    print("🚀 SUMMARY:")
    success = True

    if not torch.cuda.is_available():
        print("  ⚠️  GPU not detected (PyTorch needs CUDA version)")
        success = False

    if available != total:
        print("  ⚠️  Some packages missing from global Python")
        success = False

    if success:
        print("  ✅ GLOBAL ENVIRONMENT READY FOR GPU PRODUCTION")
        print()
        print("  To run Shepherd in GPU mode:")
        print("  uvicorn backend.app.main:app --host 0.0.0.0 --port 8000")
    else:
        print("  ❌ ISSUES FOUND - Check package installations")

if __name__ == "__main__":
    test_global_setup()
