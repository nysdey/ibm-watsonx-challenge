"use client";

import { use, useState } from "react";
import { trpc } from "@/lib/trpc";

export default function AccountDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { data: account, isLoading, refetch } = trpc.accounts.byId.useQuery({ id });

  const enrichAccount = trpc.ai.enrichAccount.useMutation({ onSuccess: () => refetch() });
  const generatePlan = trpc.ai.generatePlan.useMutation({ onSuccess: () => refetch() });
  const rankContacts = trpc.ai.rankContacts.useMutation({ onSuccess: () => refetch() });
  const generateEmail = trpc.ai.generateEmailDraft.useMutation();
  const [emailDraft, setEmailDraft] = useState<{ subject: string; body: string } | null>(null);
  const [selectedContactId, setSelectedContactId] = useState<string>("");

  const handleEnrich = () => enrichAccount.mutate({ salesAccountId: id });
  const handlePlan = () => generatePlan.mutate({ salesAccountId: id });
  const handleRank = () => rankContacts.mutate({ salesAccountId: id });
  const handleEmail = () => {
    if (!selectedContactId) return;
    generateEmail.mutate(
      { salesAccountId: id, contactId: selectedContactId },
      { onSuccess: (draft) => setEmailDraft(draft) }
    );
  };

  if (isLoading) return <div className="p-8 text-sm text-gray-500">Loading…</div>;
  if (!account) return <div className="p-8 text-sm text-red-500">Account not found</div>;

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold">{account.companyName}</h1>
          <p className="text-sm text-gray-500">
            {account.industry} · {account.segment} · {account.domain}
          </p>
          {account.tier && (
            <span className="inline-block mt-1 px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
              Tier {account.tier} · Score {account.priorityScore?.toFixed(0)}
            </span>
          )}
          {account.useCaseBucket && (
            <span className="ml-2 inline-block mt-1 px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
              {account.useCaseBucket}
            </span>
          )}
          {account.aiRationale && (
            <p className="text-xs text-gray-500 mt-2 max-w-xl">{account.aiRationale}</p>
          )}
        </div>

        {/* Action buttons */}
        <div className="flex flex-col gap-2">
          <button
            onClick={handleEnrich}
            disabled={enrichAccount.isPending}
            className="text-sm bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 disabled:opacity-50"
          >
            {enrichAccount.isPending ? "Enriching…" : "AI Enrich"}
          </button>
          <button
            onClick={handlePlan}
            disabled={generatePlan.isPending || !account.tier}
            className="text-sm bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
            title={!account.tier ? "Run AI Enrich first" : ""}
          >
            {generatePlan.isPending ? "Planning…" : "Generate Plan"}
          </button>
          <button
            onClick={handleRank}
            disabled={rankContacts.isPending}
            className="text-sm bg-gray-700 text-white px-4 py-2 rounded hover:bg-gray-800 disabled:opacity-50"
          >
            {rankContacts.isPending ? "Ranking…" : "Rank Contacts"}
          </button>
        </div>
      </div>

      {/* Two-column: contacts + signals */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* Contacts */}
        <div className="bg-white border border-gray-200 rounded-lg p-5">
          <h2 className="font-medium text-sm mb-3">Contacts ({account.contacts.length})</h2>
          {account.contacts.length === 0 ? (
            <p className="text-xs text-gray-400">No contacts — run ZoomInfo enrichment</p>
          ) : (
            <ul className="space-y-2">
              {account.contacts.map((c) => (
                <li key={c.id} className="flex items-start justify-between">
                  <div>
                    <p className="text-sm font-medium">
                      {c.name}{" "}
                      {c.isItDirector && (
                        <span className="text-xs bg-green-100 text-green-700 px-1 rounded">IT Dir</span>
                      )}
                    </p>
                    <p className="text-xs text-gray-500">{c.title}</p>
                    <p className="text-xs text-gray-400">{c.email}</p>
                  </div>
                  {c.personaFitScore != null && (
                    <span className="text-xs text-blue-600 font-medium">
                      {c.personaFitScore.toFixed(0)}
                    </span>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Signals */}
        <div className="bg-white border border-gray-200 rounded-lg p-5">
          <h2 className="font-medium text-sm mb-3">Signals ({account.signals.length})</h2>
          {account.signals.length === 0 ? (
            <p className="text-xs text-gray-400">No signals yet</p>
          ) : (
            <ul className="space-y-2">
              {account.signals.slice(0, 8).map((s) => (
                <li key={s.id} className="text-xs">
                  <span className="uppercase font-semibold text-gray-500">{s.type}</span>{" "}
                  <span className="text-gray-600">· {s.source}</span>
                  {s.score != null && (
                    <span className="ml-1 text-blue-600">{(s.score * 100).toFixed(0)}%</span>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* Email generator */}
      {account.contacts.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-5 mb-6">
          <h2 className="font-medium text-sm mb-3">Generate Email Draft</h2>
          <div className="flex gap-3 mb-4">
            <select
              value={selectedContactId}
              onChange={(e) => setSelectedContactId(e.target.value)}
              className="border border-gray-200 rounded px-3 py-1.5 text-sm flex-1 focus:outline-none"
            >
              <option value="">Select contact…</option>
              {account.contacts.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} — {c.title}
                </option>
              ))}
            </select>
            <button
              onClick={handleEmail}
              disabled={generateEmail.isPending || !selectedContactId}
              className="bg-green-600 text-white text-sm px-4 py-1.5 rounded hover:bg-green-700 disabled:opacity-50"
            >
              {generateEmail.isPending ? "Writing…" : "Generate"}
            </button>
          </div>

          {emailDraft && (
            <div className="border border-gray-200 rounded p-4 bg-gray-50">
              <p className="text-xs text-gray-500 mb-1">Subject:</p>
              <p className="text-sm font-medium mb-3">{emailDraft.subject}</p>
              <p className="text-xs text-gray-500 mb-1">Body:</p>
              <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans">{emailDraft.body}</pre>
            </div>
          )}
        </div>
      )}

      {/* Outreach plan */}
      {account.outreachPlans.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-5">
          <h2 className="font-medium text-sm mb-3">Upcoming Outreach Plan</h2>
          <ul className="space-y-2">
            {account.outreachPlans.map((p) => (
              <li key={p.id} className="flex items-center gap-3 text-sm">
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                  p.status === "approved" ? "bg-green-100 text-green-700" : "bg-yellow-100 text-yellow-700"
                }`}>
                  {p.status}
                </span>
                <span className="capitalize text-gray-700">{p.actionType}</span>
                <span className="text-gray-400 text-xs">
                  {new Date(p.scheduledDate).toLocaleDateString()}
                </span>
                {p.aiPromptLog && (
                  <span className="text-gray-500 text-xs">— {p.aiPromptLog}</span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
