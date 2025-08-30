import axios from "axios";
import {
  ExecutionResult,
  SubmissionResult,
  CodeExecutionRequest,
  SubmissionRequest,
} from "../types/api";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 60000, // 60 seconds timeout for code execution
});

// Request interceptor for logging
api.interceptors.request.use(
  (config: any) => {
    console.log(
      `Making ${config.method?.toUpperCase()} request to ${config.url}`,
    );
    return config;
  },
  (error: any) => {
    console.error("Request error:", error);
    return Promise.reject(error);
  },
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response: any) => {
    return response;
  },
  (error: any) => {
    console.error("Response error:", error);

    if (error.response) {
      // Server responded with error status
      const message =
        error.response.data?.detail ||
        error.response.data?.message ||
        "Server error occurred";
      throw new Error(message);
    } else if (error.request) {
      // Request was made but no response received
      throw new Error("No response from server. Please check your connection.");
    } else {
      // Something else happened
      throw new Error(error.message || "An unexpected error occurred");
    }
  },
);

export const executeCode = async (code: string): Promise<ExecutionResult> => {
  const request: CodeExecutionRequest = { code };
  const response = await api.post<ExecutionResult>("/code/execute", request);
  return response.data;
};

export const submitCode = async (code: string): Promise<SubmissionResult> => {
  const request: SubmissionRequest = { code };
  const response = await api.post<SubmissionResult>("/code/submit", request);
  return response.data;
};

export const getSubmission = async (
  submissionId: string,
): Promise<SubmissionResult> => {
  const response = await api.get<SubmissionResult>(
    `/code/submissions/${submissionId}`,
  );
  return response.data;
};

export default api;
