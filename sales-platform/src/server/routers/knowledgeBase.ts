import { z } from "zod";
import { createTRPCRouter, protectedProcedure } from "@/server/trpc";

export const knowledgeBaseRouter = createTRPCRouter({
  /** List all knowledge base articles */
  list: protectedProcedure
    .input(
      z.object({
        product: z.string().optional(),
        useCase: z.string().optional(),
        search: z.string().optional(),
      })
    )
    .query(async ({ ctx, input }) => {
      return ctx.prisma.knowledgeBase.findMany({
        where: {
          ...(input.product ? { product: input.product } : {}),
          ...(input.useCase ? { useCase: input.useCase } : {}),
          ...(input.search
            ? {
                OR: [
                  { title: { contains: input.search, mode: "insensitive" as const } },
                  { content: { contains: input.search, mode: "insensitive" as const } },
                  { product: { contains: input.search, mode: "insensitive" as const } },
                ],
              }
            : {}),
        },
        orderBy: { product: "asc" },
      });
    }),

  /** Create a knowledge base article */
  create: protectedProcedure
    .input(
      z.object({
        product: z.string(),
        useCase: z.string(),
        title: z.string(),
        content: z.string(),
      })
    )
    .mutation(async ({ ctx, input }) => {
      return ctx.prisma.knowledgeBase.create({ data: input });
    }),

  /** Update an article */
  update: protectedProcedure
    .input(
      z.object({
        id: z.string(),
        product: z.string().optional(),
        useCase: z.string().optional(),
        title: z.string().optional(),
        content: z.string().optional(),
      })
    )
    .mutation(async ({ ctx, input }) => {
      const { id, ...data } = input;
      return ctx.prisma.knowledgeBase.update({ where: { id }, data });
    }),

  /** Delete an article */
  delete: protectedProcedure
    .input(z.object({ id: z.string() }))
    .mutation(async ({ ctx, input }) => {
      return ctx.prisma.knowledgeBase.delete({ where: { id: input.id } });
    }),
});
