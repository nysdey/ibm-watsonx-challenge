import { z } from "zod";
import { createTRPCRouter, protectedProcedure } from "@/server/trpc";

export const outreachRouter = createTRPCRouter({
  /** List the current user's outreach plan */
  list: protectedProcedure
    .input(
      z.object({
        status: z.string().optional(),
        from: z.date().optional(),
        to: z.date().optional(),
        limit: z.number().default(50),
        offset: z.number().default(0),
      })
    )
    .query(async ({ ctx, input }) => {
      return ctx.prisma.outreachPlan.findMany({
        where: {
          userId: ctx.userId,
          ...(input.status ? { status: input.status } : {}),
          ...(input.from || input.to
            ? {
                scheduledDate: {
                  ...(input.from ? { gte: input.from } : {}),
                  ...(input.to ? { lte: input.to } : {}),
                },
              }
            : {}),
        },
        orderBy: { scheduledDate: "asc" },
        take: input.limit,
        skip: input.offset,
        include: {
          salesAccount: { select: { companyName: true, tier: true } },
          contact: { select: { name: true, title: true, email: true } },
          cadence: { select: { name: true } },
        },
      });
    }),

  /** Approve a pending plan item */
  approve: protectedProcedure
    .input(z.object({ id: z.string() }))
    .mutation(async ({ ctx, input }) => {
      return ctx.prisma.outreachPlan.update({
        where: { id: input.id, userId: ctx.userId },
        data: { status: "approved" },
      });
    }),

  /** Skip a plan item */
  skip: protectedProcedure
    .input(z.object({ id: z.string() }))
    .mutation(async ({ ctx, input }) => {
      return ctx.prisma.outreachPlan.update({
        where: { id: input.id, userId: ctx.userId },
        data: { status: "skipped" },
      });
    }),

  /** Mark a plan item as sent */
  markSent: protectedProcedure
    .input(z.object({ id: z.string(), salesloftId: z.string().optional() }))
    .mutation(async ({ ctx, input }) => {
      return ctx.prisma.outreachPlan.update({
        where: { id: input.id, userId: ctx.userId },
        data: { status: "sent" },
      });
    }),

  /** Update the AI draft for a plan item */
  updateDraft: protectedProcedure
    .input(z.object({ id: z.string(), draft: z.string() }))
    .mutation(async ({ ctx, input }) => {
      return ctx.prisma.outreachPlan.update({
        where: { id: input.id, userId: ctx.userId },
        data: { aiDraft: input.draft },
      });
    }),
});
