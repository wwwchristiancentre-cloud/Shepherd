---
title: Persistence & Storage
status: authoritative
ai_processed: true
---

# Persistence & Storage Overview

This document explains how data is persisted in Shepherd:

- **Database (SQLite via `aiosqlite`)** for project metadata.
- **Filesystem (User Home)** for project assets and transcripts.
- **Filesystem Cache** for transcription results by audio hash.

---

## Components & Responsibilities

- **Database (SQLite, file: `shepherd.db`)**
  - Stores: `projects` table (id, name, created_at).
  - Location: created in the FastAPI server's current working directory.
  - Initialization: table auto-created on app startup.

- **Project Folder Structure (User home)**
  - Root: `~/ShepherdProjects/<ProjectName>/`
  - Subfolders: `Audio/`, `Video/`, `Exports/`, `Transcripts/`
  - Behavior: created when a project is created via API.

- **Transcripts Storage (JSON)**
  - Path: `~/ShepherdProjects/<ProjectName>/Transcripts/`
  - Pattern: `<audio_stem>_transcript_and_segments.json`

- **Transcription Cache (JSON)**
  - Path: `~/ShepherdProjects/.cache/`
  - Pattern: `<sha256_of_audio>.json`
  - Purpose: short-circuit re-processing if the same audio is submitted again.

---

## Source of Truth in Code

- **SQLite usage**
  - `backend/app/main.py`
    - Creates/opens `shepherd.db`
    - Ensures `projects` table exists (on startup)
  - `backend/app/api/projects.py`
    - Reads/writes projects via `aiosqlite.connect("shepherd.db")`

- **Filesystem usage**
  - `backend/app/api/projects.py`
    - Creates `~/ShepherdProjects/<ProjectName>` and subfolders
    - Accepts uploads to `Audio/`
  - `backend/app/api/transcription.py`
    - Saves transcripts to `Transcripts/`
    - Maintains cache in `~/ShepherdProjects/.cache/`

---

## Database Details

- **Engine**: SQLite (async driver: `aiosqlite`)
- **File name**: `shepherd.db`
- **Working-directory dependent**: The DB file is created where the server process is started. Common locations:
  - Repo root: `.../Shepherd/shepherd.db`
  - Backend root: `.../Shepherd/backend/shepherd.db`
  - App dir: `.../Shepherd/backend/app/shepherd.db`
- **Schema (current)**
  - `projects(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)`

### How to find the DB file locally (Windows PowerShell)

```powershell
Get-ChildItem -Path . -Filter shepherd.db -Recurse -ErrorAction SilentlyContinue
```

Or search for common SQLite extensions:

```powershell
Get-ChildItem -Path . -Include *.db,*.sqlite,*.sqlite3 -Recurse -ErrorAction SilentlyContinue
```

---

## File Storage Layout

- **Root**: `~/ShepherdProjects/`
- **Per-project**: `~/ShepherdProjects/<ProjectName>/`
  - `Audio/` — uploaded audio files
  - `Video/` — reserved for video assets
  - `Exports/` — reserved for future export artifacts
  - `Transcripts/` — saved transcript JSON files
- **Cache**: `~/ShepherdProjects/.cache/` — transcription cache by audio hash

Notes:
- On Windows, `~` maps to the current user profile, e.g. `C:\Users\<UserName>`.
- Filenames may be timestamp-suffixed to avoid collisions on upload.

---

## Configuration & Overrides

Current code uses hardcoded paths:
- DB path: relative `"shepherd.db"`
- Project root and cache: `Path.home() / "ShepherdProjects"`

Recommended improvements (non-breaking suggestions):
- Add `SHEPHERD_DB_PATH` env var to override DB file location.
- Add `SHEPHERD_DATA_ROOT` env var to override `~/ShepherdProjects`.
- Default to `backend/data/shepherd.db` when no env is provided to avoid cwd ambiguity.

Example configuration strategy (illustrative):

```python
# config.py (example)
from pathlib import Path
import os

DATA_ROOT = Path(os.getenv("SHEPHERD_DATA_ROOT", Path.home() / "ShepherdProjects"))
DB_PATH = Path(os.getenv("SHEPHERD_DB_PATH", Path(__file__).resolve().parents[1] / "data" / "shepherd.db"))
```

---

## Operational Notes

- Starting the API from different folders will produce different `shepherd.db` files. Pin a single location via env/config.
- Deleting a project removes its DB row and tries to delete its folder under `~/ShepherdProjects/<ProjectName>`.
- Transcription cache entries are independent of projects and keyed solely by audio content hash.

---

## Troubleshooting

- **"I can't find shepherd.db"**
  - The server likely started with a different working directory. Use the PowerShell search above or make the DB path explicit via env/config.

- **Project folders not created**
  - Ensure the `create project` API was called successfully (it creates folders and inserts the DB row).
  - Check permissions to write under your home directory.

- **Cache not being hit**
  - Cache key is SHA-256 of the audio file content. Any change in content produces a new key.
  - Verify `.cache/<hash>.json` exists under `~/ShepherdProjects/`.

---

## Change Log Scope

This document tracks persistence behavior for:
- SQLite-backed project metadata
- Filesystem project storage
- Transcription cache behavior

Schema changes or path overrides should be reflected here.
