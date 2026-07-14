import { z } from "zod";
import { createTRPCRouter, protectedProcedure } from "@/server/trpc";

export const contactsRouter = createTRPCRouter({
  /** List contacts for an account */
  byAccount: protectedProcedure
    .input(z.object({ salesAccountId: z.string() }))
    .query(async ({ ctx, input }) => {
      return ctx.prisma.contact.findMany({
        where: { salesAccountId: input.salesAccountId },
        orderBy: [{ isItDirector: "desc" }, { personaFitScore: "desc" }],
      });
    }),

  /** Create or update a contact */
  upsert: protectedProcedure
    .input(
      z.object({
        id: z.string().optional(),
        salesAccountId: z.string(),
        name: z.string(),
        title: z.string().optional(),
        email: z.string().email().optional(),
        phone: z.string().optional(),
        linkedIn: z.string().url().optional(),
        source: z.enum(["zoominfo", "manual", "csv"]).default("manual"),
        isItDirector: z.boolean().optional(),
      })
    )
    .mutation(async ({ ctx, input }) => {
      const { id, salesAccountId, ...data } = input;
      if (id) {
        return ctx.prisma.contact.update({ where: { id }, data });
      }
      return ctx.prisma.contact.create({ data: { salesAccountId, ...data } });
    }),

  /** Delete a contact */
  delete: protectedProcedure
    .input(z.object({ id: z.string() }))
    .mutation(async ({ ctx, input }) => {
      return ctx.prisma.contact.delete({ where: { id: input.id } });
    }),

  /** Bulk import contacts (from ZoomInfo enrichment or CSV) */
  bulkImport: protectedProcedure
    .input(
      z.array(
        z.object({
          salesAccountId: z.string(),
          name: z.string(),
          title: z.string().optional(),
          email: z.string().email().optional().or(z.literal("")),
          phone: z.string().optional(),
          linkedIn: z.string().optional(),
          source: z.enum(["zoominfo", "manual", "csv"]).default("manual"),
          isItDirector: z.boolean().default(false),
        })
      )
    )
    .mutation(async ({ ctx, input }) => {
      const result = await ctx.prisma.contact.createMany({
        data: input.map((c) => ({
          ...c,
          email: c.email || undefined,
        })),
        skipDuplicates: true,
      });
      return { created: result.count };
    }),
});
