import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { AlertTriangle, PackageOpen, Settings, CheckCircle2, TrendingUp, Activity } from "lucide-react";

export default function Dashboard() {
  return (
    <div className="flex flex-col gap-6 w-full max-w-7xl mx-auto">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-serif font-bold text-foreground tracking-tight">Intelligence Dashboard</h1>
        <p className="text-zinc-400">Real-time overview of warehouse operations and handling risks.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Stat Cards */}
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Incidents</CardDescription>
            <CardTitle className="text-3xl font-sans font-bold">47</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xs text-zinc-400 flex items-center gap-1">
              <TrendingUp className="h-3 w-3 text-accent-green" /> +12% from yesterday
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>High Risk Events</CardDescription>
            <CardTitle className="text-3xl font-sans font-bold text-orange-600">12</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xs text-zinc-400">Requires review</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Critical Violations</CardDescription>
            <CardTitle className="text-3xl font-sans font-bold text-red-600">4</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xs text-red-500 font-semibold">Immediate action required</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Active Docks</CardDescription>
            <CardTitle className="text-3xl font-sans font-bold text-zinc-200">5</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xs text-zinc-400 flex items-center gap-1">
              <CheckCircle2 className="h-3 w-3 text-accent-green" /> All cameras online
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
              {/* Incident Rows */}
              {[
                { id: "EVT-0042", dock: "D07", behavior: "Throwing", product: "KD Panel", risk: "HIGH", time: "2 mins ago" },
                { id: "EVT-0041", dock: "D09", behavior: "Dragging", product: "Glass Table", risk: "CRITICAL", time: "14 mins ago" },
                { id: "EVT-0038", dock: "D02", behavior: "Stacking Limit", product: "Ceramic Vase", risk: "HIGH", time: "1 hour ago" },
              ].map((incident) => (
                <div key={incident.id} className="flex items-center justify-between p-3 rounded-lg border border-border-subtle hover:bg-zinc-900 transition-colors">
                  <div className="flex items-center gap-4">
                    <div className="h-10 w-10 rounded bg-red-500/10 flex items-center justify-center border border-red-500/20">
                      <AlertTriangle className="h-5 w-5 text-red-500" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-sm text-foreground">{incident.id}</span>
                        <span className="text-xs font-medium text-zinc-500">Dock {incident.dock}</span>
                      </div>
                      <div className="text-sm text-zinc-400">{incident.behavior} • {incident.product}</div>
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <Badge variant={incident.risk === "CRITICAL" ? "critical" : "high"}>{incident.risk}</Badge>
                    <span className="text-xs text-zinc-500">{incident.time}</span>
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
                  <PackageOpen className="h-4 w-4" /> Passports Synced
                </div>
                <span className="font-mono text-sm font-semibold">1,204</span>
              </div>
              <div className="flex justify-between items-center pb-3 border-b border-border-subtle">
                <div className="flex items-center gap-2 text-sm text-zinc-400">
                  <Settings className="h-4 w-4" /> Inference Latency
                </div>
                <span className="font-mono text-sm font-semibold text-accent-green">42ms</span>
              </div>
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-2 text-sm text-zinc-400">
                  <Activity className="h-4 w-4" /> Frames Processed
                </div>
                <span className="font-mono text-sm font-semibold">24.5k/hr</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
