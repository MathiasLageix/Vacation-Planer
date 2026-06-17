"use client";
import type { Insights } from "../types";

export function InsightsSection({ insights, title }: { insights: Insights; title: string }) {
  const hasInsights = insights.price_changes.length > 0 || insights.availability.length > 0;
  if (!hasInsights) return null;

  return (
    <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mt-4">
      <div className="text-sm font-semibold text-amber-800 mb-3">Insights {title}</div>
      <div className="flex flex-wrap gap-2">
        {insights.price_changes.map((p) => (
          <span
            key={p.offer_id}
            className={`inline-flex items-center gap-1 text-xs font-medium px-3 py-1 rounded-full ${
              p.delta < 0
                ? "bg-green-100 text-green-800"
                : "bg-red-100 text-red-800"
            }`}
          >
            {p.delta < 0 ? "↓" : "↑"} {p.label} {Math.abs(p.pct_change)}%
            <span className="opacity-60">
              ({p.old_price.toFixed(0)} → {p.new_price.toFixed(0)} {p.currency})
            </span>
          </span>
        ))}
        {insights.availability.map((a) => (
          <span
            key={a.offer_id}
            className={`inline-flex items-center gap-1 text-xs font-medium px-3 py-1 rounded-full ${
              a.event === "disappeared"
                ? "bg-slate-100 text-slate-600"
                : "bg-blue-100 text-blue-800"
            }`}
          >
            {a.event === "disappeared" ? "✗ Indisponible" : "✓ Nouveau"} · {a.label}
          </span>
        ))}
      </div>
    </div>
  );
}
