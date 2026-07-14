/**
 * watsonx.ai prompt chains for the sales intelligence platform
 *
 * Chain steps:
 *  1. summarizeAccountSignals   — raw signal data → structured brief
 *  2. scoreAndTierAccount       — brief → tier (A/B/C/D) + rationale
 *  3. classifyUseCaseBucket     — brief + KB snippets → use-case bucket
 *  4. generateOutreachPlan      — brief + profile → scheduled action list
 *  5. generateEmail             — brief + contact + profile → personalized email
 *  6. rankContacts              — contacts + profile → sorted list with scores
 */

import { generateText, chat, type ChatMessage } from "@/lib/watsonx";

// ─── Types ────────────────────────────────────────────────────────────────────

export interface AccountBrief {
  companyName: string;
  domain?: string | null;
  industry?: string | null;
  segment?: string | null;
  installSignals: string[];
  intentSignals: string[];
  newsSignals: string[];
  contacts: Array<{ name: string; title: string }>;
}

export interface RepContext {
  products: string[];
  territory?: string | null;
  industries: string[];
  toneFormality: number;
  toneBrevity: number;
  writingStyleNote?: string | null;
  exampleEmails: string[];
}

export interface ScoredAccount {
  tier: "A" | "B" | "C" | "D";
  priorityScore: number;
  rationale: string;
}

export interface UseCaseResult {
  bucket: string;
  confidence: number;
  reasoning: string;
}

export interface OutreachAction {
  actionType: "email" | "call" | "linkedin";
  daysFromNow: number;
  contactTitle: string;
  note: string;
}

export interface EmailDraft {
  subject: string;
  body: string;
}

export interface ContactRanking {
  name: string;
  title: string;
  score: number;
  reason: string;
}

// ─── Helper: safe JSON parse ──────────────────────────────────────────────────

function parseJsonFromLlm<T>(text: string, fallback: T): T {
  // Strip markdown code fences if present
  const cleaned = text
    .replace(/^```(?:json)?\n?/m, "")
    .replace(/\n?```$/m, "")
    .trim();
  try {
    return JSON.parse(cleaned) as T;
  } catch {
    return fallback;
  }
}

// ─── Step 1: Summarize signals ────────────────────────────────────────────────

export async function summarizeAccountSignals(brief: AccountBrief): Promise<string> {
  const messages: ChatMessage[] = [
    {
      role: "system",
      content: `You are a sales intelligence analyst. Your job is to write a concise, factual account brief (3-5 sentences) for an enterprise software sales rep. 
Focus on: current technology footprint, active buying signals, relevant company context, and potential pain points.
Do not speculate beyond the provided data. Use plain prose, no bullet points.`,
    },
    {
      role: "user",
      content: `Account: ${brief.companyName} (${brief.domain ?? "unknown domain"})
Industry: ${brief.industry ?? "Unknown"}
Segment: ${brief.segment ?? "Unknown"}

Install base signals:
${brief.installSignals.length ? brief.installSignals.join("\n") : "None"}

Buyer intent signals:
${brief.intentSignals.length ? brief.intentSignals.join("\n") : "None"}

Recent news:
${brief.newsSignals.length ? brief.newsSignals.join("\n") : "None"}

Key contacts: ${brief.contacts.map((c) => `${c.name} (${c.title})`).join(", ") || "Unknown"}

Write the account brief now.`,
    },
  ];

  const result = await chat(messages, { maxNewTokens: 400, temperature: 0.2 });
  return result.text;
}

// ─── Step 2: Score and tier account ──────────────────────────────────────────

export async function scoreAndTierAccount(
  accountSummary: string,
  repContext: RepContext
): Promise<ScoredAccount> {
  const messages: ChatMessage[] = [
    {
      role: "system",
      content: `You are a sales prioritization engine. Given an account brief and a rep's product/territory profile, score the account.

Output ONLY valid JSON matching this schema:
{
  "tier": "A" | "B" | "C" | "D",
  "priorityScore": <number 0-100>,
  "rationale": "<one sentence>"
}

Scoring guidance:
- A (80-100): Strong signals, clear fit, active intent
- B (60-79): Good fit, moderate signals
- C (40-59): Weak signals or marginal fit
- D (0-39): Poor fit or no signals`,
    },
    {
      role: "user",
      content: `Account brief:
${accountSummary}

Rep profile:
- Products: ${repContext.products.join(", ") || "Not specified"}
- Territory: ${repContext.territory ?? "Not specified"}
- Target industries: ${repContext.industries.join(", ") || "All"}

Respond with JSON only.`,
    },
  ];

  const result = await chat(messages, { maxNewTokens: 200, temperature: 0.1 });
  return parseJsonFromLlm<ScoredAccount>(result.text, {
    tier: "C",
    priorityScore: 40,
    rationale: "Unable to score — insufficient data",
  });
}

// ─── Step 3: Classify use-case bucket ────────────────────────────────────────

const USE_CASE_BUCKETS = [
  "Security & Compliance",
  "Cost Optimization",
  "Modernization & Migration",
  "AI & Analytics",
  "Developer Productivity",
  "Infrastructure Scaling",
  "Data Management",
  "Other",
];

