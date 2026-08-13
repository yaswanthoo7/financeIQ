"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/layout/app-shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api, type Analytics, type RecordListItem } from "@/lib/api";
import {
  formatCurrency,
  formatDate,
  getStatusColor,
  getRecordTypeIcon,
  getRecordTypeLabel,
  getRecordTypeColor,
} from "@/lib/utils";
import {
  FileText,
  DollarSign,
  TrendingUp,
  Upload,
  ArrowRight,
  Building2,
  AlertCircle,
  Tag,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
} from "recharts";

export default function DashboardPage() {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [recentRecords, setRecentRecords] = useState<RecordListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      setLoading(true);
      const [analyticsData, recordsData] = await Promise.all([
        api.getAnalytics(),
        api.listRecords({ page_size: 5, sort_by: "created_at", sort_order: "desc" }),
      ]);
      setAnalytics(analyticsData);
      setRecentRecords(recordsData.items);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  // Empty state
  if (!loading && analytics && analytics.total_records === 0) {
    return (
      <AppShell>
        <div className="flex flex-col items-center justify-center min-h-[70vh] text-center">
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-violet-500/20 to-indigo-500/20 flex items-center justify-center mb-6 animate-float">
            <FileText className="w-10 h-10 text-violet-400" />
          </div>
          <h1 className="text-3xl font-bold text-zinc-100 mb-3">
            Welcome to <span className="gradient-text">FinanceIQ</span>
          </h1>
          <p className="text-zinc-400 text-lg mb-8 max-w-md">
            Upload your first financial document to get started. We&apos;ll automatically
            classify, categorize, and extract all the data.
          </p>
          <Link href="/upload">
            <Button size="lg" className="gap-2">
              <Upload className="w-5 h-5" />
              Upload Your First Document
            </Button>
          </Link>
          <div className="mt-12 grid grid-cols-4 gap-6 text-center max-w-2xl">
            <div>
              <div className="text-2xl mb-1">📄</div>
              <div className="text-sm text-zinc-500">Invoices</div>
            </div>
            <div>
              <div className="text-2xl mb-1">🧾</div>
              <div className="text-sm text-zinc-500">Receipts</div>
            </div>
            <div>
              <div className="text-2xl mb-1">📋</div>
              <div className="text-sm text-zinc-500">Purchase Orders</div>
            </div>
            <div>
              <div className="text-2xl mb-1">💰</div>
              <div className="text-sm text-zinc-500">Expense Reports</div>
            </div>
          </div>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">Dashboard</h1>
          <p className="text-zinc-400 mt-1">Overview of your financial records</p>
        </div>
        <Link href="/upload">
          <Button className="gap-2">
            <Upload className="w-4 h-4" />
            Upload Documents
          </Button>
        </Link>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-32 skeleton rounded-xl" />
          ))}
        </div>
      ) : error ? (
        <Card className="border-red-500/20">
          <CardContent className="p-6 flex items-center gap-3 text-red-400">
            <AlertCircle className="w-5 h-5" />
            <span>{error}</span>
          </CardContent>
        </Card>
      ) : analytics ? (
        <>
          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <Card className="gradient-border">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-zinc-400">Total Records</p>
                    <p className="text-3xl font-bold text-zinc-100 mt-1">
                      {analytics.total_records}
                    </p>
                  </div>
                  <div className="w-12 h-12 rounded-xl bg-violet-500/10 flex items-center justify-center">
                    <FileText className="w-6 h-6 text-violet-400" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="gradient-border">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-zinc-400">Total Spend</p>
                    <p className="text-3xl font-bold text-zinc-100 mt-1">
                      {formatCurrency(analytics.total_spend)}
                    </p>
                  </div>
                  <div className="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center">
                    <DollarSign className="w-6 h-6 text-emerald-400" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="gradient-border">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-zinc-400">Average Amount</p>
                    <p className="text-3xl font-bold text-zinc-100 mt-1">
                      {formatCurrency(analytics.average_record_amount)}
                    </p>
                  </div>
                  <div className="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center">
                    <TrendingUp className="w-6 h-6 text-blue-400" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="gradient-border">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-zinc-400">Categories</p>
                    <p className="text-3xl font-bold text-zinc-100 mt-1">
                      {analytics.spend_by_category.length}
                    </p>
                  </div>
                  <div className="w-12 h-12 rounded-xl bg-amber-500/10 flex items-center justify-center">
                    <Tag className="w-6 h-6 text-amber-400" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {/* Spend by Category (Pie Chart) */}
            {analytics.spend_by_category.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Spend by Category</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={analytics.spend_by_category.slice(0, 8)}
                          dataKey="total_spend"
                          nameKey="category_name"
                          cx="50%"
                          cy="50%"
                          outerRadius={80}
                          label={({ category_name, percent }: any) =>
                            `${category_name} (${(percent * 100).toFixed(0)}%)`
                          }
                          labelLine={true}
                        >
                          {analytics.spend_by_category.slice(0, 8).map((entry, index) => (
                            <Cell
                              key={index}
                              fill={entry.category_color || `hsl(${index * 45}, 70%, 60%)`}
                            />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={{
                            backgroundColor: "#18181b",
                            border: "1px solid #27272a",
                            borderRadius: "8px",
                            color: "#fafafa",
                          }}
                          formatter={(value: any) => [formatCurrency(value ? Number(value) : 0), "Spend"]}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Monthly Trend */}
            {analytics.monthly_trend.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Monthly Spending Trend</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={analytics.monthly_trend}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                        <XAxis dataKey="month" stroke="#71717a" fontSize={12} />
                        <YAxis stroke="#71717a" fontSize={12} />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: "#18181b",
                            border: "1px solid #27272a",
                            borderRadius: "8px",
                            color: "#fafafa",
                          }}
                          formatter={(value: any) => [formatCurrency(value ? Number(value) : 0), "Spend"]}
                        />
                        <Line
                          type="monotone"
                          dataKey="total_spend"
                          stroke="#8b5cf6"
                          strokeWidth={2}
                          dot={{ fill: "#8b5cf6", r: 4 }}
                          activeDot={{ r: 6, fill: "#a78bfa" }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Top Vendors */}
            {analytics.top_vendors.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Top Vendors by Spend</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={analytics.top_vendors.slice(0, 5)} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                        <XAxis type="number" stroke="#71717a" fontSize={12} />
                        <YAxis
                          dataKey="vendor_name"
                          type="category"
                          stroke="#71717a"
                          fontSize={12}
                          width={120}
                          tickFormatter={(value: string) =>
                            value.length > 15 ? value.slice(0, 15) + "…" : value
                          }
                        />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: "#18181b",
                            border: "1px solid #27272a",
                            borderRadius: "8px",
                            color: "#fafafa",
                          }}
                          formatter={(value: any) => [formatCurrency(value ? Number(value) : 0), "Spend"]}
                        />
                        <Bar dataKey="total_spend" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Record Type Breakdown */}
            {analytics.record_type_breakdown.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Document Types</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {analytics.record_type_breakdown.map((item) => (
                      <div key={item.record_type} className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="text-xl">{getRecordTypeIcon(item.record_type)}</span>
                          <div>
                            <p className="text-sm font-medium text-zinc-200">
                              {getRecordTypeLabel(item.record_type)}
                            </p>
                            <p className="text-xs text-zinc-500">
                              {item.count} {item.count === 1 ? "record" : "records"}
                            </p>
                          </div>
                        </div>
                        <span className="text-sm font-medium text-zinc-300">
                          {formatCurrency(item.total_spend)}
                        </span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Recent Records */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-base">Recent Records</CardTitle>
              <Link href="/records">
                <Button variant="ghost" size="sm" className="gap-1">
                  View All <ArrowRight className="w-4 h-4" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent>
              {recentRecords.length === 0 ? (
                <p className="text-zinc-500 text-center py-4">No records yet</p>
              ) : (
                <div className="space-y-3">
                  {recentRecords.map((record) => (
                    <Link
                      key={record.id}
                      href={`/records/${record.id}`}
                      className="flex items-center justify-between p-3 rounded-lg hover:bg-zinc-800/50 transition-colors group"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-zinc-800 flex items-center justify-center group-hover:bg-zinc-700 transition-colors text-lg">
                          {getRecordTypeIcon(record.record_type)}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <p className="text-sm font-medium text-zinc-200">
                              {record.vendor_name || record.original_filename}
                            </p>
                            {record.category && (
                              <span
                                className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium"
                                style={{
                                  backgroundColor: `${record.category.color}20`,
                                  color: record.category.color || "#a1a1aa",
                                }}
                              >
                                {record.category.icon} {record.category.name}
                              </span>
                            )}
                          </div>
                          <p className="text-xs text-zinc-500">
                            {getRecordTypeLabel(record.record_type)} · {formatDate(record.record_date || record.created_at)}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-sm font-medium text-zinc-200">
                          {formatCurrency(record.total_amount, record.currency)}
                        </span>
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
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </>
      ) : null}
    </AppShell>
  );
}
