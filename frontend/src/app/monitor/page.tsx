import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Video } from "lucide-react";

export default function LiveMonitor() {
  return (
    <div className="flex flex-col gap-6 w-full max-w-7xl mx-auto h-full">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-serif font-bold text-foreground tracking-tight">Live Monitor</h1>
        <p className="text-slate-500">Real-time video feeds with active tracking and behavior detection.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 flex-1 min-h-[500px]">
        {[
          { id: "D07", status: "LIVE", incidents: 2 },
          { id: "D09", status: "LIVE", incidents: 0 },
        ].map((dock) => (
          <Card key={dock.id} className="overflow-hidden flex flex-col">
            <CardHeader className="py-3 px-4 bg-slate-900 border-b-0">
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-2 text-white">
                  <Video className="h-4 w-4" />
                  <CardTitle className="text-sm font-sans tracking-widest text-slate-200">DOCK {dock.id}</CardTitle>
                </div>
                <div className="flex gap-2">
                  {dock.incidents > 0 && <Badge variant="destructive" className="animate-pulse">INCIDENT DETECTED</Badge>}
                  <Badge variant="outline" className="text-green-400 border-green-400/30 bg-green-400/10"><span className="h-1.5 w-1.5 rounded-full bg-green-400 mr-1.5 animate-pulse"></span>LIVE</Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent className="flex-1 bg-slate-950 p-0 relative min-h-[300px] flex items-center justify-center">
              <span className="text-slate-600 font-mono text-sm">[ Live Video Stream ]</span>
              
              {/* Simulated Detection Box overlay */}
              {dock.incidents > 0 && (
                <div className="absolute top-1/2 left-1/3 w-32 h-32 border-2 border-red-500 bg-red-500/10">
                  <div className="bg-red-500 text-white text-[10px] font-bold px-1 py-0.5 absolute -top-5 left-[-2px]">
                    THROWING 89%
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
