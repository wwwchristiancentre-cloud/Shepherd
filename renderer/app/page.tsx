'use client'

import { useState, useEffect } from 'react'

type Project = {
  id: number;
  name: string;
  created_at: string;
}

export default function Home() {
  const [projects, setProjects] = useState<Project[]>([])
  const [showModal, setShowModal] = useState(false)
  const [newProjectName, setNewProjectName] = useState('')

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
