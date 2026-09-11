"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Filter } from "lucide-react";
import {
  api,
  formatInr,
  humanizeBehavior,
  riskBadgeVariant,
  type EventRead,
} from "@/lib/api";

function formatClock(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? "—" : d.toLocaleTimeString();
}

export default function Incidents() {
  const [events, setEvents] = useState<EventRead[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .eventsDetailed()
      .then((rows) => setEvents(rows.sort((a, b) => b.id - a.id)))
      .catch((err) => setError(String(err)))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex flex-col gap-6 w-full max-w-7xl mx-auto">
      <div className="flex justify-between items-end">
        <div className="flex flex-col gap-2">
          <h1 className="text-3xl font-serif font-bold text-foreground tracking-tight">Incidents</h1>
          <p className="text-zinc-400">Review and acknowledge handling contract violations.</p>
        </div>
        <button className="flex items-center gap-2 px-3 py-1.5 text-sm font-semibold border border-border-subtle rounded bg-card-bg hover:bg-zinc-900 transition-colors text-foreground">
          <Filter className="h-4 w-4" /> Filter
        </button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Open Incidents</CardTitle>
          <CardDescription>All unresolved risk events across docks</CardDescription>
        </CardHeader>
        <CardContent>
          {error && (
            <div className="text-sm text-red-500 mb-3">
              Could not reach the backend ({error}).
            </div>
          )}
          <div className="border border-border-subtle rounded-md overflow-hidden">
            <table className="w-full text-sm text-left">
              <thead className="text-xs uppercase bg-zinc-900 border-b border-border-subtle text-zinc-400">
                <tr>
                  <th className="px-4 py-3 font-semibold">Incident ID</th>
                  <th className="px-4 py-3 font-semibold">Dock</th>
                  <th className="px-4 py-3 font-semibold">Product</th>
                  <th className="px-4 py-3 font-semibold">Behavior</th>
                  <th className="px-4 py-3 font-semibold">Risk Level</th>
                  <th className="px-4 py-3 font-semibold">Exposure</th>
                  <th className="px-4 py-3 font-semibold">Time</th>
                  <th className="px-4 py-3 text-right font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle">
                {loading && (
                  <tr>
                    <td colSpan={8} className="px-4 py-6 text-center text-zinc-500">Loading…</td>
                  </tr>
                )}
                {!loading && events.length === 0 && !error && (
                  <tr>
                    <td colSpan={8} className="px-4 py-6 text-center text-zinc-500">No incidents recorded yet.</td>
                  </tr>
                )}
                {events.map((item) => (
                  <tr key={item.id} className="hover:bg-zinc-900 transition-colors align-top">
                    <td className="px-4 py-3 font-medium text-foreground">{item.public_id}</td>
                    <td className="px-4 py-3 text-zinc-400">{item.dock ?? "—"}</td>
                    <td className="px-4 py-3 text-zinc-400">
                      {item.product ? `${item.product.name}` : "—"}
                      {item.product && (
                        <span className="block text-xs text-zinc-600">{item.product.sku}</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-zinc-400">
                      {item.behaviors.map(humanizeBehavior).join(", ") || "—"}
                      {item.contract_clause_violated && (
                        <span className="block text-xs text-red-500 mt-1">
                          {item.contract_clause_violated}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={riskBadgeVariant(item.risk_level)}>{item.risk_level}</Badge>
                    </td>
                    <td className="px-4 py-3 text-zinc-300 font-mono text-xs">
                      {formatInr(item.estimated_exposure_inr)}
                    </td>
                    <td className="px-4 py-3 text-zinc-500 text-xs">{formatClock(item.created_at)}</td>
                    <td className="px-4 py-3 text-right">
                      <button className="text-accent-indigo hover:underline font-semibold text-xs">Review</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
