"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Upload,
  FileText,
  Search,
  Zap,
  Menu,
  X,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/upload", label: "Upload", icon: Upload },
  { href: "/records", label: "Records", icon: FileText },
  { href: "/query", label: "Query", icon: Search },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  // Close mobile menu when route changes
  useEffect(() => {
    setIsMobileOpen(false);
  }, [pathname]);

  return (
    <div className="flex h-screen bg-zinc-950 overflow-hidden">
      {/* Mobile Overlay */}
      {isMobileOpen && (
        <div 
          className="fixed inset-0 bg-black/60 z-40 md:hidden"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside 
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex flex-col border-r border-zinc-800 bg-zinc-950 transition-all duration-300 md:relative",
          isMobileOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0",
          isCollapsed ? "w-20" : "w-64"
        )}
      >
        {/* Logo */}
        <div className="p-6 border-b border-zinc-800 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5 group overflow-hidden">
            <div className="w-9 h-9 shrink-0 rounded-lg bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-violet-500/20 group-hover:shadow-violet-500/40 transition-shadow duration-300">
              <Zap className="w-5 h-5 text-white" />
            </div>
            {!isCollapsed && (
              <div className="whitespace-nowrap transition-opacity duration-300">
                <span className="text-lg font-bold text-zinc-100">Finance</span>
                <span className="text-lg font-bold gradient-text">IQ</span>
              </div>
            )}
          </Link>
          {/* Mobile close button */}
          <Button 
            variant="ghost" 
            size="icon" 
            className="md:hidden shrink-0 text-zinc-400"
            onClick={() => setIsMobileOpen(false)}
          >
            <X className="w-5 h-5" />
          </Button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto overflow-x-hidden">
          {navItems.map((item) => {
            const isActive = pathname === item.href || 
              (item.href !== "/" && pathname.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                title={isCollapsed ? item.label : undefined}
                className={cn(
                  "flex items-center px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200",
                  isCollapsed ? "justify-center" : "gap-3",
                  isActive
                    ? "bg-violet-500/10 text-violet-400 shadow-inner"
                    : "text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/50"
                )}
              >
                <item.icon className={cn("shrink-0", isCollapsed ? "w-6 h-6" : "w-5 h-5", isActive && "text-violet-400")} />
                {!isCollapsed && <span className="whitespace-nowrap">{item.label}</span>}
              </Link>
            );
          })}
        </nav>

        {/* Footer & Collapse Toggle */}
        <div className="p-4 border-t border-zinc-800 flex flex-col gap-4">
          <Button
            variant="ghost"
            size="icon"
            className="hidden md:flex self-end text-zinc-400 hover:text-zinc-100"
            onClick={() => setIsCollapsed(!isCollapsed)}
          >
            {isCollapsed ? <ChevronRight className="w-5 h-5" /> : <ChevronLeft className="w-5 h-5" />}
          </Button>
          {!isCollapsed && (
            <div className="px-3 text-xs text-zinc-500 whitespace-nowrap hidden md:block">
              <p>FinanceIQ v1.0</p>
            </div>
          )}
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Mobile Header */}
        <header className="flex items-center gap-4 p-4 border-b border-zinc-800 bg-zinc-950 md:hidden shrink-0">
          <Button 
            variant="ghost" 
            size="icon" 
            className="text-zinc-400 hover:text-zinc-100"
            onClick={() => setIsMobileOpen(true)}
          >
            <Menu className="w-6 h-6" />
          </Button>
          <div className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-violet-500" />
            <span className="font-bold text-zinc-100">FinanceIQ</span>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-auto bg-zinc-950">
          <div className="p-4 md:p-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
