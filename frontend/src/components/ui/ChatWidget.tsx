"use client";

import { useState } from "react";
import { Bot, Send, X, MessageSquare } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { cn } from "@/lib/utils";

export default function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      {/* Floating Action Button */}
      <button
        onClick={() => setIsOpen(true)}
        className={cn(
          "fixed bottom-6 right-6 h-14 w-14 bg-accent-indigo text-white rounded-full flex items-center justify-center shadow-lg hover:bg-indigo-500 transition-all duration-300 z-50",
          isOpen ? "scale-0 opacity-0 pointer-events-none" : "scale-100 opacity-100"
        )}
      >
        <MessageSquare className="h-6 w-6" />
      </button>

      {/* Chat Window */}
      <div 
        className={cn(
          "fixed bottom-6 right-6 w-[380px] max-w-[calc(100vw-3rem)] h-[600px] max-h-[calc(100vh-6rem)] z-50 transition-all duration-300 origin-bottom-right",
          isOpen ? "scale-100 opacity-100" : "scale-95 opacity-0 pointer-events-none"
        )}
      >
        <Card className="h-full flex flex-col overflow-hidden border-border-subtle shadow-2xl bg-card-bg">
          <CardHeader className="border-b border-border-subtle bg-zinc-900/90 backdrop-blur-md pb-4 flex flex-row items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 bg-accent-indigo rounded-full flex items-center justify-center text-white shrink-0">
                <Bot className="h-5 w-5" />
              </div>
              <div className="flex flex-col">
                <CardTitle className="text-base m-0 leading-none">Operations Analyst</CardTitle>
                <CardDescription className="text-xs mt-1">Grounded in official incidents.</CardDescription>
              </div>
            </div>
            <button 
              onClick={() => setIsOpen(false)}
              className="text-zinc-500 hover:text-zinc-300 transition-colors p-1"
            >
              <X className="h-5 w-5" />
            </button>
          </CardHeader>
          
          <CardContent className="flex-1 overflow-y-auto p-4 space-y-4 bg-background">
            <div className="flex justify-start">
              <div className="bg-zinc-900 text-zinc-300 px-4 py-3 rounded-2xl max-w-[85%] rounded-tl-sm text-sm border border-zinc-800 shadow-sm">
                Hello. I am the intelligence assistant. You can ask me questions like:
                <ul className="list-disc pl-4 mt-2 space-y-1 text-zinc-400 font-medium text-xs">
                  <li>"Which dock had the most high-risk incidents today?"</li>
                  <li>"Show me all dropping violations for KD Panels."</li>
                  <li>"What is the required orientation for SKU ABC-123?"</li>
                </ul>
              </div>
            </div>
          </CardContent>
          
          <div className="p-3 bg-card-bg border-t border-border-subtle shrink-0">
            <div className="relative">
              <input 
                type="text" 
                placeholder="Ask about incidents..." 
                className="w-full pl-4 pr-12 py-2.5 border border-border-subtle rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-accent-indigo bg-zinc-900 text-foreground"
              />
              <button className="absolute right-1.5 top-1.5 h-7 w-7 bg-accent-indigo text-white rounded-full flex items-center justify-center hover:bg-indigo-500 transition-colors">
                <Send className="h-3 w-3 ml-0.5" />
              </button>
            </div>
          </div>
        </Card>
      </div>
    </>
  );
}
