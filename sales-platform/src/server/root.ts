import { createTRPCRouter } from "@/server/trpc";
import { accountsRouter } from "./routers/accounts";
import { contactsRouter } from "./routers/contacts";
import { repProfileRouter } from "./routers/repProfile";
import { aiRouter } from "./routers/ai";
import { outreachRouter } from "./routers/outreach";
import { activitiesRouter } from "./routers/activities";
import { knowledgeBaseRouter } from "./routers/knowledgeBase";
import { dashboardRouter } from "./routers/dashboard";

export const appRouter = createTRPCRouter({
  accounts: accountsRouter,
  contacts: contactsRouter,
  repProfile: repProfileRouter,
  ai: aiRouter,
  outreach: outreachRouter,
  activities: activitiesRouter,
  knowledgeBase: knowledgeBaseRouter,
  dashboard: dashboardRouter,
});

export type AppRouter = typeof appRouter;
