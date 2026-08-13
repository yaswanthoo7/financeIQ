import React from "react";
import { type Category } from "@/lib/api";
import { cn } from "@/lib/utils";

interface CategoryBadgeProps {
  category: Category | null;
  className?: string;
}

export function CategoryBadge({ category, className }: CategoryBadgeProps) {
  if (!category) return null;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium border transition-colors",
        className
      )}
      style={{
        backgroundColor: `${category.color || "#a1a1aa"}15`,
        borderColor: `${category.color || "#a1a1aa"}30`,
        color: category.color || "#e4e4e7",
      }}
    >
      {category.icon && <span className="text-[10px]">{category.icon}</span>}
      <span>{category.name}</span>
    </span>
  );
}
