import { ChatSDKError } from "@/lib/errors";

type RetryOptions = {
  retries: number;
  baseDelayMs: number;
  maxDelayMs: number;
};

type TimeoutOptions = {
  timeoutMs: number;
};

type RequestOptions = {
  headers?: Record<string, string>;
  retry?: RetryOptions;
  timeout?: TimeoutOptions;
};

type StreamChunk =
  | { type: "text-delta"; text: string }
  | { type: "usage"; data: any }
  | { type: "finish" };

export type PythonAIConfig = {
  baseUrl: string;
  apiKey?: string;
  defaultTimeoutMs?: number;
  defaultRetries?: number;
  fetchImpl?: typeof fetch;
};

const TRAILING_SLASHES_RE = /\/+$/;

export class PythonAI {
  private readonly baseUrl: string;
  private readonly apiKey?: string;
  private readonly defaultTimeoutMs: number;
  private readonly defaultRetries: number;
  private readonly fetchImpl: typeof fetch;

  constructor(config: PythonAIConfig) {
    this.baseUrl = config.baseUrl.replace(TRAILING_SLASHES_RE, "");
    this.apiKey = config.apiKey;
    const envTimeout =
      Number(process.env.NEXT_PUBLIC_AI_TIMEOUT_MS || process.env.PYTHON_AI_TIMEOUT_MS || "0") || 0;
    this.defaultTimeoutMs =
      (envTimeout > 0 ? envTimeout : undefined) ?? config.defaultTimeoutMs ?? 120_000;
    this.defaultRetries = config.defaultRetries ?? 2;
    this.fetchImpl = config.fetchImpl ?? fetch;
  }

  private async fetchJson<T>(
    path: string,
    body: any,
    options?: RequestOptions
  ): Promise<T> {
    const url = new URL(path, this.baseUrl).toString();
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options?.headers ?? {}),
    };
    if (this.apiKey) {
      headers.Authorization = `Bearer ${this.apiKey}`;
    }

    const retry: RetryOptions = options?.retry ?? {
      retries: this.defaultRetries,
      baseDelayMs: 500,
      maxDelayMs: 4000,
    };
    const timeoutMs = options?.timeout?.timeoutMs ?? this.defaultTimeoutMs;

    let attempt = 0;
    for (;;) {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), timeoutMs);
      try {
        const res = await this.fetchImpl(url, {
          method: "POST",
          headers,
          body: JSON.stringify(body),
          signal: controller.signal,
        });
        clearTimeout(timeout);

        if (!res.ok) {
          let cause: any;
          try {
            // Clone the response to avoid "Body is unusable" error if we read it twice
            cause = await res.clone().json();
          } catch {
            cause = await res.text();
          }
          throw new ChatSDKError("bad_request:api", String(cause));
        }
        return (await res.json()) as T;
      } catch (err: any) {
        clearTimeout(timeout);
        const isTimeout =
          err?.name === "AbortError" ||
          String(err?.message ?? "").includes("aborted");
        if (attempt >= retry.retries) {
          if (isTimeout) {
            throw new ChatSDKError("offline:chat", "AI API timeout");
          }
          throw err;
        }
        const delay =
          Math.min(retry.maxDelayMs, retry.baseDelayMs * 2 ** attempt) +
          Math.floor(Math.random() * 100);
        await new Promise((r) => setTimeout(r, delay));
        attempt++;
      }
    }
  }

  async generateTitle(input: { text: string }): Promise<{ title: string }> {
    try {
      const apiPath = process.env.PYTHON_AI_API_PATH || "/api/v1";
      return await this.fetchJson<{ title: string }>(`${apiPath}/title`, input);
    } catch (error) {
      console.error("PythonAI.generateTitle error", error);
      throw error;
    }
  }

  async *streamChat(input: {
    id: string;
    messages: any[];
    modelId?: string;
    hints?: Record<string, any>;
  }): AsyncIterable<StreamChunk> {
    const apiPath = process.env.PYTHON_AI_API_PATH || "/api/v1";
    
    // Use the correct streaming endpoint
    let path = `${apiPath}/chat/stream`;
    
    // Remove double slashes if any
    path = path.replace("//", "/");
    
    const url = new URL(path, this.baseUrl).toString();
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (this.apiKey) {
      headers.Authorization = `Bearer ${this.apiKey}`;
    }

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.defaultTimeoutMs);
    try {
      const res = await this.fetchImpl(url, {
        method: "POST",
        headers,
        body: JSON.stringify(input),
        signal: controller.signal,
      });
      if (!res.ok) {
        let cause: any;
        try {
          // Clone the response to avoid "Body is unusable" error if we read it twice
          cause = await res.clone().json();
        } catch {
          cause = await res.text();
        }
        throw new ChatSDKError("bad_request:api", String(cause));
      }
      if (!res.body) {
        throw new ChatSDKError("offline:chat", "No response body from AI API");
      }
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      for (;;) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }
        buffer += decoder.decode(value, { stream: true });
        // Parse Server-Sent Events style: lines starting with "data: "
        let idx = buffer.indexOf("\n\n");
        while (idx !== -1) {
          const raw = buffer.slice(0, idx).trim();
          buffer = buffer.slice(idx + 2);
          const dataLine = raw.startsWith("data:") ? raw.slice(5).trim() : raw;
          const maybeJson = dataLine.trim();
          if (maybeJson.startsWith("{") && maybeJson.endsWith("}")) {
            try {
              // Defensive fix: Python might send NaN/Infinity which is invalid JSON
              // We replace them with null before parsing
              const sanitized = maybeJson
                .replace(/:\s*NaN/g, ": null")
                .replace(/:\s*Infinity/g, ": null")
                .replace(/:\s*-Infinity/g, ": null");

              const json = JSON.parse(sanitized);
              if (json.type === "text-delta" && typeof json.data === "string") {
                yield { type: "text-delta", text: json.data };
              } else if (json.type === "usage") {
                yield { type: "usage", data: json.data };
              }
            } catch (e) {
              console.warn("Failed to parse JSON chunk:", e, maybeJson);
            }
          }
          idx = buffer.indexOf("\n\n");
        }
      }
      yield { type: "finish" };
    } catch (error) {
      const isTimeout =
        (error as any)?.name === "AbortError" ||
        String((error as any)?.message ?? "").includes("aborted");
      if (isTimeout) {
        throw new ChatSDKError("offline:chat", "AI API timeout");
      }
      console.error("PythonAI.streamChat error", error);
      throw error;
    } finally {
      clearTimeout(timeout);
    }
  }
}

export function getPythonAI(): PythonAI {
  const baseUrl =
    process.env.PYTHON_AI_BASE_URL ||
    process.env.AI_PY_BASE_URL ||
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    "";
  if (!baseUrl) {
    throw new Error("PYTHON_AI_BASE_URL is not configured");
  }
  const apiKey = process.env.PYTHON_AI_API_KEY || process.env.AI_API_KEY;
  const envTimeout =
    Number(process.env.NEXT_PUBLIC_AI_TIMEOUT_MS || process.env.PYTHON_AI_TIMEOUT_MS || "0") || 0;
  return new PythonAI({
    baseUrl,
    apiKey,
    defaultTimeoutMs: envTimeout > 0 ? envTimeout : undefined,
  });
}
