#!/usr/bin/env python3
"""
Global Shepherd GPU Production Startup Script
Always use Python 3.11 globally for optimal GPU performance
"""

import subprocess
import sys
import os

def main():
    print("🚀 Shepherd GPU Production Startup")
    print("=" * 50)

    # Ensure we're using Python 3.11
    if sys.version_info[:2] != (3, 11):
        print(f"⚠️  Wrong Python version: {sys.version}")
        print("Run with: py -3.11 global_start.py")
        return

    print(f"✅ Using Python {sys.version.split()[0]}")

    # Check GPU status
    try:
        import torch
        if torch.cuda.is_available():
            print(f"🎮 GPU: {torch.cuda.get_device_name(0)} ({torch.cuda.get_device_properties(0).total_memory // (1024**3)}GB VRAM)")
        else:
            print("⚠️  No GPU detected - falling back to CPU")
    except ImportError:
        print("❌ PyTorch not available")

    print()
    print("📡 Starting Global Shepherd Backend...")
    print("🌐 URL: http://127.0.0.1:8000")
    print("🎙️  API: http://127.0.0.1:8000/transcription")
    print("📊 Docs: http://127.0.0.1:8000/docs")
    print()
    print("Press Ctrl+C to stop")
    print()

    # Start the server
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "backend.app.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ], cwd=os.path.dirname(__file__))
    except KeyboardInterrupt:
        print("\n👋 Server stopped")

if __name__ == "__main__":
    main()
