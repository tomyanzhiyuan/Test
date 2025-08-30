import React from 'react'
import { Toaster } from 'react-hot-toast'
import CodeEditor from './components/CodeEditor'
import './App.css'

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Toaster position="top-right" />
      <div className="container mx-auto px-4 py-8">
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Code Execution Platform
          </h1>
          <p className="text-lg text-gray-600">
            Write and execute Python code securely in your browser
          </p>
        </header>
        <main>
          <CodeEditor />
        </main>
      </div>
    </div>
  )
}

export default App
