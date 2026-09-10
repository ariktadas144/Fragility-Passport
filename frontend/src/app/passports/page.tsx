import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { FileText, Search } from "lucide-react";

export default function Passports() {
  return (
    <div className="flex flex-col gap-6 w-full max-w-7xl mx-auto">
      <div className="flex justify-between items-end">
        <div className="flex flex-col gap-2">
          <h1 className="text-3xl font-serif font-bold text-foreground tracking-tight">Fragility Passports</h1>
          <p className="text-zinc-400">Product-specific handling contracts and fragility rules.</p>
        </div>
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-zinc-500" />
          <input 
            type="text" 
            placeholder="Search SKU or Product..." 
            className="pl-9 pr-4 py-2 border border-border-subtle rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-accent-indigo bg-zinc-900 text-foreground"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[
          { sku: "ABC-123", name: "KD Panel", tilt: "40°", drop: "10 cm", orientation: "UPRIGHT", actions: ["NO DRAGGING", "NO THROWING"] },
          { sku: "XYZ-987", name: "Glass Table", tilt: "15°", drop: "0 cm", orientation: "UPRIGHT", actions: ["NO DRAGGING", "NO THROWING", "NO STACKING"] },
          { sku: "DEF-456", name: "Steel Pipes", tilt: "Any", drop: "50 cm", orientation: "ANY", actions: [] },
        ].map((passport) => (
          <Card key={passport.sku}>
            <CardHeader className="pb-3">
              <div className="flex justify-between items-start">
                <div className="flex items-center gap-2">
                  <div className="h-8 w-8 bg-indigo-500/10 rounded flex items-center justify-center">
                    <FileText className="h-4 w-4 text-accent-indigo" />
                  </div>
                  <div>
                    <CardTitle className="text-base">{passport.name}</CardTitle>
                    <CardDescription className="text-xs">SKU: {passport.sku}</CardDescription>
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-2 text-sm border-b border-border-subtle pb-3">
                  <div className="flex flex-col">
                    <span className="text-zinc-500 text-[10px] uppercase font-bold tracking-wider">Max Tilt</span>
                    <span className="font-semibold text-foreground">{passport.tilt}</span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-zinc-500 text-[10px] uppercase font-bold tracking-wider">Max Drop</span>
                    <span className="font-semibold text-foreground">{passport.drop}</span>
                  </div>
                  <div className="flex flex-col col-span-2 mt-1">
                    <span className="text-zinc-500 text-[10px] uppercase font-bold tracking-wider">Orientation</span>
                    <span className="font-semibold text-foreground">{passport.orientation}</span>
                  </div>
                </div>
                <div>
                  <span className="text-zinc-500 text-[10px] uppercase font-bold tracking-wider block mb-1.5">Strict Restrictions</span>
                  <div className="flex flex-wrap gap-1.5">
                    {passport.actions.length > 0 ? passport.actions.map(a => (
                      <Badge key={a} variant="outline" className="text-[10px] bg-zinc-900 border-zinc-700 text-zinc-300">{a}</Badge>
                    )) : <span className="text-xs text-zinc-500 italic">No special restrictions</span>}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
