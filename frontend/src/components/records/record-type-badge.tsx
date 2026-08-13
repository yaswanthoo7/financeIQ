import React from "react";
import { getRecordTypeLabel, getRecordTypeIcon, getRecordTypeColor } from "@/lib/utils";
import { cn } from "@/lib/utils";

interface RecordTypeBadgeProps {
  type: string;
  className?: string;
  showLabel?: boolean;
}

export function RecordTypeBadge({ type, className, showLabel = true }: RecordTypeBadgeProps) {
  const colorClass = getRecordTypeColor(type);
  
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium border",
        colorClass,
        className
      )}
      title={!showLabel ? getRecordTypeLabel(type) : undefined}
    >
      <span className="text-[10px]">{getRecordTypeIcon(type)}</span>
      {showLabel && <span>{getRecordTypeLabel(type)}</span>}
    </span>
  );
}
