"use client";

import { useState } from "react";
import { trpc } from "@/lib/trpc";

export default function KnowledgeBasePage() {
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ product: "", useCase: "", title: "", content: "" });

  const { data, isLoading, refetch } = trpc.knowledgeBase.list.useQuery({
    search: search || undefined,
  });

  const create = trpc.knowledgeBase.create.useMutation({
    onSuccess: () => { refetch(); setShowForm(false); setForm({ product: "", useCase: "", title: "", content: "" }); },
  });

  const del = trpc.knowledgeBase.delete.useMutation({ onSuccess: () => refetch() });

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Knowledge Base</h1>
        <button
          onClick={() => setShowForm((s) => !s)}
          className="bg-blue-600 text-white text-sm px-4 py-2 rounded hover:bg-blue-700"
        >
          {showForm ? "Cancel" : "+ Add Article"}
        </button>
      </div>

      {showForm && (
        <div className="bg-white border border-gray-200 rounded-lg p-5 mb-6">
          <h2 className="font-medium text-sm mb-4">New Article</h2>
          <div className="grid grid-cols-2 gap-3 mb-3">
            <input
              placeholder="Product (e.g. IBM Cloud)"
              value={form.product}
              onChange={(e) => setForm((f) => ({ ...f, product: e.target.value }))}
              className="border border-gray-200 rounded px-3 py-1.5 text-sm"
            />
            <input
              placeholder="Use Case (e.g. Modernization)"
              value={form.useCase}
              onChange={(e) => setForm((f) => ({ ...f, useCase: e.target.value }))}
              className="border border-gray-200 rounded px-3 py-1.5 text-sm"
            />
          </div>
          <input
            placeholder="Article title"
            value={form.title}
            onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
            className="border border-gray-200 rounded px-3 py-1.5 text-sm w-full mb-3"
          />
          <textarea
            placeholder="Article content — talking points, value props, customer stories..."
            value={form.content}
            onChange={(e) => setForm((f) => ({ ...f, content: e.target.value }))}
            className="border border-gray-200 rounded px-3 py-2 text-sm w-full h-32 mb-3"
          />
          <button
            onClick={() => create.mutate(form)}
            disabled={create.isPending || !form.product || !form.title || !form.content}
            className="bg-blue-600 text-white text-sm px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {create.isPending ? "Saving…" : "Save Article"}
          </button>
        </div>
      )}

      <input
        type="text"
        placeholder="Search articles…"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="border border-gray-200 rounded px-3 py-1.5 text-sm w-64 mb-4"
      />

      {isLoading && <p className="text-sm text-gray-500">Loading…</p>}

      <div className="space-y-3">
        {data?.map((article) => (
          <div key={article.id} className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex gap-2 mb-1">
                  <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                    {article.product}
                  </span>
                  <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded">
                    {article.useCase}
                  </span>
                </div>
                <h3 className="font-medium text-sm">{article.title}</h3>
                <p className="text-xs text-gray-500 mt-1 line-clamp-2">{article.content}</p>
              </div>
              <button
                onClick={() => del.mutate({ id: article.id })}
                className="text-xs text-red-400 hover:text-red-600 ml-4"
              >
                Delete
              </button>
            </div>
          </div>
        ))}
        {data?.length === 0 && (
          <p className="text-sm text-gray-400 text-center py-8">
            No articles yet. Add product knowledge to improve AI email quality.
          </p>
        )}
      </div>
    </div>
  );
}
