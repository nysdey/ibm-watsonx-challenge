"use client";

import { useState } from "react";
import { trpc } from "@/lib/trpc";

export default function ProfilePage() {
  const { data: profile, isLoading } = trpc.repProfile.get.useQuery();
  const save = trpc.repProfile.save.useMutation();

  const [form, setForm] = useState({
    products: [] as string[],
    territory: "",
    industries: [] as string[],
    toneFormality: 3,
    toneBrevity: 3,
    automationLevel: 1,
    writingStyleNote: "",
    notifyDigest: "daily" as "daily" | "weekly" | "none",
    exampleEmails: [] as string[],
  });
  const [productInput, setProductInput] = useState("");
  const [industryInput, setIndustryInput] = useState("");
  const [exampleInput, setExampleInput] = useState("");
  const [saved, setSaved] = useState(false);

  // Initialize form from loaded profile
  const [initialized, setInitialized] = useState(false);
  if (profile && !initialized) {
    setForm({
      products: profile.products,
      territory: profile.territory ?? "",
      industries: profile.industries,
      toneFormality: profile.toneFormality,
      toneBrevity: profile.toneBrevity,
      automationLevel: profile.automationLevel,
      writingStyleNote: profile.writingStyleNote ?? "",
      notifyDigest: profile.notifyDigest as "daily" | "weekly" | "none",
      exampleEmails: profile.exampleEmails,
    });
    setInitialized(true);
  }

  const handleSave = async () => {
    await save.mutateAsync(form);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  if (isLoading) return <div className="p-8 text-sm text-gray-500">Loading…</div>;

  const AUTOMATION_LABELS = [
    "0 — Manual (approve every action)",
    "1 — Assisted (daily digest approval)",
    "2 — Semi-auto (loads drafts, you send)",
    "3 — Auto during business hours",
    "4 — Fully automatic",
  ];

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-semibold mb-6">My Rep Profile</h1>

      <div className="space-y-6">
        {/* Products */}
        <Section title="Products You Sell">
          <div className="flex gap-2 mb-2">
            <input
              value={productInput}
              onChange={(e) => setProductInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && productInput.trim()) {
                  setForm((f) => ({ ...f, products: [...f.products, productInput.trim()] }));
                  setProductInput("");
                }
              }}
              placeholder="Add product (press Enter)"
              className="border border-gray-200 rounded px-3 py-1.5 text-sm flex-1"
            />
          </div>
          <div className="flex flex-wrap gap-2">
            {form.products.map((p) => (
              <span key={p} className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded flex items-center gap-1">
                {p}
                <button onClick={() => setForm((f) => ({ ...f, products: f.products.filter((x) => x !== p) }))} className="hover:text-red-600">×</button>
              </span>
            ))}
          </div>
        </Section>

        {/* Territory */}
        <Section title="Territory">
          <input
            value={form.territory}
            onChange={(e) => setForm((f) => ({ ...f, territory: e.target.value }))}
            placeholder="e.g. US West, EMEA, Northeast"
            className="border border-gray-200 rounded px-3 py-1.5 text-sm w-full"
          />
        </Section>

        {/* Industries */}
        <Section title="Target Industries">
          <div className="flex gap-2 mb-2">
            <input
              value={industryInput}
              onChange={(e) => setIndustryInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && industryInput.trim()) {
                  setForm((f) => ({ ...f, industries: [...f.industries, industryInput.trim()] }));
                  setIndustryInput("");
                }
              }}
              placeholder="Add industry (press Enter)"
              className="border border-gray-200 rounded px-3 py-1.5 text-sm flex-1"
            />
          </div>
          <div className="flex flex-wrap gap-2">
            {form.industries.map((ind) => (
              <span key={ind} className="bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded flex items-center gap-1">
                {ind}
                <button onClick={() => setForm((f) => ({ ...f, industries: f.industries.filter((x) => x !== ind) }))} className="hover:text-red-600">×</button>
              </span>
            ))}
          </div>
        </Section>

        {/* Tone sliders */}
        <Section title="Writing Tone">
          <div className="space-y-4">
            <SliderField
              label={`Formality: ${["Very Casual", "Casual", "Semi-formal", "Formal", "Very Formal"][form.toneFormality - 1]}`}
              value={form.toneFormality}
              min={1} max={5}
              onChange={(v) => setForm((f) => ({ ...f, toneFormality: v }))}
            />
            <SliderField
              label={`Brevity: ${["Very Detailed", "Detailed", "Balanced", "Concise", "Very Brief"][form.toneBrevity - 1]}`}
              value={form.toneBrevity}
              min={1} max={5}
              onChange={(v) => setForm((f) => ({ ...f, toneBrevity: v }))}
            />
          </div>
          <div className="mt-3">
            <label className="block text-xs text-gray-500 mb-1">Additional style notes</label>
            <textarea
              value={form.writingStyleNote}
              onChange={(e) => setForm((f) => ({ ...f, writingStyleNote: e.target.value }))}
              placeholder="e.g. Always reference the prospect's industry, end with a soft ask..."
              className="border border-gray-200 rounded px-3 py-2 text-sm w-full h-20"
            />
          </div>
        </Section>

        {/* Example emails */}
        <Section title="Example Emails (for style matching)">
          <textarea
            value={exampleInput}
            onChange={(e) => setExampleInput(e.target.value)}
            placeholder="Paste an example email you&apos;ve written…"
            className="border border-gray-200 rounded px-3 py-2 text-sm w-full h-24 mb-2"
          />
          <button
            onClick={() => {
              if (exampleInput.trim()) {
                setForm((f) => ({ ...f, exampleEmails: [...f.exampleEmails, exampleInput.trim()] }));
                setExampleInput("");
              }
            }}
            className="text-xs bg-gray-700 text-white px-3 py-1.5 rounded hover:bg-gray-800"
          >
            Add Example
          </button>
          <p className="text-xs text-gray-400 mt-1">{form.exampleEmails.length} example(s) saved</p>
        </Section>

        {/* Automation level */}
        <Section title="Automation Level">
          <div className="space-y-2">
            {AUTOMATION_LABELS.map((label, i) => (
              <label key={i} className="flex items-center gap-3 cursor-pointer">
                <input
                  type="radio"
                  name="automation"
                  checked={form.automationLevel === i}
                  onChange={() => setForm((f) => ({ ...f, automationLevel: i }))}
                  className="text-blue-600"
                />
                <span className="text-sm text-gray-700">{label}</span>
              </label>
            ))}
          </div>
        </Section>

        {/* Notification digest */}
        <Section title="Notification Frequency">
          <select
            value={form.notifyDigest}
            onChange={(e) => setForm((f) => ({ ...f, notifyDigest: e.target.value as "daily" | "weekly" | "none" }))}
            className="border border-gray-200 rounded px-3 py-1.5 text-sm"
          >
            <option value="daily">Daily digest</option>
            <option value="weekly">Weekly digest</option>
            <option value="none">No notifications</option>
          </select>
        </Section>

        <button
          onClick={handleSave}
          disabled={save.isPending}
          className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 text-sm font-medium"
        >
          {save.isPending ? "Saving…" : saved ? "Saved!" : "Save Profile"}
        </button>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-5">
      <h2 className="font-medium text-sm mb-4">{title}</h2>
      {children}
    </div>
  );
}

function SliderField({
  label,
  value,
  min,
  max,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  onChange: (v: number) => void;
}) {
  return (
    <div>
      <label className="block text-xs text-gray-500 mb-1">{label}</label>
      <input
        type="range"
        min={min}
        max={max}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-blue-600"
      />
      <div className="flex justify-between text-xs text-gray-300 mt-0.5">
        <span>{min}</span>
        <span>{max}</span>
      </div>
    </div>
  );
}
