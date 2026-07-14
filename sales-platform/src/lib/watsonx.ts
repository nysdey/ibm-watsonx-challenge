/**
 * IBM watsonx.ai client wrapper
 *
 * Reads credentials from environment variables:
 *   WATSONX_API_KEY        — your watsonx.ai API key
 *   WATSONX_PROJECT_ID     — watsonx.ai project ID
 *   WATSONX_URL            — regional endpoint (default: us-south)
 *   WATSONX_GENERATION_MODEL — model for text generation (default: granite-3-3-8b-instruct)
 *   WATSONX_EMBEDDING_MODEL  — model for embeddings (default: slate-30m-english-rtrvr)
 */

import { WatsonXAI } from "@ibm-cloud/watsonx-ai";
import { IamAuthenticator } from "ibm-cloud-sdk-core";

// ─── Singleton ────────────────────────────────────────────────────────────────

let _client: WatsonXAI | null = null;

function getWatsonxClient(): WatsonXAI {
  if (_client) return _client;

  const apiKey = process.env.WATSONX_API_KEY;
  const serviceUrl = process.env.WATSONX_URL ?? "https://us-south.ml.cloud.ibm.com";

  if (!apiKey) {
    throw new Error("WATSONX_API_KEY is not set. Add it to your .env file.");
  }

  _client = WatsonXAI.newInstance({
    authenticator: new IamAuthenticator({ apikey: apiKey }),
    serviceUrl,
    version: "2024-05-31",
  });

  return _client;
}

// ─── Config helpers ───────────────────────────────────────────────────────────

function getProjectId(): string {
  const id = process.env.WATSONX_PROJECT_ID;
  if (!id) throw new Error("WATSONX_PROJECT_ID is not set.");
  return id;
}

const DEFAULT_GENERATION_MODEL =
  process.env.WATSONX_GENERATION_MODEL ?? "ibm/granite-3-3-8b-instruct";

const DEFAULT_EMBEDDING_MODEL =
  process.env.WATSONX_EMBEDDING_MODEL ?? "ibm/slate-30m-english-rtrvr";

// ─── Text Generation ──────────────────────────────────────────────────────────

export interface GenerateOptions {
  modelId?: string;
  maxNewTokens?: number;
  temperature?: number;
  stopSequences?: string[];
}

export interface GenerateResult {
  text: string;
  modelId: string;
  inputTokens: number;
  generatedTokens: number;
}

/**
 * Generate text from a prompt using watsonx.ai.
 */
export async function generateText(
  prompt: string,
  options: GenerateOptions = {}
): Promise<GenerateResult> {
  const client = getWatsonxClient();
  const projectId = getProjectId();

  const {
    modelId = DEFAULT_GENERATION_MODEL,
    maxNewTokens = 1024,
    temperature = 0.3,
    stopSequences,
  } = options;

  const response = await client.generateText({
    modelId,
    projectId,
    input: prompt,
    parameters: {
      max_new_tokens: maxNewTokens,
      temperature,
      ...(stopSequences ? { stop_sequences: stopSequences } : {}),
    },
  });

  const result = response.result;
  const generated = result.results?.[0];

  if (!generated) {
    throw new Error("watsonx.ai returned no results");
  }

  return {
    text: (generated as { generated_text?: string }).generated_text?.trim() ?? "",
    modelId: result.model_id ?? modelId,
    inputTokens: (generated as { input_token_count?: number }).input_token_count ?? 0,
    generatedTokens: (generated as { generated_token_count?: number }).generated_token_count ?? 0,
  };
}

// ─── Chat / Instruction Generation ───────────────────────────────────────────

export interface ChatMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

/**
 * Chat-style generation. Formats a messages array into a prompt string.
 */
export async function chat(
  messages: ChatMessage[],
  options: GenerateOptions = {}
): Promise<GenerateResult> {
  const prompt = messages
    .map((m) => {
      if (m.role === "system") return `<|system|>\n${m.content}`;
      if (m.role === "user") return `<|user|>\n${m.content}`;
      return `<|assistant|>\n${m.content}`;
    })
    .join("\n\n")
    .concat("\n\n<|assistant|>\n");

  return generateText(prompt, { maxNewTokens: 2048, ...options });
}

// ─── Embeddings ───────────────────────────────────────────────────────────────

export interface EmbedResult {
  embeddings: number[][];
  modelId: string;
}

/**
 * Generate embeddings for an array of text inputs.
 */
export async function embed(
  inputs: string[],
  modelId: string = DEFAULT_EMBEDDING_MODEL
): Promise<EmbedResult> {
  const client = getWatsonxClient();
  const projectId = getProjectId();

  const response = await client.embedText({
    modelId,
    projectId,
    inputs,  // string[] — the API accepts plain strings directly
  });

  const result = response.result;
  const results = (result as { results?: Array<{ embedding?: number[] }> }).results ?? [];

  return {
    embeddings: results.map((r) => r.embedding ?? []),
    modelId: (result as { model_id?: string }).model_id ?? modelId,
  };
}

// ─── Utility: Cosine similarity ───────────────────────────────────────────────

export function cosineSimilarity(a: number[], b: number[]): number {
  if (a.length !== b.length) throw new Error("Vector length mismatch");
  let dot = 0, normA = 0, normB = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }
  if (normA === 0 || normB === 0) return 0;
  return dot / (Math.sqrt(normA) * Math.sqrt(normB));
}

// ─── Model listing ────────────────────────────────────────────────────────────

export async function listAvailableModels() {
  const client = getWatsonxClient();
  const response = await client.listFoundationModelSpecs({});
  return (response.result as { resources?: unknown[] }).resources ?? [];
}