export async function classifyUseCaseBucket(
  accountSummary: string,
  knowledgeSnippets: string[]
): Promise<UseCaseResult> {
  const messages: ChatMessage[] = [
    {
      role: "system",
      content: `You are a sales use-case classifier. Given an account brief and relevant product knowledge, identify the primary use-case bucket.

Available buckets:
${USE_CASE_BUCKETS.map((b, i) => `${i + 1}. ${b}`).join("\n")}

Output ONLY valid JSON:
{
  "bucket": "<exact bucket name from the list>",
  "confidence": <number 0.0-1.0>,
  "reasoning": "<one sentence>"
}`,
    },
    {
      role: "user",
      content: `Account brief:
${accountSummary}

Relevant product knowledge:
${knowledgeSnippets.length ? knowledgeSnippets.slice(0, 3).join("\n\n---\n\n") : "No knowledge snippets available."}

Classify the use case. Respond with JSON only.`,
    },
  ];

  const result = await chat(messages, { maxNewTokens: 200, temperature: 0.1 });
  return parseJsonFromLlm<UseCaseResult>(result.text, {
    bucket: "Other",
    confidence: 0.3,
    reasoning: "Unable to classify",
  });
}

// ─── Step 4: Generate outreach plan ──────────────────────────────────────────

export async function generateOutreachPlan(
  accountSummary: string,
  repContext: RepContext,
  tier: string
): Promise<OutreachAction[]> {
  const touchCount = tier === "A" ? 6 : tier === "B" ? 4 : 2;

  const messages: ChatMessage[] = [
    {
      role: "system",
      content: `You are a sales cadence planner. Create a personalized multi-touch outreach plan.
Output ONLY a valid JSON array of actions.

Each action:
{
  "actionType": "email" | "call" | "linkedin",
  "daysFromNow": <integer>,
  "contactTitle": "<target persona title>",
  "note": "<brief instruction for the rep, 1 sentence>"
}

Rules:
- Plan exactly ${touchCount} touches
- Space touches appropriately (no two touches on the same day)
- Start within 1-2 business days
- Mix email, call, and linkedin appropriately
- Target the most senior IT/business contact first`,
    },
    {
      role: "user",
      content: `Account brief:
${accountSummary}

Account tier: ${tier}
Rep products: ${repContext.products.join(", ")}

Respond with a JSON array only.`,
    },
  ];

  const result = await chat(messages, { maxNewTokens: 600, temperature: 0.3 });
  return parseJsonFromLlm<OutreachAction[]>(result.text, []);
}

// ─── Step 5: Generate personalized email ────────────────────────────────────

export async function generateEmail(
  accountSummary: string,
  contact: { name: string; title: string; company: string },
  repContext: RepContext,
  useCaseBucket: string,
  knowledgeSnippets: string[]
): Promise<EmailDraft> {
  const toneDescription =
    repContext.toneFormality >= 4
      ? "formal and professional"
      : repContext.toneFormality <= 2
      ? "casual and conversational"
      : "semi-formal and approachable";

  const lengthDescription =
    repContext.toneBrevity >= 4
      ? "very brief (3-4 sentences max)"
      : repContext.toneBrevity <= 2
      ? "detailed with context"
      : "concise (5-7 sentences)";

  const styleGuide = repContext.writingStyleNote
    ? `\nAdditional style notes: ${repContext.writingStyleNote}`
    : "";

  const exampleBlock =
    repContext.exampleEmails.length > 0
      ? `\nExample email from this rep (match the tone/style):\n---\n${repContext.exampleEmails[0]}\n---`
      : "";

  const messages: ChatMessage[] = [
    {
      role: "system",
      content: `You are an enterprise software sales email writer. Write a highly personalized cold outreach email.

Tone: ${toneDescription}
Length: ${lengthDescription}${styleGuide}${exampleBlock}

Output ONLY valid JSON:
{
  "subject": "<email subject line>",
  "body": "<full email body with greeting and sign-off>"
}

Rules:
- Reference specific account context (not generic)
- One clear call to action
- No unsubscribe links, no attachments mentioned
- Do not hallucinate customer names or metrics not provided
- Sign off with [REP_NAME] as a placeholder`,
    },
    {
      role: "user",
      content: `Account brief:
${accountSummary}

Recipient: ${contact.name}, ${contact.title} at ${contact.company}
Use case focus: ${useCaseBucket}
Products: ${repContext.products.join(", ")}

Relevant talking points from knowledge base:
${knowledgeSnippets.length ? knowledgeSnippets.slice(0, 2).join("\n\n") : "Use general product value."}

Write the email. Respond with JSON only.`,
    },
  ];

  const result = await chat(messages, { maxNewTokens: 800, temperature: 0.5 });
  return parseJsonFromLlm<EmailDraft>(result.text, {
    subject: "Quick question about " + contact.company,
    body: "Hi " + contact.name + ",\n\n[Draft generation failed — please write manually]\n\nBest,\n[REP_NAME]",
  });
}

// ─── Step 6: Rank contacts ────────────────────────────────────────────────────

export async function rankContacts(
  contacts: Array<{ name: string; title: string }>,
  repContext: RepContext,
  useCaseBucket: string
): Promise<ContactRanking[]> {
  if (contacts.length === 0) return [];

  const messages: ChatMessage[] = [
    {
      role: "system",
      content: `You are a sales persona expert. Rank the provided contacts for outreach priority given the rep's focus area.

Output ONLY a valid JSON array sorted from highest to lowest priority:
[{
  "name": "<contact name>",
  "title": "<contact title>",
  "score": <number 0-100>,
  "reason": "<one sentence>"
}]`,
    },
    {
      role: "user",
      content: `Contacts:
${contacts.map((c) => `- ${c.name}, ${c.title}`).join("\n")}

Rep products: ${repContext.products.join(", ")}
Use case: ${useCaseBucket}
Target industries: ${repContext.industries.join(", ") || "All"}

Rank contacts from most to least valuable. Respond with JSON array only.`,
    },
  ];

  const result = await chat(messages, { maxNewTokens: 600, temperature: 0.2 });
  return parseJsonFromLlm<ContactRanking[]>(result.text, []);
}
