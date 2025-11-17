# Shepherd

**🏆 FR-002 IMPLEMENTED** - Local AI-powered church media production system

Local-first church media production system built with Electron, Next.js, and FastAPI. Features local Whisper transcription with GPU acceleration and complete project management.

## Features

- **Project Management**: Create and manage church media production projects locally
- **Transcription Service**: AI-powered transcription using local Whisper models with timestamps
- **Local AI Processing**: All transcription happens locally - no data sent to external APIs
- **Local Storage**: All data stored locally in SQLite
- **Cross-Platform**: Runs on Windows, macOS, and Linux

## Quick Start

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.11 (required for Whisper compatibility)
- **FFmpeg** (for media processing)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd shepherd
   ```

2. **Set up Node.js dependencies**
   ```bash
   npm install
   ```

3. **Set up Python backend with Whisper support**
   ```bash
   # Create Python 3.11 virtual environment (compatible with Whisper)
   python -m venv venv311

   # Activate virtual environment
   # On Windows:
   venv311\Scripts\activate
   # On macOS/Linux:
   source venv311/bin/activate

   # Install core backend dependencies
   pip install fastapi uvicorn[standard] python-multipart aiosqlite pydantic

   # Install Whisper and its ML dependencies
   pip install torch>=2.0.0 numpy>=1.21.0
   pip install --no-deps openai-whisper

   # Verify Whisper import
   python -c "import whisper; print('Whisper available')"
   ```

4. **Whisper Setup & Performance Options**

   ### Basic Setup (Recommended for Most Users)
   - Follow steps 1-3 above to install in virtual environment
   - Models downloaded automatically on first transcription (~1.5GB)

   ### Performance Options

   #### CPU Mode (Default - Works Everywhere)
   - Whisper runs on CPU - reliable and compatible
   - Suitable for churches, home users, any hardware
   - Performance: ~1-2 minutes for 45-minute sermon
   - ✅ Zero configuration, just works

#### Production GPU Mode (Fastest - Python 3.11 Global)
```bash
# Step 1: Verify setup (all packages installed globally in Python 3.11)
python test_global_setup.py  # Should show all ✅

# Step 2: Start with GPU acceleration
python global_start.py  # Uses Python 3.11 automatically
# OR: py -3.11 global_start.py
# OR: py -3.11 -m uvicorn backend.app.main:app --reload

# Check GPU working: http://127.0.0.1:8000/logs
```
- Performance: ~10-30 seconds for 45-minute sermon (10x faster!)
- All packages in global Python 3.11 (no venv conflicts)

### Setup Scenarios for Different Users

#### Scenario 1: End User (Church Staff - CPU Only)
- Follow basic installation steps 1-3
- No special hardware requirements
- Reliable performance for church recordings
- Zero configuration - "it just works"

#### Scenario 2: Developer (Basic Development)
- Same as End User setup
- Use venv311 for all development
- Focus on feature development and testing

#### Scenario 3: Performance User (Church with NVIDIA GPU)
- Follow basic installation + GPU setup above
- Requires: NVIDIA GPU + CUDA drivers installed
- Production: Run backend globally for GPU speed
- Development: Still use venv311 for stability

#### Scenario 4: Enterprise/System Admin
- Global PyTorch + GPU for best performance
- Can port existing Whisper models to new systems
- Use `--download_root` parameter to specify model location
- Ideal for multi-user environments

#### Advanced: Custom Model Location
```bash
# Store models on external drive
uvicorn backend.app.main:app --env WHISPER_MODEL_ROOT=/external/drive/models
```
- Supports network storage, external drives, etc.
- Useful for institutional deployments

**📖 For detailed performance optimization and troubleshooting, see:** `docs/Performance_Configuration_Guide.md`

### Running the Application

#### Option 1: Full Stack Development (Recommended)
```bash
# Start BOTH frontend + backend in one terminal
npm run dev
```

#### Option 2: Full Stack Scripts
```bash
# Windows
./start_full.bat

