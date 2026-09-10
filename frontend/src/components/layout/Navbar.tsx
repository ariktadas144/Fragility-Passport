import { Bell, Activity } from "lucide-react";

export default function Navbar() {
  return (
    <header className="sticky top-0 z-50 flex h-16 w-full items-center justify-between border-b border-border-subtle bg-background/80 backdrop-blur-md px-6">
      <div className="flex items-center gap-4">
        <h2 className="text-xl font-serif font-bold text-foreground">Overview</h2>
      </div>
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 px-3 py-1 bg-zinc-900 border border-zinc-800 rounded-full shadow-sm">
          <Activity className="h-4 w-4 text-accent-green animate-pulse" />
          <span className="text-xs font-semibold text-zinc-300 tracking-wide uppercase">System Live</span>
        </div>
        <button className="relative p-2 text-zinc-400 hover:text-foreground transition-colors duration-200 ease-out">
          <Bell className="h-5 w-5" />
          <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-red-500 border border-background" />
        </button>
      </div>
    </header>
  );
}
