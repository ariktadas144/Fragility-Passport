"use client";

import { useRef, useState } from "react";
import { UploadCloud } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { API_BASE_URL } from "@/lib/api";

type Status = { kind: "idle" | "uploading" | "ok" | "error"; message?: string };

export default function UploadClip() {
  const fileRef = useRef<HTMLInputElement>(null);
  const [dock, setDock] = useState("");
  const [sku, setSku] = useState("");
  const [status, setStatus] = useState<Status>({ kind: "idle" });

  async function submit() {
    const file = fileRef.current?.files?.[0];
    if (!file) {
      setStatus({ kind: "error", message: "Choose a video file first." });
      return;
    }
    const form = new FormData();
    form.append("file", file);
    if (dock.trim()) form.append("dock", dock.trim());
    if (sku.trim()) form.append("product_sku", sku.trim());

    setStatus({ kind: "uploading", message: `Uploading ${file.name}…` });
    try {
      const res = await fetch(`${API_BASE_URL}/pipeline/upload`, { method: "POST", body: form });
      const body = await res.json();
      if (!res.ok) throw new Error(body.detail || `HTTP ${res.status}`);
      setStatus({
        kind: "ok",
        message: `Processing "${body.clip}" (job ${body.job_id}). New incidents appear on this page and Incidents in ~1–3 min — refresh then.`,
      });
      if (fileRef.current) fileRef.current.value = "";
    } catch (err) {
      setStatus({ kind: "error", message: String(err instanceof Error ? err.message : err) });
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <UploadCloud className="h-4 w-4" /> Upload a Clip
        </CardTitle>
        <CardDescription>Run a warehouse video through the detection + risk pipeline.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap items-center gap-3">
          <input
            ref={fileRef}
            type="file"
            accept="video/*"
            className="text-sm text-zinc-300 file:mr-3 file:rounded file:border-0 file:bg-zinc-800 file:px-3 file:py-1.5 file:text-zinc-200"
          />
          <input
            value={dock}
            onChange={(e) => setDock(e.target.value)}
            placeholder="Dock (e.g. 08)"
            className="w-28 rounded-md border border-border-subtle bg-zinc-900 px-3 py-1.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-accent-indigo"
          />
          <input
            value={sku}
            onChange={(e) => setSku(e.target.value)}
            placeholder="Product SKU (e.g. CARTON-001)"
            className="w-52 rounded-md border border-border-subtle bg-zinc-900 px-3 py-1.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-accent-indigo"
          />
          <button
            onClick={submit}
            disabled={status.kind === "uploading"}
            className="rounded-md bg-accent-indigo px-4 py-1.5 text-sm font-semibold text-white hover:bg-indigo-500 disabled:opacity-50"
          >
            {status.kind === "uploading" ? "Uploading…" : "Upload & Process"}
          </button>
        </div>
        {status.message && (
          <p
            className={`mt-3 text-xs ${
              status.kind === "error" ? "text-red-500" : status.kind === "ok" ? "text-accent-green" : "text-zinc-400"
            }`}
          >
            {status.message}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
