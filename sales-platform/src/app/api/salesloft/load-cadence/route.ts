import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

/**
 * POST /api/salesloft/load-cadence
 * Body: { outreachPlanId: string }
 *
 * Loads an approved email draft into SalesLoft as a cadence step.
 * Falls back to a mock response when SALESLOFT_API_KEY is not set.
 */
export async function POST(req: Request) {
  const session = await auth();
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { outreachPlanId } = await req.json();

  const plan = await prisma.outreachPlan.findUnique({
    where: { id: outreachPlanId, userId: session.user.id as string },
    include: {
      contact: true,
      salesAccount: true,
      cadence: true,
    },
  });

  if (!plan) {
    return NextResponse.json({ error: "Plan item not found" }, { status: 404 });
  }

  if (!plan.aiDraft) {
    return NextResponse.json({ error: "No email draft to load" }, { status: 400 });
  }

  const salesloftId = await loadIntoSalesLoft({
    draft: plan.aiDraft,
    contactEmail: plan.contact?.email ?? null,
    contactName: plan.contact?.name ?? "Prospect",
    cadenceId: plan.cadence?.salesloftCadenceId ?? null,
    scheduledDate: plan.scheduledDate,
  });

  // Mark as sent / synced
  await prisma.outreachPlan.update({
    where: { id: outreachPlanId },
    data: { status: "sent" },
  });

  // Log activity
  await prisma.activity.create({
    data: {
      userId: session.user.id as string,
      salesAccountId: plan.salesAccountId,
      contactId: plan.contactId,
      type: "email",
      salesloftId,
      outcome: "opened",
    },
  });

  return NextResponse.json({ salesloftId, status: "loaded" });
}

// ─── SalesLoft loader (real or mock) ─────────────────────────────────────────

interface SalesLoftPayload {
  draft: string;
  contactEmail: string | null;
  contactName: string;
  cadenceId: string | null;
  scheduledDate: Date;
}

async function loadIntoSalesLoft(payload: SalesLoftPayload): Promise<string> {
  if (!process.env.SALESLOFT_API_KEY) {
    // Mock: return a fake cadence step ID
    return `mock_sl_${Date.now()}`;
  }

  const lines = payload.draft.split("\n");
  const subjectLine = lines[0].replace(/^Subject:\s*/i, "").trim();
  const body = lines.slice(2).join("\n").trim();

  const resp = await fetch(`${process.env.SALESLOFT_BASE_URL}/v2/steps.json`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${process.env.SALESLOFT_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      cadence_id: payload.cadenceId,
      day: 1,
      type: "Email",
      name: subjectLine,
      scheduled_at: payload.scheduledDate.toISOString(),
      email_template: {
        title: subjectLine,
        subject: subjectLine,
        body,
        open_tracking_enabled: true,
        click_tracking_enabled: true,
      },
      prospect: payload.contactEmail ? { email_address: payload.contactEmail } : undefined,
    }),
  });

  if (!resp.ok) throw new Error(`SalesLoft API error: ${resp.status}`);
  const data = await resp.json();
  return data.data?.id?.toString() ?? `sl_${Date.now()}`;
}
