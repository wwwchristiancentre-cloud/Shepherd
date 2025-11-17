'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'

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

type SermonSegment = {
  start_time: number;
  end_time: number;
  duration: number;
  segment_type: string;
  confidence: number;
  text?: string;
  energy_level?: number;
  silence_duration?: number;
}

type SegmentationResult = {
  segments: SermonSegment[];
  audio_duration: number;
  total_segments: number;
  average_segment_duration: number;
  processing_time: number;
  confidence_threshold: number;
  transcription?: TranscriptResult;
}

type CombinedResult = {
  transcription: TranscriptResult;
  segmentation: {
    segments: SermonSegment[];
    audio_duration: number;
    total_segments: number;
    average_segment_duration: number;
    processing_time: number;
  };
}

function formatTimestamp(seconds: number): string {
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  const milliseconds = Math.floor((seconds % 1) * 100)
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}.${milliseconds.toString().padStart(2, '0')}`
}

function getSegmentTypeIcon(type: string): string {
  switch (type.toLowerCase()) {
    case 'sermon': return '🎤'
    case 'announcement': return '📢'
    case 'music': return '🎵'
    case 'prayer': return '🙏'
    default: return '❓'
  }
}

function getSegmentTypeColor(type: string): string {
  switch (type.toLowerCase()) {
    case 'sermon': return 'bg-blue-600'
    case 'announcement': return 'bg-yellow-600'
    case 'music': return 'bg-green-600'
    case 'prayer': return 'bg-purple-600'
    default: return 'bg-gray-600'
  }
}

export default function ProjectPage() {
  const params = useParams()
  const router = useRouter()
  const projectId = params.id as string

  const [project, setProject] = useState<{ id: number; name: string; created_at: string } | null>(null)
  const [transcript, setTranscript] = useState<TranscriptResult | null>(null)
  const [segmentation, setSegmentation] = useState<SegmentationResult | null>(null)
  const [combined, setCombined] = useState<CombinedResult | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [activeTab, setActiveTab] = useState<'overview' | 'transcription' | 'segmentation' | 'combined'>('overview')
  const [uploadedFileName, setUploadedFileName] = useState<string>('')
  const [existingTranscripts, setExistingTranscripts] = useState<any[]>([])
  const [showTranscriptsModal, setShowTranscriptsModal] = useState(false)

  useEffect(() => {
    fetchProject()
    loadLatestResults() // Load existing results on page load
  }, [projectId])

  async function loadLatestResults() {
    try {
      // Load transcripts from project (this includes segmentation results)
      const response = await fetch(`http://localhost:8000/projects/${projectId}/transcripts`)
      if (response.ok) {
        const data = await response.json()
        const transcripts = data.transcripts || []

        // Find the most recent result with segmentation
        const latestWithSegmentation = transcripts
          .filter((t: any) => t.has_segmentation && t.has_transcription)
          .sort((a: any, b: any) => new Date(b.modified).getTime() - new Date(a.modified).getTime())[0]

        if (latestWithSegmentation) {
          try {
            const transcriptResponse = await fetch(`http://localhost:8000/projects/${projectId}/transcripts/${latestWithSegmentation.filename}`)
            if (transcriptResponse.ok) {
              const fullData = await transcriptResponse.json()

              if (fullData.transcription && fullData.segmentation) {
                setCombined(fullData)
                setTranscript(fullData.transcription)
                if (fullData.source === 'segmentation_only') {
                  setSegmentation(fullData)
                }
              } else if (fullData.source === 'segmentation_only') {
                setSegmentation(fullData)
              } else {
                setTranscript(fullData)
              }
            }
          } catch (err) {
            console.log('Could not load latest results')
          }
        }
      }
    } catch (error) {
      console.log('No existing results to load')
    }
  }

  async function fetchProject() {
    try {
      const res = await fetch(`http://localhost:8000/projects/${projectId}`)
      if (res.ok) {
        const data = await res.json()
        setProject(data)
      } else {
        console.error('Failed to fetch project')
        router.push('/')
      }
    } catch (error) {
      console.error('Error fetching project:', error)
      router.push('/')
    }
  }

  async function handleTranscriptionUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (!file) return

    // Validate file type
    if (!file.name.toLowerCase().match(/\.(mp3|wav|m4a|flac|ogg)$/)) {
      alert('Please select a supported audio file: MP3, WAV, M4A, FLAC, or OGG')
      return
    }

    setIsProcessing(true)
    setTranscript(null)
    setUploadedFileName(file.name)
    setActiveTab('transcription')

    const formData = new FormData()
    formData.append('file', file)
    formData.append('project_id', projectId)

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
      setIsProcessing(false)
    }
  }

  async function handleSegmentationUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (!file) return

    // Validate file type
    if (!file.name.toLowerCase().match(/\.(mp3|wav|m4a|flac|ogg)$/)) {
      alert('Please select a supported audio file: MP3, WAV, M4A, FLAC, or OGG')
      return
    }

    setIsProcessing(true)
    setSegmentation(null)
    setUploadedFileName(file.name)
    setActiveTab('segmentation')

    const formData = new FormData()
    formData.append('file', file)
    formData.append('include_transcription', 'false')
    formData.append('project_id', projectId)

    try {
      const response = await fetch('http://localhost:8000/transcription/segment', {
        method: 'POST',
        body: formData,
      })

      if (response.ok) {
        const result: SegmentationResult = await response.json()
        console.log('Segmentation result:', result)
        console.log('Segments found:', result.segments?.length || 0)
        console.log('First segment:', result.segments?.[0])
        setSegmentation(result)
      } else {
        const errorText = await response.text()
        alert('Segmentation failed: ' + errorText)
      }
    } catch (error) {
      console.error('Upload error:', error)
      alert('Error uploading file for segmentation')
    } finally {
      setIsProcessing(false)
    }
  }

  async function handleCombinedUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (!file) return

    // Validate file type
    if (!file.name.toLowerCase().match(/\.(mp3|wav|m4a|flac|ogg)$/)) {
      alert('Please select a supported audio file: MP3, WAV, M4A, FLAC, or OGG')
      return
    }

    setIsProcessing(true)
    setCombined(null)
    setTranscript(null)
    setSegmentation(null)
    setUploadedFileName(file.name)
    setActiveTab('combined')

    const formData = new FormData()
    formData.append('file', file)
    formData.append('project_id', projectId)

    try {
      const response = await fetch('http://localhost:8000/transcription/transcribe-and-segment', {
        method: 'POST',
        body: formData,
      })

      if (response.ok) {
        const result: CombinedResult = await response.json()
        setCombined(result)
        setTranscript(result.transcription)
      } else {
        const errorText = await response.text()
        alert('Processing failed: ' + errorText)
      }
    } catch (error) {
      console.error('Upload error:', error)
      alert('Error uploading file')
    } finally {
      setIsProcessing(false)
    }
  }

  async function loadExistingTranscripts() {
    try {
      const response = await fetch(`http://localhost:8000/projects/${projectId}/transcripts`)
      if (response.ok) {
        const data = await response.json()
        setExistingTranscripts(data.transcripts || [])
        setShowTranscriptsModal(true)
      } else {
        alert('Failed to load transcripts')
      }
    } catch (error) {
      console.error('Error loading transcripts:', error)
      alert('Error loading transcripts')
    }
  }

  async function segmentExistingTranscript(transcriptFilename: string) {
    setIsProcessing(true)
    setSegmentation(null)
    setShowTranscriptsModal(false)
    setActiveTab('segmentation')

    try {
      const response = await fetch(`http://localhost:8000/projects/${projectId}/segment-existing`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transcript_filename: transcriptFilename })
      })

      if (response.ok) {
        const result = await response.json()
        console.log('Segmentation result:', result)  // Debug logging
        console.log('Segments found:', result.segments?.length || 0)
        console.log('First segment:', result.segments?.[0])
        setSegmentation(result)
      } else {
        const errorText = await response.text()
        alert('Segmentation failed: ' + errorText)
      }
    } catch (error) {
      console.error('Segmentation error:', error)
      alert('Error segmenting existing transcript')
    } finally {
      setIsProcessing(false)
    }
  }

  async function deleteProject() {
    try {
      const response = await fetch(`http://localhost:8000/projects/${projectId}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        alert('Project deleted successfully!')
        router.push('/') // Go back to projects list
      } else {
        const errorText = await response.text()
        alert('Failed to delete project: ' + errorText)
      }
    } catch (error) {
      console.error('Delete error:', error)
      alert('Error deleting project')
    }
  }

  if (!project) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 p-4 shadow-lg">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.push('/')}
              className="text-blue-400 hover:text-blue-300 text-sm"
            >
              ← Back to Projects
            </button>
            <div>
              <h1 className="text-2xl font-bold text-blue-400">{project.name}</h1>
              <p className="text-gray-400 text-sm">
                Created: {new Date(project.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>

          {/* Delete Project Button */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                if (confirm(`Are you sure you want to delete the "${project.name}" project? This will permanently delete all files and data in this project.`)) {
                  deleteProject();
                }
              }}
              className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded font-medium text-sm transition-colors"
              disabled={isProcessing}
            >
              🗑️ Delete Project
            </button>
          </div>
        </div>
      </header>

      <main className="p-6">
        {/* Upload Section */}
        <div className="bg-gray-800 p-6 rounded-lg mb-6">
          <h2 className="text-xl font-semibold mb-4 text-blue-400">Process Audio</h2>
          <p className="text-gray-400 text-sm mb-4">
            Upload audio files to this project for transcription, segmentation, or both.
          </p>

          {/* Existing Transcripts Button */}
          <div className="mb-6">
            <button
              onClick={loadExistingTranscripts}
              disabled={isProcessing}
              className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-600 px-4 py-2 rounded font-medium text-sm transition-colors"
            >
              📄 Segment Existing Transcripts
            </button>
            <p className="text-gray-500 text-xs mt-1">
              Run segmentation on previously transcribed audio without re-transcribing
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Transcription Only */}
            <div className="bg-gray-700 p-4 rounded-lg">
              <h3 className="font-semibold mb-2 text-green-400">📝 Transcription Only</h3>
              <p className="text-sm text-gray-300 mb-3">
                Generate timestamped transcript with Whisper AI
              </p>
              <input
                type="file"
                accept=".mp3,.wav,.m4a,.flac,.ogg"
                onChange={handleTranscriptionUpload}
                disabled={isProcessing}
                className="w-full text-sm text-gray-300 file:mr-3 file:py-2 file:px-3 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-green-600 file:text-white hover:file:bg-green-700 disabled:opacity-50"
              />
            </div>

            {/* Segmentation Only */}
            <div className="bg-gray-700 p-4 rounded-lg">
              <h3 className="font-semibold mb-2 text-orange-400">🎯 Smart Segmentation</h3>
              <p className="text-sm text-gray-300 mb-3">
                Automatically detect sermon segments and content types
              </p>
              <input
                type="file"
                accept=".mp3,.wav,.m4a,.flac,.ogg"
                onChange={handleSegmentationUpload}
                disabled={isProcessing}
                className="w-full text-sm text-gray-300 file:mr-3 file:py-2 file:px-3 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-orange-600 file:text-white hover:file:bg-orange-700 disabled:opacity-50"
              />
            </div>

            {/* Combined */}
            <div className="bg-gray-700 p-4 rounded-lg">
              <h3 className="font-semibold mb-2 text-purple-400">🚀 Transcription + Segmentation</h3>
              <p className="text-sm text-gray-300 mb-3">
                Get both transcript AND automatic segment suggestions
              </p>
              <input
                type="file"
                accept=".mp3,.wav,.m4a,.flac,.ogg"
                onChange={handleCombinedUpload}
                disabled={isProcessing}
                className="w-full text-sm text-gray-300 file:mr-3 file:py-2 file:px-3 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-purple-600 file:text-white hover:file:bg-purple-700 disabled:opacity-50"
              />
            </div>
          </div>

          {isProcessing && (
            <div className="mt-4 flex items-center justify-center">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 mr-3"></div>
              <span className="text-blue-400">
                {uploadedFileName ? `Processing "${uploadedFileName}"...` : 'Processing audio...'}
              </span>
            </div>
          )}
        </div>

        {/* Tabs Navigation */}
        {(transcript || segmentation || combined) && (
          <div className="mb-6">
            <div className="border-b border-gray-700">
              <nav className="-mb-px flex space-x-8">
                {transcript && (
                  <button
                    onClick={() => setActiveTab('transcription')}
                    className={`py-2 px-1 border-b-2 font-medium text-sm ${
                      activeTab === 'transcription'
                        ? 'border-green-400 text-green-400'
                        : 'border-transparent text-gray-500 hover:text-gray-300'
                    }`}
                  >
                    📝 Transcription
                  </button>
                )}
                {segmentation && (
                  <button
                    onClick={() => setActiveTab('segmentation')}
                    className={`py-2 px-1 border-b-2 font-medium text-sm ${
                      activeTab === 'segmentation'
                        ? 'border-orange-400 text-orange-400'
                        : 'border-transparent text-gray-500 hover:text-gray-300'
                    }`}
                  >
                    🎯 Segmentation
                  </button>
                )}
                {combined && (
                  <button
                    onClick={() => setActiveTab('combined')}
                    className={`py-2 px-1 border-b-2 font-medium text-sm ${
                      activeTab === 'combined'
                        ? 'border-purple-400 text-purple-400'
                        : 'border-transparent text-gray-500 hover:text-gray-300'
                    }`}
                  >
                    🚀 Combined Results
                  </button>
                )}
              </nav>
            </div>
          </div>
        )}

        {/* Tab Content */}
        {activeTab === 'transcription' && transcript && (
          <TranscriptionView transcript={transcript} />
        )}

        {activeTab === 'segmentation' && segmentation && (
          <SegmentationView segmentation={segmentation} />
        )}

        {activeTab === 'combined' && combined && (
          <CombinedView combined={combined} />
        )}
      </main>

      {/* Existing Transcripts Modal */}
      {showTranscriptsModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 p-6 rounded-lg w-full max-w-2xl max-h-[80vh] overflow-y-auto mx-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-blue-400">Select Transcript to Segment</h2>
              <button
                onClick={() => setShowTranscriptsModal(false)}
                className="text-gray-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            {existingTranscripts.length === 0 ? (
              <p className="text-gray-400">No existing transcripts found in this project.</p>
            ) : (
              <div className="space-y-3">
                {existingTranscripts.map((transcript) => (
                  <div key={transcript.filename} className="bg-gray-700 p-4 rounded-lg">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h3 className="font-medium text-white">{transcript.audio_filename}</h3>
                        <p className="text-sm text-gray-400">
                          {transcript.has_transcription ? "✅ Has transcription" : "❌ No transcription"}
                          {" • "}
                          {transcript.has_segmentation ? "✅ Already segmented" : "➕ Can add segmentation"}
                        </p>
                      </div>
                      <button
                        onClick={() => segmentExistingTranscript(transcript.filename)}
                        disabled={isProcessing}
                        className="bg-orange-600 hover:bg-orange-700 disabled:bg-gray-600 px-3 py-1 rounded text-sm font-medium transition-colors"
                      >
                        🎯 Segment
                      </button>
                    </div>
                    <div className="text-xs text-gray-500">
                      Duration: {transcript.audio_duration ? `${transcript.audio_duration.toFixed(1)}s` : "N/A"}
                      {" • "}
                      Size: {(transcript.size / 1024).toFixed(1)} KB
                      {" • "}
                      Modified: {new Date(transcript.modified).toLocaleDateString()}
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div className="mt-6 text-center">
              <button
                onClick={() => setShowTranscriptsModal(false)}
                className="bg-gray-600 hover:bg-gray-500 px-4 py-2 rounded font-medium transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// Component Views
function TranscriptionView({ transcript }: { transcript: TranscriptResult }) {
  return (
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
  )
}

function SegmentationView({ segmentation }: { segmentation: SegmentationResult }) {
  return (
    <div className="bg-gray-800 p-6 rounded-lg">
      <h3 className="text-lg font-semibold mb-4 text-orange-400">Segmentation Results</h3>

      {/* Debug Info */}
      <div className="mb-4 p-4 bg-gray-700 rounded flex justify-between items-center">
        <div className="text-sm">
          <strong>Debug:</strong> {segmentation.total_segments} segments found
        </div>
        <button
          onClick={() => {
            const jsonStr = JSON.stringify(segmentation, null, 2)
            const blob = new Blob([jsonStr], { type: 'application/json' })
            const url = URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = `segmentation_results_${Date.now()}.json`
            a.click()
            URL.revokeObjectURL(url)
          }}
          className="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-xs font-medium transition-colors"
        >
          📥 Export Raw JSON
        </button>
      </div>

      {/* Summary Stats */}
      <div className="bg-gray-700 rounded-md p-4 mb-6 flex flex-wrap gap-6 text-sm">
        <div><strong>Audio Duration:</strong> {segmentation.audio_duration.toFixed(1)}s</div>
        <div><strong>Detected Segments:</strong> {segmentation.total_segments}</div>
        <div><strong>Average Duration:</strong> {segmentation.average_segment_duration.toFixed(1)}s</div>
        <div><strong>Processing Time:</strong> {segmentation.processing_time.toFixed(1)}s</div>
      </div>

      {/* Segments List */}
      <div className="space-y-3">
        <h4 className="font-semibold mb-3">Detected Segments:</h4>
        {segmentation.segments.map((segment, index) => (
          <div key={index} className="bg-gray-700 p-4 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="text-lg">{getSegmentTypeIcon(segment.segment_type)}</span>
                <span className="font-medium">{segment.segment_type.charAt(0).toUpperCase() + segment.segment_type.slice(1)}</span>
                <span className={`px-2 py-1 rounded text-xs text-white ${getSegmentTypeColor(segment.segment_type)}`}>
                  {(segment.confidence * 100).toFixed(0)}% confident
                </span>
              </div>
              <div className="text-sm text-gray-400 font-mono">
                {formatTimestamp(segment.start_time)} - {formatTimestamp(segment.end_time)}
                <span className="ml-2">({segment.duration.toFixed(1)}s)</span>
              </div>
            </div>

            {segment.energy_level !== undefined && (
              <div className="text-sm text-gray-400 mb-1">
                Energy: {segment.energy_level.toFixed(1)} dB
              </div>
            )}

            {segment.text && (
              <div className="text-gray-300 bg-gray-600 p-3 rounded mt-2">
                "{segment.text}"
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Timeline Visualization */}
      <div className="mt-8">
        <h4 className="font-semibold mb-4">Timeline:</h4>
        <div className="bg-gray-700 p-4 rounded-lg">
          <div className="flex items-center mb-2 text-sm">
            {segmentation.segments.map((segment, index) => {
              const widthPercent = (segment.duration / segmentation.audio_duration) * 100
              return (
                <div
                  key={index}
                  className={`h-8 ${getSegmentTypeColor(segment.segment_type)} border-r border-gray-600 first:rounded-l last:rounded-r flex items-center justify-center text-white text-xs font-medium`}
                  style={{ width: `${widthPercent}%` }}
                  title={`${segment.segment_type}: ${segment.duration.toFixed(1)}s (${(segment.confidence * 100).toFixed(0)}%)`}
                >
                  {widthPercent > 10 && getSegmentTypeIcon(segment.segment_type)}
                </div>
              )
            })}
          </div>
          <div className="flex justify-between text-xs text-gray-400">
            <span>0:00</span>
            <span>{formatTimestamp(segmentation.audio_duration)}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

function CombinedView({ combined }: { combined: CombinedResult }) {
  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="bg-gray-800 p-6 rounded-lg">
        <h3 className="text-lg font-semibold mb-4 text-purple-400">📊 Processing Summary</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div className="bg-gray-700 p-3 rounded">
            <div className="text-gray-400">Audio Duration</div>
            <div className="font-semibold">{combined.segmentation.audio_duration.toFixed(1)}s</div>
          </div>
          <div className="bg-gray-700 p-3 rounded">
            <div className="text-gray-400">Segments Found</div>
            <div className="font-semibold">{combined.segmentation.total_segments}</div>
          </div>
          <div className="bg-gray-700 p-3 rounded">
            <div className="text-gray-400">Transcription Time</div>
            <div className="font-semibold">{combined.transcription.metadata?.processing_time?.toFixed(1)}s</div>
          </div>
          <div className="bg-gray-700 p-3 rounded">
            <div className="text-gray-400">Segmentation Time</div>
            <div className="font-semibold">{combined.segmentation.processing_time.toFixed(1)}s</div>
          </div>
        </div>
      </div>

      {/* Transcription */}
      <TranscriptionView transcript={combined.transcription} />

      {/* Segmentation */}
      <SegmentationView segmentation={{
        segments: combined.segmentation.segments,
        audio_duration: combined.segmentation.audio_duration,
        total_segments: combined.segmentation.total_segments,
        average_segment_duration: combined.segmentation.average_segment_duration,
        processing_time: combined.segmentation.processing_time,
        confidence_threshold: 0.5
      }} />
    </div>
  )
}
