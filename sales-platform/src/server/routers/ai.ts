import { z } from "zod";
import { createTRPCRouter, protectedProcedure } from "@/server/trpc";
import { TRPCError } from "@trpc/server";
import {
  summarizeAccountSignals,
  scoreAndTierAccount,
  classifyUseCaseBucket,
  generateOutreachPlan,
  generateEmail,
  rankContacts,
  type AccountBrief,
} from "@/server/lib/promptChains";

export const aiRouter = createTRPCRouter({
  /**
   * Full enrichment chain for a single account:
   * signals → summary → tier → use-case → outreach plan
   */
  enrichAccount: protectedProcedure
    .input(z.object({ salesAccountId: z.string() }))
    .mutation(async ({ ctx, input }) => {
      // 1. Load account + signals + contacts
      const account = await ctx.prisma.salesAccount.findUnique({
        where: { id: input.salesAccountId },
        include: {
          signals: true,
          contacts: { select: { name: true, title: true } },
        },
      });

      if (!account) throw new TRPCError({ code: "NOT_FOUND" });

      // 2. Load rep profile
      const repProfile = await ctx.prisma.repProfile.findUnique({
        where: { userId: ctx.userId },
      });

      if (!repProfile) {
        throw new TRPCError({
          code: "PRECONDITION_FAILED",
          message: "Complete your rep profile before running AI enrichment.",
        });
      }

      // 3. Build brief from signals
      const brief: AccountBrief = {
        companyName: account.companyName,
        domain: account.domain,
        industry: account.industry,
        segment: account.segment,
        installSignals: account.signals
          .filter((s) => s.type === "install")
          .map((s) => JSON.stringify(s.payload)),
        intentSignals: account.signals
          .filter((s) => s.type === "intent" || s.type === "lisn")
          .map((s) => JSON.stringify(s.payload)),
        newsSignals: account.signals
          .filter((s) => s.type === "news")
          .map((s) => JSON.stringify(s.payload)),
        contacts: account.contacts.map((c) => ({ name: c.name, title: c.title ?? "" })),
      };

      // 4. Step 1 — Summarize
      const summary = await summarizeAccountSignals(brief);

      // 5. Step 2 — Score
      const repContext = {
        products: repProfile.products,
        territory: repProfile.territory,
        industries: repProfile.industries,
        toneFormality: repProfile.toneFormality,
        toneBrevity: repProfile.toneBrevity,
        writingStyleNote: repProfile.writingStyleNote,
        exampleEmails: repProfile.exampleEmails,
      };

      const scored = await scoreAndTierAccount(summary, repContext);

      // 6. Step 3 — Use-case bucket (retrieve relevant KB snippets first)
      const kbArticles = await ctx.prisma.knowledgeBase.findMany({ take: 20 });
      const kbSnippets = kbArticles
        .filter(
          (a) =>
            repProfile.products.some(
              (p) => p.toLowerCase() === a.product.toLowerCase()
            ) || repProfile.products.length === 0
        )
        .map((a) => `[${a.product} / ${a.useCase}]\n${a.content}`)
        .slice(0, 5);

      const useCase = await classifyUseCaseBucket(summary, kbSnippets);

      // 7. Update account in DB
      const updatedAccount = await ctx.prisma.salesAccount.update({
        where: { id: account.id },
        data: {
          tier: scored.tier,
          priorityScore: scored.priorityScore,
          aiRationale: scored.rationale,
          useCaseBucket: useCase.bucket,
          lastEnrichedAt: new Date(),
        },
      });

      // 8. Audit log
      await ctx.prisma.auditLog.create({
        data: {
          userId: ctx.userId,
          action: "ai_enrich_account",
          entity: "SalesAccount",
          entityId: account.id,
          payload: {
            summary: summary.slice(0, 500),
            tier: scored.tier,
            bucket: useCase.bucket,
          },
          modelVersion: process.env.WATSONX_GENERATION_MODEL,
        },
      });

      return { account: updatedAccount, summary, scored, useCase };
    }),

  /**
   * Generate outreach plan for an account + schedule items
   */
  generatePlan: protectedProcedure
    .input(z.object({ salesAccountId: z.string() }))
    .mutation(async ({ ctx, input }) => {
      const account = await ctx.prisma.salesAccount.findUnique({
        where: { id: input.salesAccountId },
        include: {
          contacts: { orderBy: { personaFitScore: "desc" }, take: 5 },
          signals: true,
        },
      });

      if (!account) throw new TRPCError({ code: "NOT_FOUND" });
      if (!account.tier) {
        throw new TRPCError({
          code: "PRECONDITION_FAILED",
          message: "Run AI enrichment first to tier the account.",
        });
      }

      const repProfile = await ctx.prisma.repProfile.findUnique({
        where: { userId: ctx.userId },
      });
      if (!repProfile) throw new TRPCError({ code: "PRECONDITION_FAILED", message: "Complete rep profile first." });

      const brief: AccountBrief = {
        companyName: account.companyName,
        domain: account.domain,
        industry: account.industry,
        segment: account.segment,
        installSignals: account.signals.filter((s) => s.type === "install").map((s) => JSON.stringify(s.payload)),
        intentSignals: account.signals.filter((s) => s.type === "intent").map((s) => JSON.stringify(s.payload)),
        newsSignals: account.signals.filter((s) => s.type === "news").map((s) => JSON.stringify(s.payload)),
        contacts: account.contacts.map((c) => ({ name: c.name, title: c.title ?? "" })),
      };

      const summary = await summarizeAccountSignals(brief);
      const repContext = {
        products: repProfile.products,
        territory: repProfile.territory,
        industries: repProfile.industries,
        toneFormality: repProfile.toneFormality,
        toneBrevity: repProfile.toneBrevity,
        writingStyleNote: repProfile.writingStyleNote,
        exampleEmails: repProfile.exampleEmails,
      };

      const actions = await generateOutreachPlan(summary, repContext, account.tier);

      // Find or use first contact as default
      const defaultContact = account.contacts[0];

      const now = new Date();
      const created = await ctx.prisma.$transaction(
        actions.map((action) => {
          const scheduledDate = new Date(now);
          scheduledDate.setDate(now.getDate() + action.daysFromNow);

          return ctx.prisma.outreachPlan.create({
            data: {
              userId: ctx.userId,
              salesAccountId: account.id,
              contactId: defaultContact?.id ?? null,
              actionType: action.actionType,
              scheduledDate,
              status: repProfile.automationLevel >= 3 ? "approved" : "pending",
              aiPromptLog: action.note,
              modelVersion: process.env.WATSONX_GENERATION_MODEL,
            },
          });
        })
      );

      return { created: created.length, actions };
    }),

  /**
   * Generate a personalized email draft for a specific plan item or contact
   */
  generateEmailDraft: protectedProcedure
    .input(
      z.object({
        salesAccountId: z.string(),
        contactId: z.string(),
        outreachPlanId: z.string().optional(),
      })
    )
    .mutation(async ({ ctx, input }) => {
      const [account, contact, repProfile] = await Promise.all([
        ctx.prisma.salesAccount.findUnique({
          where: { id: input.salesAccountId },
          include: { signals: true },
        }),
        ctx.prisma.contact.findUnique({ where: { id: input.contactId } }),
        ctx.prisma.repProfile.findUnique({ where: { userId: ctx.userId } }),
      ]);

      if (!account || !contact || !repProfile) {
        throw new TRPCError({ code: "NOT_FOUND" });
      }

      // KB snippets for this account's use case
      const kbArticles = await ctx.prisma.knowledgeBase.findMany({
        where: account.useCaseBucket
          ? { useCase: { contains: account.useCaseBucket, mode: "insensitive" } }
          : {},
        take: 5,
      });
      const kbSnippets = kbArticles.map((a) => `${a.title}\n${a.content}`);

      const brief: AccountBrief = {
        companyName: account.companyName,
        domain: account.domain,
        industry: account.industry,
        segment: account.segment,
        installSignals: account.signals.filter((s) => s.type === "install").map((s) => JSON.stringify(s.payload)),
        intentSignals: account.signals.filter((s) => s.type === "intent").map((s) => JSON.stringify(s.payload)),
        newsSignals: account.signals.filter((s) => s.type === "news").map((s) => JSON.stringify(s.payload)),
        contacts: [{ name: contact.name, title: contact.title ?? "" }],
      };
      const summary = await summarizeAccountSignals(brief);

      const repContext = {
        products: repProfile.products,
        territory: repProfile.territory,
        industries: repProfile.industries,
        toneFormality: repProfile.toneFormality,
        toneBrevity: repProfile.toneBrevity,
        writingStyleNote: repProfile.writingStyleNote,
        exampleEmails: repProfile.exampleEmails,
      };

      const draft = await generateEmail(
        summary,
        { name: contact.name, title: contact.title ?? "", company: account.companyName },
        repContext,
        account.useCaseBucket ?? "General",
        kbSnippets
      );

      // Save draft to plan item if provided
      if (input.outreachPlanId) {
        await ctx.prisma.outreachPlan.update({
          where: { id: input.outreachPlanId, userId: ctx.userId },
          data: {
            aiDraft: `Subject: ${draft.subject}\n\n${draft.body}`,
            modelVersion: process.env.WATSONX_GENERATION_MODEL,
          },
        });
      }

      // Audit log
      await ctx.prisma.auditLog.create({
        data: {
          userId: ctx.userId,
          action: "ai_generate_email",
          entity: "OutreachPlan",
          entityId: input.outreachPlanId,
          payload: { subject: draft.subject, contactId: input.contactId },
          modelVersion: process.env.WATSONX_GENERATION_MODEL,
        },
      });

      return draft;
    }),

  /**
   * Rank contacts for an account
   */
  rankContacts: protectedProcedure
    .input(z.object({ salesAccountId: z.string() }))
    .mutation(async ({ ctx, input }) => {
      const [account, repProfile] = await Promise.all([
        ctx.prisma.salesAccount.findUnique({
          where: { id: input.salesAccountId },
          include: { contacts: true },
        }),
        ctx.prisma.repProfile.findUnique({ where: { userId: ctx.userId } }),
      ]);

      if (!account || !repProfile) throw new TRPCError({ code: "NOT_FOUND" });

      const rankings = await rankContacts(
        account.contacts.map((c) => ({ name: c.name, title: c.title ?? "" })),
        {
          products: repProfile.products,
          territory: repProfile.territory,
          industries: repProfile.industries,
          toneFormality: repProfile.toneFormality,
          toneBrevity: repProfile.toneBrevity,
          writingStyleNote: repProfile.writingStyleNote,
          exampleEmails: repProfile.exampleEmails,
        },
        account.useCaseBucket ?? "General"
      );

      // Persist scores back to contacts
      await Promise.all(
        rankings.map((r) => {
          const contact = account.contacts.find((c) => c.name === r.name);
          if (!contact) return Promise.resolve();
          return ctx.prisma.contact.update({
            where: { id: contact.id },
            data: { personaFitScore: r.score },
          });
        })
      );

      return rankings;
    }),

  /**
   * Bulk enrich all accounts for this user's territory
   */
  bulkEnrich: protectedProcedure
    .input(
      z.object({
        accountIds: z.array(z.string()),
        concurrency: z.number().min(1).max(5).default(2),
      })
    )
    .mutation(async ({ ctx, input }) => {
      // Process in batches to avoid rate limiting
      const results: Array<{ id: string; status: "ok" | "error"; error?: string }> = [];

      for (let i = 0; i < input.accountIds.length; i += input.concurrency) {
        const batch = input.accountIds.slice(i, i + input.concurrency);
        const batchResults = await Promise.allSettled(
          batch.map(async (id) => {
            const account = await ctx.prisma.salesAccount.findUnique({
              where: { id },
              include: { signals: true, contacts: { select: { name: true, title: true } } },
            });
            if (!account) throw new Error("Not found");

            const repProfile = await ctx.prisma.repProfile.findUnique({ where: { userId: ctx.userId } });
            if (!repProfile) throw new Error("No rep profile");

            const brief: AccountBrief = {
              companyName: account.companyName,
              domain: account.domain,
              industry: account.industry,
              segment: account.segment,
              installSignals: account.signals.filter((s) => s.type === "install").map((s) => JSON.stringify(s.payload)),
              intentSignals: account.signals.filter((s) => s.type === "intent").map((s) => JSON.stringify(s.payload)),
              newsSignals: account.signals.filter((s) => s.type === "news").map((s) => JSON.stringify(s.payload)),
              contacts: account.contacts.map((c) => ({ name: c.name, title: c.title ?? "" })),
            };

            const summary = await summarizeAccountSignals(brief);
            const repContext = {
              products: repProfile.products,
              territory: repProfile.territory,
              industries: repProfile.industries,
              toneFormality: repProfile.toneFormality,
              toneBrevity: repProfile.toneBrevity,
              writingStyleNote: repProfile.writingStyleNote,
              exampleEmails: repProfile.exampleEmails,
            };
            const scored = await scoreAndTierAccount(summary, repContext);

            const kbArticles = await ctx.prisma.knowledgeBase.findMany({ take: 10 });
            const kbSnippets = kbArticles.map((a) => `${a.product}: ${a.content}`).slice(0, 3);
            const useCase = await classifyUseCaseBucket(summary, kbSnippets);

            await ctx.prisma.salesAccount.update({
              where: { id },
              data: {
                tier: scored.tier,
                priorityScore: scored.priorityScore,
                aiRationale: scored.rationale,
                useCaseBucket: useCase.bucket,
                lastEnrichedAt: new Date(),
              },
            });

            return id;
          })
        );

        for (let j = 0; j < batch.length; j++) {
          const r = batchResults[j];
          results.push({
            id: batch[j],
            status: r.status === "fulfilled" ? "ok" : "error",
            error: r.status === "rejected" ? String(r.reason) : undefined,
          });
        }

        // Small delay between batches to respect rate limits
        if (i + input.concurrency < input.accountIds.length) {
          await new Promise((res) => setTimeout(res, 1000));
        }
      }

      return { results, ok: results.filter((r) => r.status === "ok").length };
    }),
});
