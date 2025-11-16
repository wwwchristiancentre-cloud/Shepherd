'use client'

import { useState, useEffect } from 'react'

type Project = {
  id: number;
  name: string;
  created_at: string;
}

type TranscriptSegment = {
  start: number;
  end: number;
  text: string;
}

type TranscriptResult = {
  transcripts: Array<{ text: string }>;
  segments: TranscriptSegment[];
  metadata?: {
    model: string;
    language: string;
    duration: number;
    processing_time: number;
  };
  error?: string;
}

function formatTimestamp(seconds: number): string {
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}

export default function Home() {
  const [projects, setProjects] = useState<Project[]>([])
  const [showModal, setShowModal] = useState(false)
  const [newProjectName, setNewProjectName] = useState('')
  const [transcript, setTranscript] = useState<TranscriptResult | null>(null)
  const [isTranscribing, setIsTranscribing] = useState(false)

  useEffect(() => {
    fetchProjects()
  }, [])

  async function fetchProjects() {
    try {
      const res = await fetch('http://localhost:8000/projects')
      if (res.ok) {
        const data = await res.json()
        setProjects(data)
      } else {
        console.error('Failed to fetch projects')
      }
    } catch (error) {
      console.error('Error fetching projects:', error)
    }
  }

  async function createProject() {
    if (!newProjectName.trim()) return
    try {
      const res = await fetch('http://localhost:8000/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newProjectName.trim() })
      })
      if (res.ok) {
        await fetchProjects()
        setShowModal(false)
        setNewProjectName('')
      } else {
        const error = await res.text()
        alert('Error creating project: ' + error)
      }
    } catch (error) {
      console.error('Error creating project:', error)
      alert('Error creating project')
    }
  }

  async function handleFileUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (!file) return

    // Validate file type
    if (!file.name.toLowerCase().match(/\.(mp3|wav|m4a|flac|ogg)$/)) {
      alert('Please select a supported audio file: MP3, WAV, M4A, FLAC, or OGG')
      return
    }

    setIsTranscribing(true)
    setTranscript(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('http://localhost:8000/transcription/', {
        method: 'POST',
        body: formData,
      })

      if (response.ok) {
        const result: TranscriptResult = await response.json()
        setTranscript(result)
      } else {
        const errorText = await response.text()
        alert('Transcription failed: ' + errorText)
      }
    } catch (error) {
      console.error('Upload error:', error)
      alert('Error uploading file for transcription')
    } finally {
      setIsTranscribing(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <header className="bg-gray-800 p-4 shadow-lg">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold text-blue-400">Shepherd Projects</h1>
          <button
            onClick={() => setShowModal(true)}
            className="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-md font-semibold transition-colors"
          >
            New Project
          </button>
        </div>
      </header>
      <main className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((project) => (
            <div key={project.id} className="bg-gray-800 p-4 rounded-lg shadow-lg hover:shadow-xl transition-shadow">
              <h2 className="text-xl font-semibold mb-2">{project.name}</h2>
              <p className="text-gray-400 text-sm">
                Created: {new Date(project.created_at).toLocaleDateString()}
              </p>
              <div className="mt-4 flex gap-2">
                <button className="bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded text-sm">
                  Open
                </button>
              </div>
            </div>
          ))}
        </div>
        {projects.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-400 text-lg">No projects yet. Create your first project to get started.</p>
          </div>
        )}

        {/* Transcription Section */}
        <div className="mt-12">
          <h2 className="text-2xl font-bold mb-6 text-blue-400">Audio Transcription</h2>

          {/* Upload Section */}
          <div className="bg-gray-800 p-6 rounded-lg mb-6">
            <h3 className="text-lg font-semibold mb-4">Upload Audio File</h3>
            <p className="text-gray-400 text-sm mb-4">
              Upload an audio file (MP3, WAV, M4A, FLAC, or OGG) to transcribe it using local Whisper AI.
              Files are processed securely on your machine.
            </p>
            <input
              type="file"
              accept=".mp3,.wav,.m4a,.flac,.ogg"
              onChange={handleFileUpload}
              disabled={isTranscribing}
              className="block w-full text-sm text-gray-300 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700 disabled:opacity-50"
            />
            {isTranscribing && (
              <div className="mt-4 flex items-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500 mr-2"></div>
                <span className="text-blue-400">Transcribing audio with local Whisper model...</span>
              </div>
            )}
          </div>

          {/* Transcript Display */}
          {transcript && (
            <div className="bg-gray-800 p-6 rounded-lg">
              <h3 className="text-lg font-semibold mb-4 text-green-400">Transcription Results</h3>

              {transcript.error ? (
                <div className="bg-red-900/50 border border-red-500 rounded-md p-4">
                  <p className="text-red-400">Error: {transcript.error}</p>
                </div>
              ) : (
                <>
                  {/* Metadata */}
                  {transcript.metadata && (
                    <div className="bg-gray-700 rounded-md p-4 mb-4 flex flex-wrap gap-4 text-sm">
                      <div><strong>Model:</strong> {transcript.metadata.model}</div>
                      <div><strong>Language:</strong> {transcript.metadata.language || 'Auto-detected'}</div>
                      <div><strong>Duration:</strong> {transcript.metadata.duration?.toFixed(1)}s</div>
                      <div><strong>Processing Time:</strong> {transcript.metadata.processing_time?.toFixed(1)}s</div>
                    </div>
                  )}

                  {/* Full Transcript */}
                  <div className="mb-6">
                    <h4 className="font-semibold mb-2">Full Transcript:</h4>
                    <p className="text-gray-300 leading-relaxed bg-gray-700 p-4 rounded-md">
                      {transcript.transcripts[0]?.text || 'No transcript available'}
                    </p>
                  </div>

                  {/* Detailed Segments */}
                  {transcript.segments && transcript.segments.length > 0 && (
                    <div>
                      <h4 className="font-semibold mb-3">Detailed Segments:</h4>
                      <div className="space-y-2 max-h-96 overflow-y-auto">
                        {transcript.segments.map((segment, index) => (
                          <div key={index} className="bg-gray-700 p-3 rounded-md flex items-start gap-4">
                            <div className="text-xs text-gray-400 font-mono min-w-[80px]">
                              {formatTimestamp(segment.start)} - {formatTimestamp(segment.end)}
                            </div>
                            <div className="flex-1 text-gray-200">
                              {segment.text.trim()}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      </main>
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 p-6 rounded-lg w-96 max-w-full mx-4">
            <h2 className="text-2xl font-bold mb-4 text-blue-400">Create New Project</h2>
            <input
              type="text"
              value={newProjectName}
              onChange={(e) => setNewProjectName(e.target.value)}
              className="w-full p-3 bg-gray-700 text-white rounded-md mb-6 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter project name"
              onKeyPress={(e) => e.key === 'Enter' && createProject()}
            />
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowModal(false)}
                className="bg-gray-600 hover:bg-gray-500 px-4 py-2 rounded font-medium transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={createProject}
                disabled={!newProjectName.trim()}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed px-4 py-2 rounded font-medium transition-colors"
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
