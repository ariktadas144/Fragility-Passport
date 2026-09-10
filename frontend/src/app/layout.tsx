import type { Metadata } from "next";
import { Inter, Playfair_Display } from "next/font/google";
import "./globals.css";

import Navbar from "@/components/layout/Navbar";
import Sidebar from "@/components/layout/Sidebar";
import ChatWidget from "@/components/ui/ChatWidget";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const playfair = Playfair_Display({
  variable: "--font-playfair",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Fragility Passport",
  description: "AI-Powered Warehouse Video Intelligence System",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} ${playfair.variable} antialiased tracking-tight h-full`}>
      <body className="flex h-full flex-col md:flex-row bg-background text-foreground overflow-hidden">
        <Sidebar />
        <div className="flex flex-col flex-1 overflow-hidden relative">
          <Navbar />
          <main className="flex-1 overflow-y-auto p-4 md:p-8">
            {children}
          </main>
        </div>
        <ChatWidget />
      </body>
    </html>
  );
}
