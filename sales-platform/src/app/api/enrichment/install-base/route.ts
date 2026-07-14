import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

/**
 * POST /api/enrichment/install-base
 * Body: { records: Array<{ companyName: string; domain?: string; product: string; version?: string }> }
 *
 * Ingests install base records as signals. Typically called after CSV import.
 */
export async function POST(req: Request) {
  const session = await auth();
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { records } = await req.json() as {
    records: Array<{ companyName: string; domain?: string; product: string; version?: string }>;
  };

  if (!Array.isArray(records)) {
    return NextResponse.json({ error: "records array required" }, { status: 400 });
  }

  let created = 0;
  let skipped = 0;

  for (const record of records) {
    // Find the matching account
    const account = await prisma.salesAccount.findFirst({
      where: {
        OR: [
          { companyName: { equals: record.companyName, mode: "insensitive" } },
          ...(record.domain ? [{ domain: record.domain }] : []),
        ],
      },
    });

    if (!account) {
      skipped++;
      continue;
    }

    await prisma.signal.create({
      data: {
        salesAccountId: account.id,
        type: "install",
        source: "install_base",
        payload: {
          product: record.product,
          version: record.version ?? null,
          importedAt: new Date().toISOString(),
        },
        score: 1.0,
      },
    });
    created++;
  }

  return NextResponse.json({ created, skipped });
}
