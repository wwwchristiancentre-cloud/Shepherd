# Shepherd

Local-first church media production system built with Electron, Next.js, and FastAPI.

## Features

- **Project Management**: Create and manage church media production projects locally
- **Transcription Service**: AI-powered transcription using Whisper (stub implementation)
- **Local Storage**: All data stored locally in SQLite
- **Cross-Platform**: Runs on Windows, macOS, and Linux

## Quick Start

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.10+
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

3. **Set up Python backend**
   ```bash
   # Navigate to backend directory
   cd backend

   # Create virtual environment
   python -m venv venv

   # Activate virtual environment
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate

   # Install dependencies
   pip install -r requirements.txt

   # Return to root
   cd ..
   ```

4. **Set up Whisper models (optional for MVP)**
   - For full transcription functionality, download Whisper models from Hugging Face
   - Place model files in `backend/models/` directory

### Running the Application

```bash
# Start development mode (Electron app with backend and frontend)
npm run dev
```

This will:
- Start the Next.js frontend on http://localhost:3000
- Start the FastAPI backend on http://localhost:8000
- Launch the Electron app

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

- `GET /projects` - List all projects
- `POST /projects` - Create new project

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

## Whisper Models

Download from Hugging Face:
- Base model: https://huggingface.co/openai/whisper-base
- Other sizes available (small, medium, large)

Place downloaded models in `backend/models/` directory.

## Troubleshooting

### Port conflicts
Make sure ports 3000 and 8000 are available.

### Python virtual environment issues
Ensure you activate the virtual environment before running the backend.

### Electron not starting
Check Node.js and Electron versions compatibility.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes
4. Submit a pull request

## License

[Add license information]
