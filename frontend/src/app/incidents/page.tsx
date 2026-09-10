import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { AlertTriangle, Filter } from "lucide-react";

export default function Incidents() {
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
          <div className="border border-border-subtle rounded-md overflow-hidden">
            <table className="w-full text-sm text-left">
              <thead className="text-xs uppercase bg-zinc-900 border-b border-border-subtle text-zinc-400">
                <tr>
                  <th className="px-4 py-3 font-semibold">Incident ID</th>
                  <th className="px-4 py-3 font-semibold">Dock</th>
                  <th className="px-4 py-3 font-semibold">Product</th>
                  <th className="px-4 py-3 font-semibold">Behavior</th>
                  <th className="px-4 py-3 font-semibold">Risk Level</th>
                  <th className="px-4 py-3 font-semibold">Time</th>
                  <th className="px-4 py-3 text-right font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle">
                {[
                  { id: "EVT-0042", dock: "D07", product: "KD Panel", behavior: "Throwing", risk: "HIGH", time: "14:32:18" },
                  { id: "EVT-0041", dock: "D09", product: "Glass Table", behavior: "Dragging", risk: "CRITICAL", time: "14:20:05" },
                  { id: "EVT-0038", dock: "D02", product: "Ceramic Vase", behavior: "Stacking Limit", risk: "HIGH", time: "13:45:11" },
                ].map((item) => (
                  <tr key={item.id} className="hover:bg-zinc-900 transition-colors">
                    <td className="px-4 py-3 font-medium text-foreground">{item.id}</td>
                    <td className="px-4 py-3 text-zinc-400">{item.dock}</td>
                    <td className="px-4 py-3 text-zinc-400">{item.product}</td>
                    <td className="px-4 py-3 text-zinc-400">{item.behavior}</td>
                    <td className="px-4 py-3">
                      <Badge variant={item.risk === "CRITICAL" ? "critical" : "high"}>{item.risk}</Badge>
                    </td>
                    <td className="px-4 py-3 text-zinc-500 text-xs">{item.time}</td>
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
