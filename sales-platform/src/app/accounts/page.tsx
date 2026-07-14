"use client";

import { useState, useCallback } from "react";
import { trpc } from "@/lib/trpc";
import Papa from "papaparse";
import Link from "next/link";

export default function AccountsPage() {
  const [search, setSearch] = useState("");
  const [tierFilter, setTierFilter] = useState("");
  const [csvError, setCsvError] = useState("");
  const [importing, setImporting] = useState(false);
  const [importMessage, setImportMessage] = useState("");

  const { data, isLoading, refetch } = trpc.accounts.list.useQuery({
    search: search || undefined,
    tier: tierFilter || undefined,
    limit: 100,
  });

  const bulkImport = trpc.accounts.bulkImport.useMutation({
    onSuccess: (result) => {
      setImportMessage(`Imported ${result.created} accounts (${result.failed} failed)`);
      refetch();
      setImporting(false);
    },
  });

  const bulkEnrich = trpc.ai.bulkEnrich.useMutation({
    onSuccess: (result) => {
      setImportMessage(`Enriched ${result.ok} accounts`);
      refetch();
    },
  });

  const handleCsvUpload = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;
      setCsvError("");
      setImporting(true);

      Papa.parse(file, {
        header: true,
        skipEmptyLines: true,
        complete: (results) => {
          const rows = results.data as Record<string, string>[];
          const mapped = rows
            .map((row) => ({
              companyName:
                row["Company Name"] || row["company_name"] || row["Company"] || row["name"] || "",
              domain: row["Domain"] || row["domain"] || row["Website"] || undefined,
              industry: row["Industry"] || row["industry"] || undefined,
              segment: row["Segment"] || row["segment"] || row["Size"] || undefined,
            }))
            .filter((r) => r.companyName);

          if (mapped.length === 0) {
            setCsvError("No valid company names found. Expected column: Company Name");
            setImporting(false);
            return;
          }

          bulkImport.mutate(mapped);
        },
        error: (err) => {
          setCsvError(err.message);
          setImporting(false);
        },
      });
    },
    [bulkImport]
  );

  const handleEnrichAll = () => {
    if (!data?.accounts) return;
    const ids = data.accounts.map((a) => a.id);
    bulkEnrich.mutate({ accountIds: ids, concurrency: 2 });
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Accounts</h1>
        <div className="flex items-center gap-3">
          <label className="cursor-pointer bg-blue-600 text-white text-sm px-4 py-2 rounded-md hover:bg-blue-700">
            {importing ? "Importing…" : "Import CSV"}
            <input
              type="file"
              accept=".csv"
              className="hidden"
              onChange={handleCsvUpload}
              disabled={importing}
            />
          </label>
          <button
            onClick={handleEnrichAll}
            disabled={bulkEnrich.isPending || !data?.accounts?.length}
            className="bg-purple-600 text-white text-sm px-4 py-2 rounded-md hover:bg-purple-700 disabled:opacity-50"
          >
            {bulkEnrich.isPending ? "Enriching…" : "AI Enrich All"}
          </button>
        </div>
      </div>

      {(csvError || importMessage) && (
        <div
          className={`mb-4 p-3 rounded text-sm ${
            csvError ? "bg-red-50 text-red-700" : "bg-green-50 text-green-700"
          }`}
        >
          {csvError || importMessage}
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-3 mb-4">
        <input
          type="text"
          placeholder="Search accounts…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="border border-gray-200 rounded-md px-3 py-1.5 text-sm w-64 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <select
          value={tierFilter}
          onChange={(e) => setTierFilter(e.target.value)}
          className="border border-gray-200 rounded-md px-3 py-1.5 text-sm focus:outline-none"
        >
          <option value="">All Tiers</option>
          {["A", "B", "C", "D"].map((t) => (
            <option key={t} value={t}>
              Tier {t}
            </option>
          ))}
        </select>
        <span className="text-sm text-gray-500 self-center">
          {data?.total ?? 0} accounts
        </span>
      </div>

      {/* Table */}
      {isLoading && <p className="text-sm text-gray-500">Loading…</p>}
      {data?.accounts && (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-700">Company</th>
                <th className="text-left px-4 py-3 font-medium text-gray-700">Industry</th>
                <th className="text-left px-4 py-3 font-medium text-gray-700">Tier</th>
                <th className="text-left px-4 py-3 font-medium text-gray-700">Score</th>
                <th className="text-left px-4 py-3 font-medium text-gray-700">Use Case</th>
                <th className="text-left px-4 py-3 font-medium text-gray-700">Contacts</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.accounts.map((account) => (
                <tr key={account.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">
                    <Link href={`/accounts/${account.id}`} className="text-blue-600 hover:underline">
                      {account.companyName}
                    </Link>
                    {account.domain && (
                      <p className="text-xs text-gray-400">{account.domain}</p>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-600">{account.industry ?? "—"}</td>
                  <td className="px-4 py-3">
                    {account.tier ? (
                      <TierBadge tier={account.tier} />
                    ) : (
                      <span className="text-gray-300 text-xs">unscored</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {account.priorityScore != null
                      ? account.priorityScore.toFixed(0)
                      : "—"}
                  </td>
                  <td className="px-4 py-3 text-gray-600 text-xs">
                    {account.useCaseBucket ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-gray-600">{account._count.contacts}</td>
                  <td className="px-4 py-3">
                    <Link
                      href={`/accounts/${account.id}`}
                      className="text-xs text-blue-600 hover:underline"
                    >
                      View →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {data.accounts.length === 0 && (
            <p className="text-center text-sm text-gray-400 py-12">
              No accounts yet — import a CSV to get started.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function TierBadge({ tier }: { tier: string }) {
  const colors: Record<string, string> = {
    A: "bg-green-100 text-green-800",
    B: "bg-blue-100 text-blue-800",
    C: "bg-yellow-100 text-yellow-800",
    D: "bg-red-100 text-red-800",
  };
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${colors[tier] ?? "bg-gray-100 text-gray-600"}`}>
      {tier}
    </span>
  );
}
