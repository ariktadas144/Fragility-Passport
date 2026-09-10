"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { AlertTriangle, PackageOpen, Settings, CheckCircle2, TrendingUp, Activity } from "lucide-react";
import {
  api,
  formatInr,
  humanizeBehavior,
  riskBadgeVariant,
  type DashboardSummary,
  type EventListItem,
} from "@/lib/api";

export default function Dashboard() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [events, setEvents] = useState<EventListItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.dashboardSummary(), api.events()])
      .then(([s, e]) => {
        setSummary(s);
        setEvents(e);
      })
      .catch((err) => setError(String(err)))
      .finally(() => setLoading(false));
  }, []);

  const riskCount = (level: string) => summary?.events_by_risk_level?.[level] ?? 0;
  const activeDocks = summary ? Object.keys(summary.events_by_dock).length : 0;

  const recentIncidents = [...events]
    .filter((e) => e.risk_level === "HIGH" || e.risk_level === "CRITICAL")
    .sort((a, b) => b.id - a.id)
    .slice(0, 5);

  return (
    <div className="flex flex-col gap-6 w-full max-w-7xl mx-auto">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-serif font-bold text-foreground tracking-tight">Intelligence Dashboard</h1>
        <p className="text-zinc-400">Real-time overview of warehouse operations and handling risks.</p>
      </div>

      {error && (
        <Card>
          <CardContent className="pt-6 text-sm text-red-500">
            Could not reach the backend ({error}). Start it with{" "}
            <code className="text-zinc-300">cd backend &amp;&amp; uvicorn app.main:app</code>.
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Stat Cards */}
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Incidents</CardDescription>
            <CardTitle className="text-3xl font-sans font-bold">{loading ? "—" : summary?.total_events ?? 0}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xs text-zinc-400 flex items-center gap-1">
              <TrendingUp className="h-3 w-3 text-accent-green" /> Across all processed clips
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>High Risk Events</CardDescription>
            <CardTitle className="text-3xl font-sans font-bold text-orange-600">{loading ? "—" : riskCount("HIGH")}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xs text-zinc-400">Requires review</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Critical Violations</CardDescription>
            <CardTitle className="text-3xl font-sans font-bold text-red-600">{loading ? "—" : riskCount("CRITICAL")}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xs text-red-500 font-semibold">Immediate action required</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Active Docks</CardDescription>
            <CardTitle className="text-3xl font-sans font-bold text-zinc-200">{loading ? "—" : activeDocks}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xs text-zinc-400 flex items-center gap-1">
              <CheckCircle2 className="h-3 w-3 text-accent-green" /> Reporting incidents
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Recent Critical Incidents</CardTitle>
            <CardDescription>Latest handling violations requiring supervisor attention</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {loading && <div className="text-sm text-zinc-500">Loading…</div>}
              {!loading && recentIncidents.length === 0 && (
                <div className="text-sm text-zinc-500">No high-risk incidents yet.</div>
              )}
              {recentIncidents.map((incident) => (
                <div key={incident.id} className="flex items-center justify-between p-3 rounded-lg border border-border-subtle hover:bg-zinc-900 transition-colors">
                  <div className="flex items-center gap-4">
                    <div className="h-10 w-10 rounded bg-red-500/10 flex items-center justify-center border border-red-500/20">
                      <AlertTriangle className="h-5 w-5 text-red-500" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-sm text-foreground">{incident.public_id}</span>
                        <span className="text-xs font-medium text-zinc-500">Dock {incident.dock ?? "—"}</span>
                      </div>
                      <div className="text-sm text-zinc-400">
                        {incident.behaviors.map(humanizeBehavior).join(", ") || "—"}
                      </div>
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <Badge variant={riskBadgeVariant(incident.risk_level)}>{incident.risk_level}</Badge>
                    <span className="text-xs text-zinc-500">Score {Math.round(incident.risk_score)}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>System Telemetry</CardTitle>
            <CardDescription>Live pipeline status</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col gap-4">
              <div className="flex justify-between items-center pb-3 border-b border-border-subtle">
                <div className="flex items-center gap-2 text-sm text-zinc-400">
                  <PackageOpen className="h-4 w-4" /> Estimated Exposure
                </div>
                <span className="font-mono text-sm font-semibold">
                  {loading ? "—" : formatInr(summary?.total_estimated_exposure_inr)}
                </span>
              </div>
              <div className="flex justify-between items-center pb-3 border-b border-border-subtle">
                <div className="flex items-center gap-2 text-sm text-zinc-400">
                  <Settings className="h-4 w-4" /> Active Alerts
                </div>
                <span className="font-mono text-sm font-semibold text-accent-green">
                  {loading ? "—" : summary?.active_alerts ?? 0}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-2 text-sm text-zinc-400">
                  <Activity className="h-4 w-4" /> Escalated Alerts
                </div>
                <span className="font-mono text-sm font-semibold">
                  {loading ? "—" : summary?.escalated_alerts ?? 0}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
