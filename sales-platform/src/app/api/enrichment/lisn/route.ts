import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

/**
 * POST /api/enrichment/lisn
 * Body: { salesAccountId: string }
 *
 * Fetches buyer intent signals from LISN (or mock).
 */
export async function POST(req: Request) {
  const session = await auth();
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { salesAccountId } = await req.json();
  if (!salesAccountId) {
    return NextResponse.json({ error: "salesAccountId required" }, { status: 400 });
  }

  const account = await prisma.salesAccount.findUnique({
    where: { id: salesAccountId },
  });
  if (!account) {
    return NextResponse.json({ error: "Account not found" }, { status: 404 });
  }

  const signals = await fetchLisnSignals(account.companyName, account.domain);

  const created = await Promise.all(
    signals.map((s) =>
      prisma.signal.create({
        data: {
          salesAccountId,
          type: "lisn",
          source: "lisn",
          payload: JSON.parse(JSON.stringify(s)) as object,
          score: s.intentScore ?? null,
          ingestedAt: new Date(),
        },
      })
    )
  );

  return NextResponse.json({ created: created.length, signals });
}

// ─── LISN fetch (real or mock) ────────────────────────────────────────────────

interface LisnSignal {
  topic: string;
  intentScore: number;
  searchVolume: string;
  weekOf: string;
  [key: string]: unknown; // required for Prisma Json field
}

async function fetchLisnSignals(
  companyName: string,
  _domain?: string | null
): Promise<LisnSignal[]> {
  if (!process.env.LISN_API_KEY) {
    return getMockLisnSignals(companyName);
  }

  try {
    const resp = await fetch(`${process.env.LISN_BASE_URL}/v1/signals`, {
      method: "POST",
      headers: {
        "x-api-key": process.env.LISN_API_KEY,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ company: companyName, lookback_days: 30 }),
    });

    if (!resp.ok) throw new Error(`LISN API error: ${resp.status}`);
    const data = await resp.json();
    return data.signals ?? [];
  } catch (err) {
    console.error("LISN fetch failed, using mock:", err);
    return getMockLisnSignals(companyName);
  }
}

function getMockLisnSignals(_companyName: string): LisnSignal[] {
  const topics = [
    { topic: "cloud migration", intentScore: 0.82, searchVolume: "high" },
    { topic: "cybersecurity tools", intentScore: 0.74, searchVolume: "medium" },
    { topic: "data analytics platform", intentScore: 0.65, searchVolume: "medium" },
    { topic: "AI automation", intentScore: 0.91, searchVolume: "high" },
  ];

  const weekOf = new Date().toISOString().split("T")[0];
  return topics.slice(0, 2 + Math.floor(Math.random() * 3)).map((t) => ({
    ...t,
    weekOf,
  }));
}
