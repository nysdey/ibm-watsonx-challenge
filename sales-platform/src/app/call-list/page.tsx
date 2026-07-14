"use client";

import { trpc } from "@/lib/trpc";

export default function CallListPage() {
  const today = new Date();
  const tomorrow = new Date(today);
  tomorrow.setDate(today.getDate() + 1);

  const { data, isLoading, refetch } = trpc.outreach.list.useQuery({
    status: "approved",
    to: tomorrow,
    limit: 50,
  });

  const logActivity = trpc.activities.log.useMutation({ onSuccess: () => refetch() });
  const markSent = trpc.outreach.markSent.useMutation({ onSuccess: () => refetch() });

  const callItems = data?.filter((d) => d.actionType === "call") ?? [];

  const handleOutcome = (
    item: (typeof callItems)[0],
    outcome: "connected" | "voicemail" | "no_answer"
  ) => {
    logActivity.mutate({
      salesAccountId: item.salesAccountId,
      contactId: item.contactId ?? undefined,
      type: "call",
      outcome,
    });
    markSent.mutate({ id: item.id });
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-semibold mb-2">Today&apos;s Call List</h1>
      <p className="text-sm text-gray-500 mb-6">
        {callItems.length} approved calls scheduled for today
      </p>

      {isLoading && <p className="text-sm text-gray-500">Loading…</p>}

      {!isLoading && callItems.length === 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
          <p className="text-sm text-gray-400">
            No calls scheduled for today. Approve outreach plan items first.
          </p>
        </div>
      )}

      <div className="space-y-4">
        {callItems.map((item) => (
          <div key={item.id} className="bg-white border border-gray-200 rounded-lg p-5">
            <div className="flex items-start justify-between mb-3">
              <div>
                <h2 className="font-medium">{item.salesAccount.companyName}</h2>
                {item.contact && (
                  <p className="text-sm text-gray-600">
                    {item.contact.name} · {item.contact.title}
                  </p>
                )}
                {item.contact?.email && (
                  <p className="text-xs text-gray-400">{item.contact.email}</p>
                )}
              </div>
              {item.salesAccount.tier && (
                <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                  Tier {item.salesAccount.tier}
                </span>
              )}
            </div>

            {item.aiPromptLog && (
              <div className="bg-blue-50 rounded p-3 mb-3">
                <p className="text-xs font-medium text-blue-700 mb-1">Talking point</p>
                <p className="text-sm text-blue-900">{item.aiPromptLog}</p>
              </div>
            )}

            <div className="flex gap-2">
              <button
                onClick={() => handleOutcome(item, "connected")}
                className="flex-1 text-sm bg-green-600 text-white py-2 rounded hover:bg-green-700"
              >
                Connected
              </button>
              <button
                onClick={() => handleOutcome(item, "voicemail")}
                className="flex-1 text-sm bg-yellow-500 text-white py-2 rounded hover:bg-yellow-600"
              >
                Voicemail
              </button>
              <button
                onClick={() => handleOutcome(item, "no_answer")}
                className="flex-1 text-sm border border-gray-200 text-gray-600 py-2 rounded hover:bg-gray-50"
              >
                No Answer
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
