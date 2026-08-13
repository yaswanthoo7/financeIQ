"use client";

import React, { useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/layout/app-shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { api, type QueryResponse, type RecordListItem } from "@/lib/api";
import { formatCurrency, formatDate, getRecordTypeIcon } from "@/lib/utils";
import { CategoryBadge } from "@/components/records/category-badge";
import { RecordTypeBadge } from "@/components/records/record-type-badge";
import {
  Search,
  Sparkles,
  FileText,
  Loader2,
  ArrowRight,
  Lightbulb,
  Download,
} from "lucide-react";

const EXAMPLE_QUERIES = [
  "Show me all records from last month",
  "Software subscriptions over $500",
  "Find receipts from Uber",
  "All pending purchase orders",
  "Travel expenses between $100 and $1000",
];

export default function QueryPage() {
  const [queryText, setQueryText] = useState("");
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleQuery(q?: string) {
    const query = q || queryText;
    if (!query.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await api.query(query);
      setResult(response);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function handleExport() {
    if (!result || result.results.length === 0) return;

    const csv = [
      ["Type", "Vendor", "Date", "Category", "Amount", "Currency", "Status"].join(","),
      ...result.results.map((rec) =>
        [
          rec.record_type,
          `"${rec.vendor_name || ""}"`,
          rec.record_date || "",
          `"${rec.category?.name || ""}"`,
          rec.total_amount || "",
          rec.currency || "",
          rec.status,
        ].join(",")
      ),
    ].join("\n");

    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "financeiq_query_results.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <AppShell>
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-zinc-100 mb-2">
            <span className="gradient-text">Smart Query</span>
          </h1>
          <p className="text-zinc-400">
            Ask questions about your financial records in plain English
          </p>
        </div>

        {/* Search Bar */}
        <Card className="mb-8 gradient-border relative z-10">
          <CardContent className="p-4">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleQuery();
              }}
              className="flex gap-3 relative z-10"
            >
              <div className="relative flex-1">
                <Sparkles className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-violet-400 pointer-events-none" />
                <Input
                  value={queryText}
                  onChange={(e) => setQueryText(e.target.value)}
                  placeholder='Try: "Show me all healthcare expenses from last month"'
                  className="pl-11 h-12 text-base border-zinc-700 relative z-10"
                />
              </div>
              <Button
                type="submit"
                disabled={loading || !queryText.trim()}
                size="lg"
                className="gap-2 px-6 cursor-pointer relative z-20 hover:scale-[1.02] active:scale-[0.98] transition-all"
              >
                {loading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Search className="w-4 h-4" />
                )}
                Search
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Loading Indicator */}
        {loading && (
          <Card className="mb-6 border-violet-500/20 bg-violet-500/5">
            <CardContent className="p-10 text-center">
              <Loader2 className="w-8 h-8 text-violet-400 animate-spin mx-auto mb-3" />
              <p className="text-zinc-200 font-medium">Interpreting query with Gemini AI...</p>
              <p className="text-zinc-400 text-sm mt-1">Filtering your structured financial data</p>
            </CardContent>
          </Card>
        )}

        {/* Example Queries */}
        {!result && !loading && !error && (
          <div className="mb-8">
            <div className="flex items-center gap-2 mb-3">
              <Lightbulb className="w-4 h-4 text-amber-400" />
              <span className="text-sm text-zinc-400">Try these example queries:</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {EXAMPLE_QUERIES.map((q) => (
                <button
                  key={q}
                  onClick={() => {
                    setQueryText(q);
                    handleQuery(q);
                  }}
                  className="px-3 py-1.5 text-sm text-zinc-300 bg-zinc-800/50 border border-zinc-700 rounded-lg hover:bg-zinc-800 hover:border-violet-500/30 transition-all cursor-pointer"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <Card className="mb-6 border-red-500/20 bg-red-500/5">
            <CardContent className="p-4 text-red-300 text-sm">{error}</CardContent>
          </Card>
        )}

        {/* Results */}
        {result && (
          <>
            {/* Interpretation */}
            <Card className="mb-6 border-violet-500/20 bg-violet-500/5">
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <Sparkles className="w-5 h-5 text-violet-400 shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm text-violet-300">{result.explanation}</p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {result.interpreted_filters.record_type && (
                        <Badge variant="default">type: {result.interpreted_filters.record_type}</Badge>
                      )}
                      {result.interpreted_filters.category_name && (
                        <Badge variant="default">category: {result.interpreted_filters.category_name}</Badge>
                      )}
                      {result.interpreted_filters.vendor_name && (
                        <Badge variant="default">vendor: {result.interpreted_filters.vendor_name}</Badge>
                      )}
                      {result.interpreted_filters.date_from && (
                        <Badge variant="default">from: {result.interpreted_filters.date_from}</Badge>
                      )}
                      {result.interpreted_filters.date_to && (
                        <Badge variant="default">to: {result.interpreted_filters.date_to}</Badge>
                      )}
                      {result.interpreted_filters.amount_min != null && (
                        <Badge variant="default">min: ${result.interpreted_filters.amount_min}</Badge>
                      )}
                      {result.interpreted_filters.amount_max != null && (
                        <Badge variant="default">max: ${result.interpreted_filters.amount_max}</Badge>
                      )}
                      {result.interpreted_filters.status && (
                        <Badge variant="default">status: {result.interpreted_filters.status}</Badge>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Results Count & Export */}
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm text-zinc-400">
                {result.total_count} result{result.total_count !== 1 ? "s" : ""} found
              </p>
              {result.results.length > 0 && (
                <Button variant="outline" size="sm" onClick={handleExport} className="gap-1">
                  <Download className="w-4 h-4" /> Export CSV
                </Button>
              )}
            </div>

            {/* Results List */}
            {result.results.length === 0 ? (
              <Card>
                <CardContent className="p-12 text-center">
                  <Search className="w-12 h-12 text-zinc-700 mx-auto mb-3" />
                  <p className="text-zinc-400 font-medium">No records match your query</p>
                  <p className="text-zinc-500 text-sm mt-1">Try different search terms</p>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <div className="divide-y divide-zinc-800">
                  {result.results.map((record) => (
                    <Link
                      key={record.id}
                      href={`/records/${record.id}`}
                      className="flex items-center justify-between p-4 hover:bg-zinc-800/30 transition-colors group"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-zinc-800 flex items-center justify-center group-hover:bg-zinc-700 transition-colors text-lg">
                          {getRecordTypeIcon(record.record_type)}
                        </div>
                        <div>
                          <p className="text-sm font-medium text-zinc-200">
                            {record.vendor_name || record.original_filename}
                          </p>
                          <div className="flex items-center gap-2 mt-1">
                            <p className="text-xs text-zinc-500">
                              {formatDate(record.record_date)} ·{" "}
                              {record.line_item_count} item{record.line_item_count !== 1 ? "s" : ""}
                            </p>
                            {record.category && (
                              <CategoryBadge category={record.category} className="scale-90 origin-left" />
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-sm font-medium text-zinc-200">
                          {formatCurrency(record.total_amount, record.currency)}
                        </span>
                        <ArrowRight className="w-4 h-4 text-zinc-500 group-hover:text-violet-400 transition-colors" />
                      </div>
                    </Link>
                  ))}
                </div>
              </Card>
            )}
          </>
        )}
      </div>
    </AppShell>
  );
}
