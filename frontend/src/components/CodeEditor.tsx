import { useState } from "react";
import Editor from "@monaco-editor/react";
import toast from "react-hot-toast";
import { executeCode, submitCode } from "../services/api";
import { ExecutionResult } from "../types/api";

const DEFAULT_CODE = `# Welcome to the Code Execution Platform!
# You can write Python code here and execute it securely.
# pandas and scipy are available for use.

import pandas as pd
import numpy as np

# Example: Create a simple DataFrame
data = {
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [25, 30, 35],
    'city': ['New York', 'London', 'Tokyo']
}

df = pd.DataFrame(data)
print("Sample DataFrame:")
print(df)

# Example: Basic calculations
numbers = [1, 2, 3, 4, 5]
print(f"\\nSum: {sum(numbers)}")
print(f"Average: {np.mean(numbers)}")
`;

const CodeEditor: React.FC = () => {
  const [code, setCode] = useState<string>(DEFAULT_CODE);
  const [output, setOutput] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [isExecuting, setIsExecuting] = useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [executionTime, setExecutionTime] = useState<number | null>(null);

  const handleExecute = async () => {
    if (!code.trim()) {
      toast.error("Please enter some code to execute");
      return;
    }

    setIsExecuting(true);
    setOutput("");
    setError("");
    setExecutionTime(null);

    try {
      const result: ExecutionResult = await executeCode(code);

      if (result.status === "success") {
        setOutput(result.output || "Code executed successfully (no output)");
        setExecutionTime(result.execution_time || null);
        toast.success("Code executed successfully!");
      } else {
        setError(result.error || "Unknown error occurred");
        toast.error("Code execution failed");
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to execute code";
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setIsExecuting(false);
    }
  };

  const handleSubmit = async () => {
    if (!code.trim()) {
      toast.error("Please enter some code to submit");
      return;
    }

    setIsSubmitting(true);

    try {
      const result = await submitCode(code);
      toast.success(`Code submitted successfully! ID: ${result.id}`);

      // Update display with submission results
      if (result.status === "success") {
        setOutput(result.output || "Code executed successfully (no output)");
        setError("");
      } else {
        setError(result.error || "Unknown error occurred");
        setOutput("");
      }
      setExecutionTime(result.execution_time || null);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to submit code";
      toast.error(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Code Editor */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-semibold text-gray-800 mb-4">
          Python Code Editor
        </h2>
        <div className="border rounded-lg overflow-hidden">
          <Editor
            height="400px"
            defaultLanguage="python"
            value={code}
            onChange={(value) => setCode(value || "")}
            theme="vs-dark"
            options={{
              minimap: { enabled: false },
              fontSize: 14,
              lineNumbers: "on",
              roundedSelection: false,
              scrollBeyondLastLine: false,
              automaticLayout: true,
              tabSize: 4,
              insertSpaces: true,
            }}
          />
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4 mt-4">
          <button
            onClick={handleExecute}
            disabled={isExecuting || isSubmitting}
            className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isExecuting && <div className="loading-spinner"></div>}
            {isExecuting ? "Executing..." : "Test Code"}
          </button>

          <button
            onClick={handleSubmit}
            disabled={isExecuting || isSubmitting}
            className="flex items-center gap-2 px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isSubmitting && <div className="loading-spinner"></div>}
            {isSubmitting ? "Submitting..." : "Submit"}
          </button>
        </div>
      </div>

      {/* Output Display */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-semibold text-gray-800">Output</h2>
          {executionTime && (
            <span className="text-sm text-gray-500">
              Execution time: {executionTime.toFixed(3)}s
            </span>
          )}
        </div>

        <div className="output-container">
          {error ? (
            <div className="error-output">{error}</div>
          ) : output ? (
            <div className="success-output">{output}</div>
          ) : (
            <div className="text-gray-400">
              No output yet. Run your code to see results.
            </div>
          )}
        </div>
      </div>

      {/* Help Section */}
      <div className="bg-blue-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-800 mb-2">
          Available Libraries
        </h3>
        <p className="text-blue-700 mb-2">
          The following Python libraries are pre-installed and ready to use:
        </p>
        <ul className="list-disc list-inside text-blue-600 space-y-1">
          <li>
            <code className="bg-blue-100 px-1 rounded">pandas</code> - Data
            manipulation and analysis
          </li>
          <li>
            <code className="bg-blue-100 px-1 rounded">scipy</code> - Scientific
            computing
          </li>
          <li>
            <code className="bg-blue-100 px-1 rounded">numpy</code> - Numerical
            computing
          </li>
        </ul>
        <div className="mt-4 text-sm text-blue-600">
          <p>
            <strong>Test Code:</strong> Execute code without saving to database
          </p>
          <p>
            <strong>Submit:</strong> Execute code and save successful results to
            database
          </p>
        </div>
      </div>
    </div>
  );
};

export default CodeEditor;
