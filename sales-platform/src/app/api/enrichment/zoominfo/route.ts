import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

/**
 * POST /api/enrichment/zoominfo
 * Body: { salesAccountId: string }
 *
 * Fetches contacts from ZoomInfo (or mock) and stores them.
 * Falls back to mock data when ZOOMINFO_API_KEY is not set.
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

  const contacts = await fetchZoomInfoContacts(account.companyName, account.domain);

  if (contacts.length === 0) {
    return NextResponse.json({ created: 0, message: "No contacts found" });
  }

  const result = await prisma.contact.createMany({
    data: contacts.map((c) => ({
      salesAccountId,
      name: c.name,
      title: c.title,
      email: c.email,
      phone: c.phone,
      source: "zoominfo" as const,
      isItDirector: isItDirectorTitle(c.title),
    })),
    skipDuplicates: true,
  });

  // Store as signal
  await prisma.signal.create({
    data: {
      salesAccountId,
      type: "intent",
      source: "zoominfo",
      payload: { contacts: contacts.length, titles: contacts.map((c) => c.title) },
    },
  });

  return NextResponse.json({ created: result.count });
}

// ─── ZoomInfo fetch (real or mock) ───────────────────────────────────────────

interface ZIContact {
  name: string;
  title: string;
  email?: string;
  phone?: string;
}

async function fetchZoomInfoContacts(
  companyName: string,
  _domain?: string | null
): Promise<ZIContact[]> {
  if (!process.env.ZOOMINFO_API_KEY) {
    // Return mock data for development
    return getMockContacts(companyName);
  }

  try {
    const resp = await fetch(
      `${process.env.ZOOMINFO_BASE_URL}/lookup/outputfields`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${process.env.ZOOMINFO_API_KEY}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          matchCompanyInput: [{ name: companyName }],
          outputFields: ["firstName", "lastName", "jobTitle", "email", "phone"],
          personaFilter: {
            jobFunctionList: ["Information Technology"],
          },
          rpp: 10,
          page: 1,
        }),
      }
    );

    if (!resp.ok) throw new Error(`ZoomInfo API error: ${resp.status}`);

    const data = await resp.json();
    return (data.data?.outputFields ?? []).map(
      (p: { firstName: string; lastName: string; jobTitle: string; email: string; phone: string }) => ({
        name: `${p.firstName} ${p.lastName}`.trim(),
        title: p.jobTitle,
        email: p.email,
        phone: p.phone,
      })
    );
  } catch (err) {
    console.error("ZoomInfo fetch failed, using mock:", err);
    return getMockContacts(companyName);
  }
}

function getMockContacts(companyName: string): ZIContact[] {
  return [
    { name: "Alex Johnson", title: "IT Director", email: `ajohnson@${slugify(companyName)}.com`, phone: "555-0101" },
    { name: "Sam Rivera", title: "VP of Engineering", email: `srivera@${slugify(companyName)}.com` },
    { name: "Morgan Lee", title: "CTO", email: `mlee@${slugify(companyName)}.com` },
    { name: "Chris Davis", title: "IT Manager", email: `cdavis@${slugify(companyName)}.com` },
  ];
}

function slugify(name: string) {
  return name.toLowerCase().replace(/[^a-z0-9]/g, "").slice(0, 20);
}

function isItDirectorTitle(title: string): boolean {
  const t = title.toLowerCase();
  return (
    t.includes("it director") ||
    t.includes("cto") ||
    t.includes("chief technology") ||
    t.includes("vp of engineering") ||
    t.includes("vp engineering") ||
    t.includes("director of it") ||
    t.includes("head of it")
  );
}
