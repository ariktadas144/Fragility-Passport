"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { LayoutDashboard, Video, AlertTriangle, FileText, BarChart3, Bot } from "lucide-react";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/monitor", label: "Live Monitor", icon: Video },
  { href: "/incidents", label: "Incidents", icon: AlertTriangle },
  { href: "/passports", label: "Passports", icon: FileText },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 flex-shrink-0 border-r border-border-subtle bg-background flex flex-col hidden md:flex">
      <div className="h-16 flex items-center px-6 border-b border-border-subtle">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 bg-accent-indigo rounded-md flex items-center justify-center">
            <span className="text-white font-bold font-serif text-lg">F</span>
          </div>
          <div className="flex flex-col">
            <span className="font-bold text-foreground leading-tight tracking-tight">Fragility Passport</span>
            <span className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold">Intelligence</span>
          </div>
        </div>
      </div>
      
      <div className="flex-1 py-6 px-4 flex flex-col gap-1 overflow-y-auto">
        <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 px-2">Navigation</div>
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-all duration-200 ease-out",
                isActive
                  ? "bg-indigo-500/10 text-accent-indigo"
                  : "text-zinc-400 hover:bg-zinc-800/50 hover:text-foreground"
              )}
            >
              <item.icon className={cn("h-4 w-4", isActive ? "text-accent-indigo" : "text-zinc-500")} />
              {item.label}
            </Link>
          );
        })}
      </div>
      
      <div className="p-4 border-t border-border-subtle">
        <div className="flex items-center gap-3 px-3 py-2 rounded-md bg-zinc-900 border border-zinc-800">
          <div className="h-8 w-8 rounded-full bg-indigo-500/20 flex items-center justify-center text-accent-indigo font-bold text-sm">
            SU
          </div>
          <div className="flex flex-col">
            <span className="text-xs font-bold text-foreground">Supervisor</span>
            <span className="text-[10px] text-zinc-500">Bhiwandi DC</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
