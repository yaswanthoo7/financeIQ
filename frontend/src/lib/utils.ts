import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(amount: number | null, currency: string | null = "USD"): string {
  if (amount === null || amount === undefined) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: currency || "USD",
    minimumFractionDigits: 2,
  }).format(amount);
}

export function formatDate(dateStr: string | null): string {
  if (!dateStr) return "—";
  try {
    return new Intl.DateTimeFormat("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    }).format(new Date(dateStr));
  } catch {
    return dateStr;
  }
}

export function getStatusColor(status: string): string {
  switch (status) {
    case "completed":
      return "text-emerald-400 bg-emerald-400/10 border-emerald-400/20";
    case "processing":
      return "text-blue-400 bg-blue-400/10 border-blue-400/20";
    case "needs_review":
      return "text-amber-400 bg-amber-400/10 border-amber-400/20";
    case "failed":
      return "text-red-400 bg-red-400/10 border-red-400/20";
    default:
      return "text-zinc-400 bg-zinc-400/10 border-zinc-400/20";
  }
}

export function getConfidenceColor(score: number | null): string {
  if (score === null) return "text-zinc-500";
  if (score >= 0.8) return "text-emerald-400";
  if (score >= 0.6) return "text-amber-400";
  return "text-red-400";
}

export function formatFileSize(bytes: number | null): string {
  if (!bytes) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// ──── Record Type Helpers ────

export const RECORD_TYPE_CONFIG: Record<string, { label: string; icon: string; color: string }> = {
  invoice: { label: "Invoice", icon: "📄", color: "text-blue-400 bg-blue-400/10 border-blue-400/20" },
  receipt: { label: "Receipt", icon: "🧾", color: "text-emerald-400 bg-emerald-400/10 border-emerald-400/20" },
  purchase_order: { label: "Purchase Order", icon: "📋", color: "text-purple-400 bg-purple-400/10 border-purple-400/20" },
  expense_report: { label: "Expense Report", icon: "💰", color: "text-amber-400 bg-amber-400/10 border-amber-400/20" },
};

export function getRecordTypeLabel(type: string): string {
  return RECORD_TYPE_CONFIG[type]?.label || type;
}

export function getRecordTypeIcon(type: string): string {
  return RECORD_TYPE_CONFIG[type]?.icon || "📄";
}

export function getRecordTypeColor(type: string): string {
  return RECORD_TYPE_CONFIG[type]?.color || "text-zinc-400 bg-zinc-400/10 border-zinc-400/20";
}

export function formatStatusLabel(status: string): string {
  switch (status) {
    case "completed": return "Completed";
    case "processing": return "Processing";
    case "needs_review": return "Needs Review";
    case "failed": return "Failed";
    default: return status;
  }
}
