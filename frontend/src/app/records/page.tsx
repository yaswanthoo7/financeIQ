"use client";

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { AppShell } from "@/components/layout/app-shell";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, type RecordListItem, type Category } from "@/lib/api";
import { formatCurrency, formatDate, getStatusColor } from "@/lib/utils";
import { CategoryBadge } from "@/components/records/category-badge";
import { RecordTypeBadge } from "@/components/records/record-type-badge";
import {
  FileText,
  Search,
  Filter,
  ChevronLeft,
  ChevronRight,
  ArrowUpDown,
  Upload,
  MoreHorizontal,
} from "lucide-react";

export default function RecordsPage() {
  const [records, setRecords] = useState<RecordListItem[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Pagination & Filtering
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalRecords, setTotalRecords] = useState(0);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [sortBy, setSortBy] = useState("created_at");
  const [sortOrder, setSortOrder] = useState("desc");

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      
      // Load categories once
      if (categories.length === 0) {
        const cats = await api.listCategories();
        setCategories(cats);
      }
      
      const response = await api.listRecords({
        page,
        page_size: 15,
        vendor_name: searchQuery || undefined,
        status: statusFilter !== "all" ? statusFilter : undefined,
        record_type: typeFilter !== "all" ? typeFilter : undefined,
        category_id: categoryFilter !== "all" ? categoryFilter : undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
      });

      setRecords(response.items);
      setTotalPages(response.total_pages);
      setTotalRecords(response.total);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [page, searchQuery, statusFilter, typeFilter, categoryFilter, sortBy, sortOrder, categories.length]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const toggleSort = (column: string) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortBy(column);
      setSortOrder("desc");
    }
    setPage(1);
  };

  const renderSortIcon = (column: string) => {
    if (sortBy !== column) return <ArrowUpDown className="w-3 h-3 ml-1 opacity-50" />;
    return (
      <ArrowUpDown
        className={`w-3 h-3 ml-1 ${sortOrder === "asc" ? "rotate-180" : ""}`}
      />
    );
  };

  return (
    <AppShell>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">Financial Records</h1>
          <p className="text-zinc-400 mt-1">
            {totalRecords} {totalRecords === 1 ? "record" : "records"} total
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/upload">
            <Button className="gap-2">
              <Upload className="w-4 h-4" />
              Upload
            </Button>
          </Link>
        </div>
      </div>

      <Card className="mb-8">
        {/* Filters */}
        <div className="p-4 border-b border-zinc-800/50 flex flex-col sm:flex-row gap-4 bg-zinc-900/50">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
            <Input
              placeholder="Search by vendor or merchant..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setPage(1);
              }}
              className="pl-9 bg-zinc-950 border-zinc-800"
            />
          </div>
          
          <div className="flex gap-3 overflow-x-auto pb-1 sm:pb-0 scrollbar-hide">
            {/* Category Filter */}
            <select
              className="h-10 px-3 rounded-md bg-zinc-950 border border-zinc-800 text-sm text-zinc-300 focus:outline-none focus:ring-2 focus:ring-violet-500/50"
              value={categoryFilter}
              onChange={(e) => {
                setCategoryFilter(e.target.value);
                setPage(1);
              }}
            >
              <option value="all">All Categories</option>
              {categories.map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
            
            {/* Type Filter */}
            <select
              className="h-10 px-3 rounded-md bg-zinc-950 border border-zinc-800 text-sm text-zinc-300 focus:outline-none focus:ring-2 focus:ring-violet-500/50"
              value={typeFilter}
              onChange={(e) => {
                setTypeFilter(e.target.value);
                setPage(1);
              }}
            >
              <option value="all">All Types</option>
              <option value="invoice">Invoices</option>
              <option value="receipt">Receipts</option>
              <option value="purchase_order">Purchase Orders</option>
              <option value="expense_report">Expense Reports</option>
            </select>

            {/* Status Filter */}
            <select
              className="h-10 px-3 rounded-md bg-zinc-950 border border-zinc-800 text-sm text-zinc-300 focus:outline-none focus:ring-2 focus:ring-violet-500/50"
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
            >
              <option value="all">All Statuses</option>
              <option value="completed">Completed</option>
              <option value="needs_review">Needs Review</option>
              <option value="processing">Processing</option>
              <option value="failed">Failed</option>
            </select>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-zinc-400 uppercase bg-zinc-900/50 border-b border-zinc-800">
              <tr>
                <th className="px-6 py-4 font-medium">Record Details</th>
                <th
                  className="px-6 py-4 font-medium cursor-pointer hover:text-zinc-200"
                  onClick={() => toggleSort("record_date")}
                >
                  <div className="flex items-center">
                    Date {renderSortIcon("record_date")}
                  </div>
                </th>
                <th className="px-6 py-4 font-medium">Category / Type</th>
                <th
                  className="px-6 py-4 font-medium cursor-pointer hover:text-zinc-200"
                  onClick={() => toggleSort("total_amount")}
                >
                  <div className="flex items-center">
                    Amount {renderSortIcon("total_amount")}
                  </div>
                </th>
                <th className="px-6 py-4 font-medium">Status</th>
                <th className="px-6 py-4 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/50">
              {loading ? (
                [...Array(5)].map((_, i) => (
                  <tr key={i}>
                    <td colSpan={6} className="px-6 py-4">
                      <div className="h-12 skeleton rounded-md w-full" />
                    </td>
                  </tr>
                ))
              ) : records.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-zinc-500">
                    <div className="flex flex-col items-center justify-center">
                      <FileText className="w-8 h-8 mb-3 opacity-20" />
                      <p>No records found matching your filters.</p>
                      {(searchQuery || statusFilter !== "all" || typeFilter !== "all" || categoryFilter !== "all") && (
                        <Button
                          variant="link"
                          onClick={() => {
                            setSearchQuery("");
                            setStatusFilter("all");
                            setTypeFilter("all");
                            setCategoryFilter("all");
                          }}
                          className="mt-2 text-violet-400"
                        >
                          Clear filters
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ) : (
                records.map((record) => (
                  <tr
                    key={record.id}
                    className="hover:bg-zinc-800/30 transition-colors group"
                  >
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div>
                          <Link
                            href={`/records/${record.id}`}
                            className="font-medium text-zinc-200 hover:text-violet-400 transition-colors"
                          >
                            {record.vendor_name || record.original_filename}
                          </Link>
                          <div className="text-xs text-zinc-500 mt-0.5">
                            {record.line_item_count} items
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-zinc-300">
                      {formatDate(record.record_date || record.created_at)}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-col gap-1.5 items-start">
                        {record.category && (
                          <CategoryBadge category={record.category} />
                        )}
                        <RecordTypeBadge type={record.record_type} showLabel={true} />
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap font-medium text-zinc-200">
                      {formatCurrency(record.total_amount, record.currency)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Badge
                        variant={
                          record.status === "completed"
                            ? "success"
                            : record.status === "processing"
                            ? "default"
                            : record.status === "needs_review"
                            ? "warning"
                            : "destructive"
                        }
                      >
                        {record.status.replace("_", " ")}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link href={`/records/${record.id}`}>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="opacity-100 lg:opacity-0 lg:group-hover:opacity-100 transition-opacity"
                        >
                          Review
                        </Button>
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {!loading && totalPages > 1 && (
          <div className="p-4 border-t border-zinc-800/50 flex items-center justify-between">
            <p className="text-sm text-zinc-500">
              Showing {(page - 1) * 15 + 1} to{" "}
              {Math.min(page * 15, totalRecords)} of {totalRecords} records
            </p>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                <ChevronLeft className="w-4 h-4 mr-1" />
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
              >
                Next
                <ChevronRight className="w-4 h-4 ml-1" />
              </Button>
            </div>
          </div>
        )}
      </Card>
    </AppShell>
  );
}
