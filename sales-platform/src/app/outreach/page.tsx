"use client";

import { useState } from "react";
import { trpc } from "@/lib/trpc";

export default function OutreachPage() {
  const today = new Date();
  const nextWeek = new Date(today);
  nextWeek.setDate(today.getDate() + 7);

  const [statusFilter, setStatusFilter] = useState("pending");

  const { data, isLoading, refetch } = trpc.outreach.list.useQuery({
    status: statusFilter || undefined,
    from: today,
    to: nextWeek,
    limit: 100,
  });

  const approve = trpc.outreach.approve.useMutation({ onSuccess: () => refetch() });
  const skip = trpc.outreach.skip.useMutation({ onSuccess: () => refetch() });

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Outreach Plan</h1>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="border border-gray-200 rounded px-3 py-1.5 text-sm"
        >
          <option value="">All</option>
          <option value="pending">Pending Approval</option>
          <option value="approved">Approved</option>
          <option value="sent">Sent</option>
          <option value="skipped">Skipped</option>
        </select>
      </div>

      {isLoading && <p className="text-sm text-gray-500">Loading…</p>}

      {data && data.length === 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
          <p className="text-sm text-gray-400">
            No outreach plan items. Go to an account and click &quot;Generate Plan&quot;.
          </p>
        </div>
      )}

      {data && data.length > 0 && (
        <div className="space-y-3">
          {data.map((item) => (
            <div
              key={item.id}
              className="bg-white border border-gray-200 rounded-lg p-4 flex items-center gap-4"
            >
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-medium text-sm">{item.salesAccount.companyName}</span>
                  {item.salesAccount.tier && (
                    <span className="text-xs bg-blue-100 text-blue-700 px-1.5 rounded">
                      Tier {item.salesAccount.tier}
                    </span>
                  )}
                  <span className="text-xs text-gray-400">
                    {new Date(item.scheduledDate).toLocaleDateString()}
                  </span>
                </div>
                <p className="text-xs text-gray-600">
                  <span className="capitalize font-medium">{item.actionType}</span>
                  {item.contact && ` → ${item.contact.name} (${item.contact.title})`}
                </p>
                {item.aiPromptLog && (
                  <p className="text-xs text-gray-400 mt-0.5">{item.aiPromptLog}</p>
                )}
                {item.aiDraft && (
                  <details className="mt-2">
                    <summary className="text-xs text-blue-600 cursor-pointer">View draft</summary>
                    <pre className="text-xs text-gray-700 whitespace-pre-wrap mt-2 bg-gray-50 p-3 rounded">
                      {item.aiDraft}
                    </pre>
                  </details>
                )}
              </div>

              <div className="flex gap-2 shrink-0">
                {item.status === "pending" && (
                  <>
                    <button
                      onClick={() => approve.mutate({ id: item.id })}
                      disabled={approve.isPending}
                      className="text-xs bg-green-600 text-white px-3 py-1.5 rounded hover:bg-green-700"
                    >
                      Approve
                    </button>
                    <button
                      onClick={() => skip.mutate({ id: item.id })}
                      disabled={skip.isPending}
                      className="text-xs border border-gray-200 text-gray-600 px-3 py-1.5 rounded hover:bg-gray-50"
                    >
                      Skip
                    </button>
                  </>
                )}
                {item.status === "approved" && (
                  <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">
                    Approved
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
