import { z } from "zod";
import { createTRPCRouter, protectedProcedure } from "@/server/trpc";

export const repProfileRouter = createTRPCRouter({
  /** Get the current user's rep profile */
  get: protectedProcedure.query(async ({ ctx }) => {
    return ctx.prisma.repProfile.findUnique({
      where: { userId: ctx.userId },
    });
  }),

  /** Create or update rep profile */
  save: protectedProcedure
    .input(
      z.object({
        products: z.array(z.string()).default([]),
        territory: z.string().optional(),
        industries: z.array(z.string()).default([]),
        toneFormality: z.number().min(1).max(5).default(3),
        toneBrevity: z.number().min(1).max(5).default(3),
        automationLevel: z.number().min(0).max(4).default(1),
        exampleEmails: z.array(z.string()).default([]),
        writingStyleNote: z.string().optional(),
        notifyDigest: z.enum(["daily", "weekly", "none"]).default("daily"),
      })
    )
    .mutation(async ({ ctx, input }) => {
      return ctx.prisma.repProfile.upsert({
        where: { userId: ctx.userId },
        create: { userId: ctx.userId, ...input },
        update: input,
      });
    }),
});
