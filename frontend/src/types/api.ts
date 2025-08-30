export interface ExecutionResult {
  output?: string;
  error?: string;
  status: "success" | "error" | "timeout" | "memory_limit";
  execution_time?: number;
}

export interface SubmissionResult {
  id: string;
  code: string;
  output?: string;
  error?: string;
  status: "success" | "error" | "timeout" | "memory_limit";
  execution_time?: number;
  created_at: string;
  updated_at: string;
}

export interface CodeExecutionRequest {
  code: string;
}

export interface SubmissionRequest {
  code: string;
}
