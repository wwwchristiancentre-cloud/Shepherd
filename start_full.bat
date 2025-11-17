@echo off
REM Shepherd Full Stack Development Startup Script (Windows)
REM This starts both frontend and backend in one terminal

echo 🚀 Starting Shepherd Full Stack Development
echo ==========================================
echo.

REM Check GPU status with Python 3.11
echo 🔍 Checking GPU availability...
py -3.11 -c "
import torch
if torch.cuda.is_available():
    print('🎮 GPU: %s (%dGB VRAM)' % (torch.cuda.get_device_name(0), torch.cuda.get_device_properties(0).total_memory // (1024**3)))
    print('✅ GPU acceleration will be used')
else:
    print('⚠️  No GPU detected - using CPU mode')
"

echo.
echo 📡 Starting Services:
echo   🌐 Frontend: http://localhost:3000 (Next.js)
echo   🔧 Backend:  http://localhost:8000 (FastAPI + Whisper)
echo   📊 API Docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop both services
echo.
echo ==========================================

REM Start both services concurrently
npx concurrently "^"cd renderer && npx next dev^"" "^"py -3.11 -m uvicorn backend.app.main:app --reload --host 0.0.0.0^""
