import { z } from "zod";
import { createTRPCRouter, protectedProcedure } from "@/server/trpc";

export const activitiesRouter = createTRPCRouter({
  /** Log an activity (call outcome, email, etc.) */
  log: protectedProcedure
    .input(
      z.object({
        salesAccountId: z.string(),
        contactId: z.string().optional(),
        type: z.enum(["call", "email", "linkedin"]),
        outcome: z
          .enum([
            "connected",
            "voicemail",
            "no_answer",
            "replied",
            "opened",
            "clicked",
            "bounced",
          ])
          .optional(),
        notes: z.string().optional(),
        salesloftId: z.string().optional(),
      })
    )
    .mutation(async ({ ctx, input }) => {
      return ctx.prisma.activity.create({
        data: { userId: ctx.userId, ...input },
      });
    }),

  /** Get recent activities for a user */
  list: protectedProcedure
    .input(
      z.object({
        salesAccountId: z.string().optional(),
        type: z.enum(["call", "email", "linkedin"]).optional(),
        limit: z.number().default(50),
        offset: z.number().default(0),
      })
    )
    .query(async ({ ctx, input }) => {
      return ctx.prisma.activity.findMany({
        where: {
          userId: ctx.userId,
          ...(input.salesAccountId ? { salesAccountId: input.salesAccountId } : {}),
          ...(input.type ? { type: input.type } : {}),
        },
        orderBy: { timestamp: "desc" },
        take: input.limit,
        skip: input.offset,
        include: {
          salesAccount: { select: { companyName: true } },
          contact: { select: { name: true, title: true } },
        },
      });
    }),

  /** Summary metrics for dashboard */
  metrics: protectedProcedure
    .input(
      z.object({
        since: z.date().optional(),
      })
    )
    .query(async ({ ctx, input }) => {
      const since = input.since ?? new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);

      const [calls, emails, linkedins] = await Promise.all([
        ctx.prisma.activity.groupBy({
          by: ["outcome"],
          where: { userId: ctx.userId, type: "call", timestamp: { gte: since } },
          _count: true,
        }),
        ctx.prisma.activity.groupBy({
          by: ["outcome"],
          where: { userId: ctx.userId, type: "email", timestamp: { gte: since } },
          _count: true,
        }),
        ctx.prisma.activity.groupBy({
          by: ["outcome"],
          where: { userId: ctx.userId, type: "linkedin", timestamp: { gte: since } },
          _count: true,
        }),
      ]);

      return { calls, emails, linkedins };
    }),
});
