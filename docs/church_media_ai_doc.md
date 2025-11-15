**Project Title:** Shepherd (Smart Holistic Engine for Production, Handling, Editing, Routing, and Delivery)

---

### 1. **Project Overview**
Shepherd is a local-first, AI-assisted production system designed for churches and live event media teams. It acts as a bridge between live production tools (Reaper, OBS, Yamaha console) and post-production workflows (editing, export, publishing). Shepherd automates transcription, segment detection, content generation, and media organization.

---

### 2. **Core Goals**
- Integrate live audio/video capture (via Dante, Reaper, OBS).
- Automatically organize, tag, and label projects by event/date/type.
- Generate multi-format content outputs (sermons, podcasts, reels, highlight clips).
- Leverage local AI models for transcription, summarization, and tagging.
- Minimize human error and streamline the church media workflow.

---

### 3. **System Architecture**

#### **Frontend (Desktop App)**
- **Framework:** Electron + Next.js (React UI within desktop shell)
- **UI Elements:**
  - Dashboard (Project overview, current sessions, quick actions)
  - Project Manager (Folder view, metadata, export paths)
  - Transcription Panel (Whisper outputs, timestamps, speaker detection)
  - Segment Editor (Visual timeline, auto-detected sections like Sermon/Worship/Announcements)
  - AI Assistant (Chat or side panel powered by local LLM)
  - Export Manager (Choose export type: Sermon, Reels, Podcast, etc.)

#### **Backend (Local Server)**
- **Framework:** FastAPI (Python)
- **Responsibilities:**
  - Handle Reaper/OBS/FFmpeg automation
  - Process audio/video files
  - Run local Whisper transcription
  - Connect with local LLM (Mistral/Llama) for summaries, titles, and descriptions
  - Maintain SQLite/Postgres database for projects and metadata
  - Expose REST endpoints for Electron frontend

#### **AI & Processing Layer**
- **Speech-to-Text:** Whisper (local)
- **Language Understanding:** Llama 3.1 8B or Mistral 7B (GGUF quantized)
- **Search/Indexing:** Chroma or Qdrant (vector database)
- **Automation:** FFmpeg + ReaScript (Reaper scripting) + OBS WebSockets

---

### 4. **Minimum Usable Version (MVP)**
The MVP focuses on automating repetitive tasks for audio and media management.

**MVP Features:**
1. Project creation & folder structure automation.
2. Local transcription using Whisper (auto audio import from Reaper session folder).
3. Sermon segmentation based on silence/energy detection.
4. Summary, title, and description generation using local LLM.
5. Export pipeline:
   - Audio cleanup (normalize, noise reduction)
   - Export sermon mix + podcast version
6. Dashboard with basic project management (list, rename, archive).

**MVP Stack:**
- **Frontend:** Electron + Next.js
- **Backend:** FastAPI + Python scripts
- **Storage:** SQLite + local file system
- **Models:** Whisper (medium), Llama/Mistral (7B GGUF)
- **Automation:** FFmpeg, ReaScript (for Reaper control)

**Hardware Fit:** GTX 1080 (8GB VRAM) running quantized models locally.

---

### 5. **Future Version (v2.0 and beyond)**

#### **v2.0 Goals:**
- Multi-user collaboration with local network sync (e.g., media team access)
- Scene detection in video (AI-based visual segmentation)
- Auto-thumbnail generation (via vision model)
- AI audio cleanup (dereverb, noise, spectral gating)
- Sermon database with searchable archives (vector search)
- Analytics dashboard (viewer engagement, sermon trends)
- Smart scheduling & reminders for editing/export deadlines

#### **v3.0 Goals:**
- Real-time stream companion: AI-assisted audio monitoring and scene switching suggestions for OBS.
- Integration with cloud storage and YouTube API for direct upload.
- Fine-tuned LLM on church-specific dataset for improved contextual summaries.
- Web/mobile dashboard for remote management.

---

### 6. **Data Flow (Simplified)**
```
[Yamaha Mixer] → [Dante → Reaper Multitrack] → [Whisper STT] → [AI Segmentation + Labeling]
  → [LLM Summarization + Metadata] → [Export via FFmpeg] → [Dashboard Display + Archive]
```

---

### 7. **Development Phases**

**Phase 1: Infrastructure Setup**
- Folder structure automation (already built via PowerShell)
- Install REAPER, OBS, FFmpeg, Whisper, local LLM backend
- FastAPI + Electron scaffolding

**Phase 2: Core AI Integration**
- Whisper integration with FastAPI endpoints
- LLM-based text generation
- Audio segmentation pipeline

**Phase 3: User Interface & Automation**
- Build dashboard UI in Electron/Next.js
- Integrate project creation, Whisper transcription, and export flow

**Phase 4: Smart Automation**
- Auto export + file routing
- OBS & Reaper scripting automation

**Phase 5: Advanced AI Layer**
- Scene detection, thumbnail generation, metadata analytics

---

### 8. **Example Workflow**
1. Create new project → folder + metadata auto-generated.
2. Import or record audio via Reaper → save to project folder.
3. Whisper transcribes audio → auto-detects segments.
4. LLM summarizes + titles each segment.
5. Export pipeline cleans audio and creates deliverables.
6. Dashboard displays results; user can review, edit, and publish.

---

### 9. **Licensing & Cost Notes**
- **Free/Local:** Whisper, Llama, Mistral (quantized), FFmpeg, FastAPI, Electron, Next.js.
- **Optional Paid:** DaVinci Resolve, premium plugins, GPU cloud scaling.
- **Estimated local cost:** $0 per month (excluding electricity & hardware).

---

### 10. **Vision Summary**
Shepherd transforms a high-performance church media setup into a unified creative system. It automates technical drudgery, structures the creative process, and enables media teams to focus on storytelling and ministry impact rather than cables and exports.

---

**Next Steps:**
1. Initialize FastAPI backend.
2. Scaffold Electron + Next.js UI.
3. Connect Whisper + LLM integration.
4. Prototype local dashboard for transcription and summaries.

---

