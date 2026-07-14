import { createTRPCRouter, protectedProcedure } from "@/server/trpc";

export const dashboardRouter = createTRPCRouter({
  /** High-level snapshot for the dashboard */
  snapshot: protectedProcedure.query(async ({ ctx }) => {
    const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);

    const [
      totalAccounts,
      tierCounts,
      bucketCounts,
      pendingPlanItems,
      activitiesThisMonth,
      missingItDirectorCount,
    ] = await Promise.all([
      ctx.prisma.salesAccount.count(),
      ctx.prisma.salesAccount.groupBy({ by: ["tier"], _count: true }),
      ctx.prisma.salesAccount.groupBy({ by: ["useCaseBucket"], _count: true }),
      ctx.prisma.outreachPlan.count({
        where: { userId: ctx.userId, status: "pending" },
      }),
      ctx.prisma.activity.count({
        where: { userId: ctx.userId, timestamp: { gte: thirtyDaysAgo } },
      }),
      ctx.prisma.salesAccount
        .findMany({ include: { contacts: { where: { isItDirector: true } } } })
        .then((accs) => accs.filter((a) => a.contacts.length === 0).length),
    ]);

    return {
      totalAccounts,
      tierCounts,
      bucketCounts,
      pendingPlanItems,
      activitiesThisMonth,
      missingItDirectorCount,
    };
  }),
});
