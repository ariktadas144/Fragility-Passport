"use client";

import { useEffect, useMemo, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { FileText, Search } from "lucide-react";
import { api, type FragilityPassportRead, type ProductRead } from "@/lib/api";

interface PassportView extends ProductRead {
  passport: FragilityPassportRead | null;
}

function restrictions(p: FragilityPassportRead | null): string[] {
  if (!p) return [];
  const out: string[] = [];
  if (!p.drag_allowed) out.push("NO DRAGGING");
  if (!p.throw_allowed) out.push("NO THROWING");
  if (p.max_stack_weight_kg === 0) out.push("NO STACKING");
  return out;
}

export default function Passports() {
  const [rows, setRows] = useState<PassportView[]>([]);
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .products()
      .then(async (products) => {
        const withPassports = await Promise.all(
          products.map(async (product) => {
            let passport: FragilityPassportRead | null = null;
            try {
              passport = await api.passportForProduct(product.id);
            } catch {
              passport = null; // product without a registered passport
            }
            return { ...product, passport };
          })
        );
        setRows(withPassports);
      })
      .catch((err) => setError(String(err)))
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return rows;
    return rows.filter(
      (r) => r.sku.toLowerCase().includes(q) || r.name.toLowerCase().includes(q)
    );
  }, [rows, query]);

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
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search SKU or Product..."
            className="pl-9 pr-4 py-2 border border-border-subtle rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-accent-indigo bg-zinc-900 text-foreground"
          />
        </div>
      </div>

      {error && <div className="text-sm text-red-500">Could not reach the backend ({error}).</div>}
      {loading && <div className="text-sm text-zinc-500">Loading…</div>}
      {!loading && !error && filtered.length === 0 && (
        <div className="text-sm text-zinc-500">No products match.</div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filtered.map((row) => {
          const p = row.passport;
          const actions = restrictions(p);
          return (
            <Card key={row.sku}>
              <CardHeader className="pb-3">
                <div className="flex justify-between items-start">
                  <div className="flex items-center gap-2">
                    <div className="h-8 w-8 bg-indigo-500/10 rounded flex items-center justify-center">
                      <FileText className="h-4 w-4 text-accent-indigo" />
                    </div>
                    <div>
                      <CardTitle className="text-base">{row.name}</CardTitle>
                      <CardDescription className="text-xs">SKU: {row.sku}</CardDescription>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-2 text-sm border-b border-border-subtle pb-3">
                    <div className="flex flex-col">
                      <span className="text-zinc-500 text-[10px] uppercase font-bold tracking-wider">Max Tilt</span>
                      <span className="font-semibold text-foreground">{p ? `${p.max_tilt_deg}°` : "—"}</span>
                    </div>
                    <div className="flex flex-col">
                      <span className="text-zinc-500 text-[10px] uppercase font-bold tracking-wider">Max Drop</span>
                      <span className="font-semibold text-foreground">{p ? `${p.max_drop_height_cm} cm` : "—"}</span>
                    </div>
                    <div className="flex flex-col">
                      <span className="text-zinc-500 text-[10px] uppercase font-bold tracking-wider">Orientation</span>
                      <span className="font-semibold text-foreground">{p ? p.required_orientation : "—"}</span>
                    </div>
                    <div className="flex flex-col">
                      <span className="text-zinc-500 text-[10px] uppercase font-bold tracking-wider">Declared Value</span>
                      <span className="font-semibold text-foreground">
                        ₹{Math.round(row.declared_value_inr).toLocaleString("en-IN")}
                      </span>
                    </div>
                  </div>
                  <div>
                    <span className="text-zinc-500 text-[10px] uppercase font-bold tracking-wider block mb-1.5">Strict Restrictions</span>
                    <div className="flex flex-wrap gap-1.5">
                      {actions.length > 0 ? (
                        actions.map((a) => (
                          <Badge key={a} variant="outline" className="text-[10px] bg-zinc-900 border-zinc-700 text-zinc-300">{a}</Badge>
                        ))
                      ) : (
                        <span className="text-xs text-zinc-500 italic">
                          {p ? "No special restrictions" : "No passport registered"}
                        </span>
                      )}
                    </div>
                  </div>
                  {p?.notes && <p className="text-xs text-zinc-500 pt-1">{p.notes}</p>}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
