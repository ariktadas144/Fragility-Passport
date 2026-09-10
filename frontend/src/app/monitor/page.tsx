"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Video } from "lucide-react";
import { api, humanizeBehavior, type EventListItem } from "@/lib/api";

const RISK_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];

interface DockView {
  id: string;
  total: number;
  incidents: number; // HIGH or CRITICAL
  topEvent: EventListItem | null;
}

function buildDocks(events: EventListItem[]): DockView[] {
  const byDock = new Map<string, EventListItem[]>();
  for (const e of events) {
    const dock = e.dock ?? "unknown";
    if (!byDock.has(dock)) byDock.set(dock, []);
    byDock.get(dock)!.push(e);
  }
  return [...byDock.entries()]
    .map(([id, rows]) => {
      const sorted = [...rows].sort(
        (a, b) => RISK_ORDER.indexOf(b.risk_level) - RISK_ORDER.indexOf(a.risk_level) || b.risk_score - a.risk_score
      );
      return {
        id,
        total: rows.length,
        incidents: rows.filter((r) => r.risk_level === "HIGH" || r.risk_level === "CRITICAL").length,
        topEvent: sorted[0] ?? null,
      };
    })
    .sort((a, b) => b.incidents - a.incidents || b.total - a.total);
}

export default function LiveMonitor() {
  const [docks, setDocks] = useState<DockView[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .events()
      .then((events) => setDocks(buildDocks(events)))
      .catch((err) => setError(String(err)))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex flex-col gap-6 w-full max-w-7xl mx-auto h-full">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-serif font-bold text-foreground tracking-tight">Live Monitor</h1>
        <p className="text-slate-500">
          Per-dock incident status from processed footage. Video streaming is not wired up in this build.
        </p>
      </div>

      {error && <div className="text-sm text-red-500">Could not reach the backend ({error}).</div>}
      {loading && <div className="text-sm text-zinc-500">Loading…</div>}
      {!loading && !error && docks.length === 0 && (
        <div className="text-sm text-zinc-500">No docks have reported events yet.</div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 flex-1 min-h-[500px]">
        {docks.map((dock) => {
          const topBehavior = dock.topEvent?.behaviors[0];
          return (
            <Card key={dock.id} className="overflow-hidden flex flex-col">
              <CardHeader className="py-3 px-4 bg-slate-900 border-b-0">
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-2 text-white">
                    <Video className="h-4 w-4" />
                    <CardTitle className="text-sm font-sans tracking-widest text-slate-200">DOCK {dock.id}</CardTitle>
                  </div>
                  <div className="flex gap-2">
                    {dock.incidents > 0 && (
                      <Badge variant="destructive" className="animate-pulse">
                        {dock.incidents} INCIDENT{dock.incidents > 1 ? "S" : ""}
                      </Badge>
                    )}
                    <Badge variant="outline" className="text-slate-400 border-slate-600 bg-slate-800/40">
                      NO FEED
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="flex-1 bg-slate-950 p-4 min-h-[220px] flex flex-col items-center justify-center gap-3">
                <span className="text-slate-600 font-mono text-xs">[ no video feed in this build ]</span>
                {dock.topEvent && topBehavior ? (
                  <div className="text-center">
                    <div className="text-[10px] uppercase tracking-wider text-slate-500">Highest-risk event on this dock</div>
                    <div className="mt-1 text-sm font-semibold text-slate-200">
                      {dock.topEvent.public_id} · {humanizeBehavior(topBehavior)}
                    </div>
                    <div className="mt-1 text-xs text-slate-400">
                      {dock.topEvent.risk_level} · score {Math.round(dock.topEvent.risk_score)} · {dock.total} total event{dock.total > 1 ? "s" : ""}
                    </div>
                  </div>
                ) : (
                  <div className="text-xs text-slate-500">No events recorded</div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
