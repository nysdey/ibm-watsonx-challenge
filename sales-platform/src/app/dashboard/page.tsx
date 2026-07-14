"use client";

import { trpc } from "@/lib/trpc";

export default function DashboardPage() {
  const { data, isLoading } = trpc.dashboard.snapshot.useQuery();

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-semibold mb-6">Dashboard</h1>

      {isLoading && (
        <p className="text-sm text-gray-500">Loading snapshot…</p>
      )}

      {data && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <StatCard label="Total Accounts" value={data.totalAccounts} />
          <StatCard label="Pending Actions" value={data.pendingPlanItems} />
          <StatCard label="Activities (30d)" value={data.activitiesThisMonth} />
          <StatCard label="Missing IT Director" value={data.missingItDirectorCount} color="orange" />
        </div>
      )}

      {data && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Tier breakdown */}
          <div className="bg-white border border-gray-200 rounded-lg p-5">
            <h2 className="font-medium text-sm mb-3">Account Tier Breakdown</h2>
            <div className="space-y-2">
              {["A", "B", "C", "D", null].map((tier) => {
                const count =
                  data.tierCounts.find((t) => t.tier === tier)?._count ?? 0;
                const label = tier ?? "Unscored";
                return (
                  <div key={label} className="flex items-center gap-2">
                    <span
                      className={`w-6 h-6 rounded text-xs font-bold flex items-center justify-center text-white ${
                        tier === "A"
                          ? "bg-green-500"
                          : tier === "B"
                          ? "bg-blue-500"
                          : tier === "C"
                          ? "bg-yellow-500"
                          : tier === "D"
                          ? "bg-red-400"
                          : "bg-gray-300"
                      }`}
                    >
                      {label}
                    </span>
                    <div className="flex-1 bg-gray-100 rounded h-4">
                      <div
                        className="h-4 rounded bg-blue-200"
                        style={{
                          width: data.totalAccounts
                            ? `${(count / data.totalAccounts) * 100}%`
                            : "0%",
                        }}
                      />
                    </div>
                    <span className="text-xs text-gray-600 w-6">{count}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Use-case buckets */}
          <div className="bg-white border border-gray-200 rounded-lg p-5">
            <h2 className="font-medium text-sm mb-3">Use-Case Buckets</h2>
            <div className="space-y-1">
              {data.bucketCounts
                .filter((b) => b.useCaseBucket)
                .sort((a, b) => b._count - a._count)
                .map((b) => (
                  <div key={b.useCaseBucket} className="flex justify-between text-sm">
                    <span className="text-gray-700">{b.useCaseBucket}</span>
                    <span className="font-medium">{b._count}</span>
                  </div>
                ))}
              {data.bucketCounts.filter((b) => b.useCaseBucket).length === 0 && (
                <p className="text-sm text-gray-400">Run AI enrichment to populate buckets</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  color = "default",
}: {
  label: string;
  value: number;
  color?: "default" | "orange";
}) {
  return (
    <div
      className={`bg-white border rounded-lg p-4 ${
        color === "orange" ? "border-orange-200" : "border-gray-200"
      }`}
    >
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p
        className={`text-3xl font-semibold ${
          color === "orange" ? "text-orange-500" : "text-gray-900"
        }`}
      >
        {value}
      </p>
    </div>
  );
}
