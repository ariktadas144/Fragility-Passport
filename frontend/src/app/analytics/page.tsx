"use client";

import { useEffect, useMemo, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { api, type DashboardSummary } from "@/lib/api";

// Risk-level -> colour, so the severity pie reads at a glance.
const RISK_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];
const RISK_COLORS: Record<string, string> = {
  LOW: "#22c55e",
  MEDIUM: "#eab308",
  HIGH: "#f97316",
  CRITICAL: "#ef4444",
};

export default function Analytics() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .dashboardSummary()
      .then(setSummary)
      .catch((err) => setError(String(err)))
      .finally(() => setLoading(false));
  }, []);

  // Bar: incident count per dock (backend already aggregates this).
  const dockData = useMemo(() => {
    if (!summary) return [];
    return Object.entries(summary.events_by_dock)
      .map(([dock, incidents]) => ({ name: `Dock ${dock}`, incidents }))
      .sort((a, b) => b.incidents - a.incidents);
  }, [summary]);

  // Pie: how events break down by calibrated risk level.
  const riskData = useMemo(() => {
    if (!summary) return [];
    return Object.entries(summary.events_by_risk_level)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => RISK_ORDER.indexOf(a.name) - RISK_ORDER.indexOf(b.name));
  }, [summary]);

  return (
    <div className="flex flex-col gap-6 w-full max-w-7xl mx-auto">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-serif font-bold text-foreground tracking-tight">Analytics</h1>
        <p className="text-zinc-400">Aggregate patterns and operational insights. Data is strictly process-oriented, never individual.</p>
      </div>

      {error && <div className="text-sm text-red-500">Could not reach the backend ({error}).</div>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Incidents by Dock</CardTitle>
            <CardDescription>All processed events, grouped by dock</CardDescription>
          </CardHeader>
          <CardContent className="h-72">
            {loading ? (
              <div className="h-full flex items-center justify-center text-sm text-zinc-500">Loading…</div>
            ) : (
              <ResponsiveContainer width="100%" height={264}>
                <BarChart data={dockData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <XAxis dataKey="name" stroke="#52525b" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="#52525b" fontSize={12} tickLine={false} axisLine={false} allowDecimals={false} />
                  <Tooltip
                    cursor={{ fill: '#27272a' }}
                    contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', borderRadius: '8px' }}
                    itemStyle={{ color: '#e4e4e7' }}
                  />
                  <Bar dataKey="incidents" fill="#6366f1" radius={[4, 4, 0, 0]} isAnimationActive={false} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Incidents by Risk Level</CardTitle>
            <CardDescription>Severity distribution across all recorded events</CardDescription>
          </CardHeader>
          <CardContent className="h-72 flex flex-col items-center justify-center">
            {loading ? (
              <div className="text-sm text-zinc-500">Loading…</div>
            ) : (
              <>
                <ResponsiveContainer width="100%" height={210}>
                  <PieChart>
                    <Pie
                      data={riskData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={90}
                      paddingAngle={5}
                      dataKey="value"
                      stroke="none"
                      isAnimationActive={false}
                    >
                      {riskData.map((entry) => (
                        <Cell key={entry.name} fill={RISK_COLORS[entry.name] ?? "#6366f1"} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', borderRadius: '8px', color: '#e4e4e7' }}
                      itemStyle={{ color: '#e4e4e7' }}
                    />
                  </PieChart>
                </ResponsiveContainer>
                <div className="flex gap-4 mt-2 justify-center flex-wrap">
                  {riskData.map((entry) => (
                    <div key={entry.name} className="flex items-center gap-1.5 text-xs text-zinc-400">
                      <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: RISK_COLORS[entry.name] ?? "#6366f1" }} />
                      {entry.name} ({entry.value})
                    </div>
                  ))}
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
