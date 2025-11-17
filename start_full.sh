#!/bin/bash
# Shepherd Full Stack Development Startup Script
# This starts both frontend and backend in one terminal

echo "🚀 Starting Shepherd Full Stack Development"
echo "=========================================="
echo

# Check if we're on Windows (bash scripts work with Git Bash and WSL)
if [[ "$OS" == "Windows_NT" ]]; then
    echo "🌟 Detected Windows - using py launcher for Python 3.11"
    PY_CMD="py -3.11"
else
    PY_CMD="python3.11"
fi

# Check GPU status
echo "🔍 Checking GPU availability..."
$PY_CMD -c "
import torch
if torch.cuda.is_available():
    print(f'🎮 GPU: {torch.cuda.get_device_name(0)} ({torch.cuda.get_device_properties(0).total_memory // (1024**3)}GB VRAM)')
    print('✅ GPU acceleration will be used')
else:
    print('⚠️  No GPU detected - using CPU mode')
"

echo
echo "📡 Starting Services:"
echo "  🌐 Frontend: http://localhost:3000 (Next.js)"
echo "  🔧 Backend:  http://localhost:8000 (FastAPI + Whisper)"
echo "  📊 API Docs: http://localhost:8000/docs"
echo
echo "Press Ctrl+C to stop both services"
echo
echo "=========================================="

# Use concurrently to run both services in the same terminal
npx concurrently \
  "\"cd renderer && npx next dev\"" \
  "\"$PY_CMD -m uvicorn backend.app.main:app --reload --host 0.0.0.0\""
