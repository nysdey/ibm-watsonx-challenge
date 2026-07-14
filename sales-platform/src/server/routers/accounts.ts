import { z } from "zod";
import { createTRPCRouter, protectedProcedure } from "@/server/trpc";
import { TRPCError } from "@trpc/server";

export const accountsRouter = createTRPCRouter({
  /** List all sales accounts */
  list: protectedProcedure
    .input(
      z.object({
        tier: z.string().optional(),
        useCaseBucket: z.string().optional(),
        search: z.string().optional(),
        limit: z.number().min(1).max(200).default(50),
        offset: z.number().default(0),
      })
    )
    .query(async ({ ctx, input }) => {
      const where = {
        ...(input.tier ? { tier: input.tier } : {}),
        ...(input.useCaseBucket ? { useCaseBucket: input.useCaseBucket } : {}),
        ...(input.search
          ? {
              OR: [
                { companyName: { contains: input.search, mode: "insensitive" as const } },
                { domain: { contains: input.search, mode: "insensitive" as const } },
                { industry: { contains: input.search, mode: "insensitive" as const } },
              ],
            }
          : {}),
      };

      const [accounts, total] = await Promise.all([
        ctx.prisma.salesAccount.findMany({
          where,
          orderBy: [{ priorityScore: "desc" }, { companyName: "asc" }],
          take: input.limit,
          skip: input.offset,
          include: { _count: { select: { contacts: true, signals: true } } },
        }),
        ctx.prisma.salesAccount.count({ where }),
      ]);

      return { accounts, total };
    }),

  /** Get a single account with contacts and signals */
  byId: protectedProcedure
    .input(z.object({ id: z.string() }))
    .query(async ({ ctx, input }) => {
      const account = await ctx.prisma.salesAccount.findUnique({
        where: { id: input.id },
        include: {
          contacts: { orderBy: { personaFitScore: "desc" } },
          signals: { orderBy: { ingestedAt: "desc" }, take: 20 },
          activities: { orderBy: { timestamp: "desc" }, take: 20 },
          outreachPlans: {
            where: { status: { in: ["pending", "approved"] } },
            orderBy: { scheduledDate: "asc" },
            take: 10,
          },
        },
      });

      if (!account) throw new TRPCError({ code: "NOT_FOUND" });
      return account;
    }),

  /** Bulk import accounts from CSV parse result */
  bulkImport: protectedProcedure
    .input(
      z.array(
        z.object({
          companyName: z.string(),
          domain: z.string().optional(),
          industry: z.string().optional(),
          segment: z.string().optional(),
        })
      )
    )
    .mutation(async ({ ctx, input }) => {
      const results = await Promise.allSettled(
        input.map((row) =>
          ctx.prisma.salesAccount.upsert({
            where: {
              companyName_domain: {
                companyName: row.companyName,
                domain: row.domain ?? "",
              },
            },
            create: row,
            update: { industry: row.industry, segment: row.segment },
          })
        )
      );

      const created = results.filter((r) => r.status === "fulfilled").length;
      const failed = results.filter((r) => r.status === "rejected").length;
      return { created, failed };
    }),

  /** Update tier / use-case manually */
  update: protectedProcedure
    .input(
      z.object({
        id: z.string(),
        tier: z.string().optional(),
        useCaseBucket: z.string().optional(),
        segment: z.string().optional(),
        industry: z.string().optional(),
      })
    )
    .mutation(async ({ ctx, input }) => {
      const { id, ...data } = input;
      return ctx.prisma.salesAccount.update({ where: { id }, data });
    }),

  /** Delete an account */
  delete: protectedProcedure
    .input(z.object({ id: z.string() }))
    .mutation(async ({ ctx, input }) => {
      return ctx.prisma.salesAccount.delete({ where: { id: input.id } });
    }),

  /** Flag accounts without IT Director contact */
  flagMissingItDirector: protectedProcedure.query(async ({ ctx }) => {
    const accounts = await ctx.prisma.salesAccount.findMany({
      include: { contacts: { where: { isItDirector: true } } },
    });
    return accounts
      .filter((a) => a.contacts.length === 0)
      .map((a) => ({ id: a.id, companyName: a.companyName }));
  }),
});