# Linux/macOS
./start_full.sh
```

This will:
- 🌐 Start Next.js frontend on http://localhost:3000
- 🔧 Start FastAPI backend on http://localhost:8000 (with GPU acceleration)
- 📊 Auto-detect and use GPU/CPU based on available hardware
- 📋 Show service status and access URLs

#### Option 3: Manual Component Control
```bash
# Run services separately for development/debugging
cd renderer && npx next dev                    # Frontend only
py -3.11 -m uvicorn backend.app.main:app --reload  # Backend only (GPU)
npm run electron                             # Electron app only
```

#### Option 4: Production GPU Mode
```bash
# Maximum performance (global setup only)
python global_start.py
```

### Manual Development

If you prefer to run components separately:

```bash
# Terminal 1: Start Next.js frontend
cd renderer
npm run dev

# Terminal 2: Start FastAPI backend
cd backend
python -m uvicorn app.main:app --reload

# Terminal 3: Run Electron app
npm run electron
```

## Project Structure

```
/
├── backend/               # FastAPI Python Backend
│   ├── app/
│   │   ├── api/           # API endpoints
│   │   ├── core/          # Configuration and database
│   │   ├── models/        # Pydantic models
│   │   └── services/      # Business logic (Whisper, FFmpeg)
│   ├── models/            # AI model storage directory
│   └── requirements.txt
├── renderer/              # Next.js Frontend
│   ├── app/               # Next.js app directory
│   └── ...
├── main/                  # Electron Main Process
│   ├── main.ts            # Entry point
│   └── preload.js         # Preload script
├── docs/                  # Documentation
└── package.json           # Root configuration
```

## API Endpoints

### Projects
- `GET /projects` - List all projects
- `POST /projects` - Create new project

### Transcription
- `POST /transcription` - Upload and transcribe audio file (accepts project_id)
  - Supports: MP3, WAV, M4A, FLAC, OGG
  - Returns: Full transcript, timestamped segments, metadata

## Data Storage

- **Projects Database**: `shepherd.db` (SQLite)
- **Project Files**: `~/ShepherdProjects/{ProjectName}/`
  - `Audio/` - Audio files
  - `Video/` - Video files
  - `Exports/` - Exported productions
  - `Transcripts/` - Generated transcriptions

## Development

### Adding new features

1. Backend changes in `backend/app/`
2. Frontend changes in `renderer/app/`
3. Electron main process in `main/`

### Building for production

```bash
npm run build
```

## FFmpeg Installation

### Windows
- Download from https://ffmpeg.org/download.html#build-windows
- Add to PATH or place binaries in system PATH
- Alternatively, use Chocolatey: `choco install ffmpeg`

### macOS
```bash
brew install ffmpeg
```

### Linux
```bash
sudo apt install ffmpeg  # Ubuntu/Debian
```

## Whisper Configuration

### Model Scope: Virtual Environment Only
Currently, Whisper is installed only within the `venv311` virtual environment. This means:

- ✅ **Within the Shepherd project**: Whisper is available when `venv311` is activated
- ❌ **Outside the Shepherd project**: Whisper is not available globally

To use Whisper globally (across all Python projects):
```bash
# Install globally (not recommended unless you understand dependency conflicts)
pip install openai-whisper
```

### Models
Whisper models are automatically downloaded on first use:
- The medium model (~1.5GB) provides good accuracy/speed balance
- Models are cached locally in the `backend/models/` directory
- First transcription may take longer due to model download

## Troubleshooting

### Port conflicts
Make sure ports 3000 and 8000 are available.

### Python virtual environment issues
- Ensure you activate the correct virtual environment: `venv311\Scripts\activate`
- Verify Python version: `python --version` should show Python 3.11.x
- If activation fails, check the path: should be `d:\PROJECTS\2025\Dev\Shepherd\venv311\Scripts\activate`

### Whisper installation issues
- **"numba not compatible with Python 3.14"**: Use Python 3.11 specifically
- **Import failure**: Run verification command: `python -c "import whisper; print('Whisper available')"`
- **First transcription slow**: Model download takes time and requires internet
- **Disk space**: Ensure 5GB+ free space for models

### Electron not starting
Check Node.js and Electron versions compatibility.

### Backend won't start
- Verify all Python packages installed: `pip list | grep -E "(fastapi|uvicorn|whisper|torch)"`
- Check for missing dependencies: `pip install --upgrade pip`
- Ensure environment activated before running uvicorn

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes
4. Submit a pull request

## License

[Add license information]
