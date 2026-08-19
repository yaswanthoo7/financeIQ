"use client";

import React, { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { AppShell } from "@/components/layout/app-shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { api, type FinancialRecord, type Category } from "@/lib/api";
import { formatCurrency, getConfidenceColor } from "@/lib/utils";
import {
  ArrowLeft,
  Save,
  Trash2,
  AlertTriangle,
  Loader2,
  FileText,
  Plus,
  X,
  Tag,
} from "lucide-react";

export default function RecordDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [record, setRecord] = useState<FinancialRecord | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form State
  const [formData, setFormData] = useState<any>({});
  const [lineItems, setLineItems] = useState<any[]>([]);
  const [anomalies, setAnomalies] = useState<any[]>([]);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [recordData, cats] = await Promise.all([
        api.getRecord(id),
        api.listCategories(),
      ]);
      setRecord(recordData);
      setCategories(cats);
      
      let parsedAnomalies = [];
      try {
        if (recordData.anomalies) {
          parsedAnomalies = typeof recordData.anomalies === 'string' 
            ? JSON.parse(recordData.anomalies) 
            : recordData.anomalies;
        }
      } catch (e) {
        console.error("Failed to parse anomalies", e);
      }
      setAnomalies(parsedAnomalies);

      // Initialize form data
      setFormData({
        record_type: recordData.record_type || "invoice",
        category_id: recordData.category_id || "",
        vendor_name: recordData.vendor_name || "",
        record_date: recordData.record_date || "",
        total_amount: recordData.total_amount || 0,
        currency: recordData.currency || "USD",
        status: recordData.status || "processing",
        // Invoice specific
        invoice_number: recordData.invoice_detail?.invoice_number || "",
        due_date: recordData.invoice_detail?.due_date || "",
        customer_name: recordData.invoice_detail?.customer_name || "",
        // Receipt specific
        merchant_name: recordData.receipt_detail?.merchant_name || "",
        payment_method: recordData.receipt_detail?.payment_method || "",
        // PO specific
        po_number: recordData.purchase_order_detail?.po_number || "",
        po_status: recordData.purchase_order_detail?.po_status || "",
        // Expense Report specific
        report_number: recordData.expense_report_detail?.report_number || "",
        employee_name: recordData.expense_report_detail?.employee_name || "",
        purpose: recordData.expense_report_detail?.purpose || "",
      });
      setLineItems(recordData.line_items || []);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (id) loadData();
  }, [id, loadData]);

  const handleSave = async () => {
    if (!record) return;
    try {
      setSaving(true);
      
      // Build the update payload
      const payload: Partial<FinancialRecord> = {
        record_type: formData.record_type,
        category_id: formData.category_id || null,
        vendor_name: formData.vendor_name,
        record_date: formData.record_date || null,
        total_amount: Number(formData.total_amount),
        currency: formData.currency,
        status: "completed", // auto-complete on save
        line_items: lineItems.map((item, index) => ({
          ...item,
          sort_order: index,
        })),
      };

      // Add type-specific details
      if (formData.record_type === "invoice") {
        payload.invoice_detail = {
          ...(record.invoice_detail || {}),
          invoice_number: formData.invoice_number || null,
          due_date: formData.due_date || null,
          customer_name: formData.customer_name || null,
        } as any;
      } else if (formData.record_type === "receipt") {
        payload.receipt_detail = {
          ...(record.receipt_detail || {}),
          merchant_name: formData.merchant_name || null,
          payment_method: formData.payment_method || null,
        } as any;
      } else if (formData.record_type === "purchase_order") {
        payload.purchase_order_detail = {
          ...(record.purchase_order_detail || {}),
          po_number: formData.po_number || null,
          po_status: formData.po_status || null,
        } as any;
      } else if (formData.record_type === "expense_report") {
        payload.expense_report_detail = {
          ...(record.expense_report_detail || {}),
          report_number: formData.report_number || null,
          employee_name: formData.employee_name || null,
          purpose: formData.purpose || null,
        } as any;
      }

      await api.updateRecord(id, payload);
      router.push("/records");
    } catch (err: any) {
      setError(err.message);
      setSaving(false);
    }
  };

  const getAnomaly = (fieldName: string) => {
    return anomalies.find(a => a.field === fieldName);
  };

  const handleDelete = async () => {
    if (confirm("Are you sure you want to delete this record?")) {
      try {
        await api.deleteRecord(id);
        router.push("/records");
      } catch (err: any) {
        setError(err.message);
      }
    }
  };

  if (loading) {
    return (
      <AppShell>
        <div className="flex items-center justify-center h-[50vh]">
          <Loader2 className="w-8 h-8 animate-spin text-violet-500" />
        </div>
      </AppShell>
    );
  }

  if (error || !record) {
    return (
      <AppShell>
        <Card className="border-red-500/20 bg-red-500/5 max-w-2xl mx-auto mt-8">
          <CardContent className="p-6 flex flex-col items-center text-center">
            <AlertTriangle className="w-10 h-10 text-red-400 mb-4" />
            <h2 className="text-xl font-semibold text-zinc-100 mb-2">Error Loading Record</h2>
            <p className="text-zinc-400 mb-6">{error || "Record not found"}</p>
            <Button onClick={() => router.push("/records")} variant="outline">
              Back to Records
            </Button>
          </CardContent>
        </Card>
      </AppShell>
    );
  }

  return (
    <AppShell>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.push("/records")}
            className="rounded-full bg-zinc-900"
          >
            <ArrowLeft className="w-4 h-4" />
          </Button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-zinc-100">
                {record.original_filename}
              </h1>
              <Badge
                variant={
                  record.status === "completed"
                    ? "success"
                    : record.status === "processing"
                    ? "default"
                    : "warning"
                }
              >
                {record.status}
              </Badge>
            </div>
            <div className="flex items-center gap-2 text-sm text-zinc-400 mt-1">
              <span>{record.extraction_method === "hybrid" ? "Hybrid AI" : "Gemini Vision"}</span>
              <span>•</span>
              <span className="flex items-center gap-1">
                Confidence: 
                <span className={getConfidenceColor(record.confidence_score)}>
                  {record.confidence_score ? `${(record.confidence_score * 100).toFixed(0)}%` : "N/A"}
                </span>
              </span>
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <Button
            variant="destructive"
            onClick={handleDelete}
            className="bg-red-500/10 text-red-400 hover:bg-red-500/20 hover:text-red-300"
          >
            <Trash2 className="w-4 h-4 mr-2" />
            Delete
          </Button>
          <Button onClick={handleSave} disabled={saving} className="bg-violet-600 hover:bg-violet-700">
            {saving ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Save className="w-4 h-4 mr-2" />
            )}
            Save Changes
          </Button>
        </div>
      </div>

      {record.status === "failed" && record.error_message && (
        <Card className="mb-6 border-red-500/20 bg-red-500/5">
          <CardContent className="p-4 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-medium text-red-400 mb-1">Extraction Failed</h3>
              <p className="text-sm text-red-300/90 whitespace-pre-wrap">
                {record.error_message}
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {anomalies.length > 0 && (
        <Card className="mb-6 border-amber-500/30 bg-amber-500/10">
          <CardContent className="p-4 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-medium text-amber-500 mb-1">
                Anomalies Detected ({anomalies.length})
              </h3>
              <p className="text-sm text-amber-500/90">
                The auditor detected mathematical or logical conflicts in the extracted data. Please review the highlighted fields below.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[calc(100vh-140px)]">
        {/* Left side: Document Viewer */}
        <Card className="h-full overflow-hidden flex flex-col bg-zinc-950/50 border-zinc-800">
          <div className="p-3 border-b border-zinc-800 bg-zinc-900/50 flex items-center justify-between">
            <h3 className="text-sm font-medium text-zinc-300 flex items-center gap-2">
              <FileText className="w-4 h-4" />
              Original Document
            </h3>
          </div>
          <div className="flex-1 relative bg-zinc-900/20">
            {record.file_type === ".pdf" ? (
              <object
                data={api.getFileUrl(record.id)}
                type="application/pdf"
                className="w-full h-full rounded-b-xl"
              >
                <div className="flex items-center justify-center h-full text-zinc-500">
                  PDF viewer not available
                </div>
              </object>
            ) : (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={api.getFileUrl(record.id)}
                alt="Document preview"
                className="w-full h-full object-contain p-4"
              />
            )}
          </div>
        </Card>

        {/* Right side: Form */}
        <div className="h-full overflow-y-auto pr-2 custom-scrollbar space-y-6">
          {/* Classification */}
          <Card className="border-violet-500/20 bg-violet-500/5">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-violet-400">Classification</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-xs text-zinc-400">Document Type</label>
                <select
                  className="w-full h-9 rounded-md bg-zinc-900 border border-zinc-800 px-3 text-sm"
                  value={formData.record_type}
                  onChange={(e) => setFormData({ ...formData, record_type: e.target.value })}
                >
                  <option value="invoice">Invoice</option>
                  <option value="receipt">Receipt</option>
                  <option value="purchase_order">Purchase Order</option>
                  <option value="expense_report">Expense Report</option>
                </select>
              </div>
              <div className="space-y-1">
                <label className="text-xs text-zinc-400">Category</label>
                <div className="relative">
                  <select
                    className="w-full h-9 rounded-md bg-zinc-900 border border-zinc-800 pl-8 pr-3 text-sm"
                    value={formData.category_id || ""}
                    onChange={(e) => setFormData({ ...formData, category_id: e.target.value })}
                  >
                    <option value="">Uncategorized</option>
                    {categories.map(c => (
                      <option key={c.id} value={c.id}>{c.icon} {c.name}</option>
                    ))}
                  </select>
                  <Tag className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Core Details */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-zinc-300">Core Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-xs text-zinc-400">Vendor / Merchant</label>
                  <Input
                    value={formData.vendor_name || ""}
                    onChange={(e) => setFormData({ ...formData, vendor_name: e.target.value })}
                    className="h-9"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-zinc-400">Date</label>
                  <Input
                    type="date"
                    value={formData.record_date || ""}
                    onChange={(e) => setFormData({ ...formData, record_date: e.target.value })}
                    className="h-9"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-zinc-400">Total Amount</label>
                  <Input
                    type="number"
                    step="0.01"
                    value={formData.total_amount || ""}
                    onChange={(e) => setFormData({ ...formData, total_amount: e.target.value })}
                    className={`h-9 ${getAnomaly('total_amount') ? 'border-amber-500 bg-amber-500/10 text-amber-500' : ''}`}
                    title={getAnomaly('total_amount')?.message}
                  />
                  {getAnomaly('total_amount') && (
                    <p className="text-[10px] text-amber-500 mt-1">{getAnomaly('total_amount').message}</p>
                  )}
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-zinc-400">Currency</label>
                  <Input
                    value={formData.currency || ""}
                    onChange={(e) => setFormData({ ...formData, currency: e.target.value.toUpperCase() })}
                    className="h-9 uppercase"
                    maxLength={3}
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Type-Specific Details */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-zinc-300">
                {formData.record_type === "invoice" && "Invoice Details"}
                {formData.record_type === "receipt" && "Receipt Details"}
                {formData.record_type === "purchase_order" && "PO Details"}
                {formData.record_type === "expense_report" && "Expense Report Details"}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {formData.record_type === "invoice" && (
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-xs text-zinc-400">Invoice Number</label>
                    <Input
                      value={formData.invoice_number || ""}
                      onChange={(e) => setFormData({ ...formData, invoice_number: e.target.value })}
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs text-zinc-400">Due Date</label>
                    <Input
                      type="date"
                      value={formData.due_date || ""}
                      onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                      className={getAnomaly('due_date') ? 'border-amber-500 bg-amber-500/10 text-amber-500' : ''}
                      title={getAnomaly('due_date')?.message}
                    />
                    {getAnomaly('due_date') && (
                      <p className="text-[10px] text-amber-500 mt-1">{getAnomaly('due_date').message}</p>
                    )}
                  </div>
                  <div className="space-y-1 col-span-2">
                    <label className="text-xs text-zinc-400">Customer Name</label>
                    <Input
                      value={formData.customer_name || ""}
                      onChange={(e) => setFormData({ ...formData, customer_name: e.target.value })}
                    />
                  </div>
                </div>
              )}
              
              {formData.record_type === "receipt" && (
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-xs text-zinc-400">Merchant Name</label>
                    <Input
                      value={formData.merchant_name || ""}
                      onChange={(e) => setFormData({ ...formData, merchant_name: e.target.value })}
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs text-zinc-400">Payment Method</label>
                    <Input
                      value={formData.payment_method || ""}
                      onChange={(e) => setFormData({ ...formData, payment_method: e.target.value })}
                      placeholder="e.g. Credit Card"
                    />
                  </div>
                </div>
              )}
              
              {formData.record_type === "purchase_order" && (
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-xs text-zinc-400">PO Number</label>
                    <Input
                      value={formData.po_number || ""}
                      onChange={(e) => setFormData({ ...formData, po_number: e.target.value })}
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs text-zinc-400">Status</label>
                    <select
                      className="w-full h-9 rounded-md bg-zinc-900 border border-zinc-800 px-3 text-sm"
                      value={formData.po_status || "draft"}
                      onChange={(e) => setFormData({ ...formData, po_status: e.target.value })}
                    >
                      <option value="draft">Draft</option>
                      <option value="submitted">Submitted</option>
                      <option value="approved">Approved</option>
                      <option value="fulfilled">Fulfilled</option>
                    </select>
                  </div>
                </div>
              )}
              
              {formData.record_type === "expense_report" && (
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-xs text-zinc-400">Report Number</label>
                    <Input
                      value={formData.report_number || ""}
                      onChange={(e) => setFormData({ ...formData, report_number: e.target.value })}
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs text-zinc-400">Employee Name</label>
                    <Input
                      value={formData.employee_name || ""}
                      onChange={(e) => setFormData({ ...formData, employee_name: e.target.value })}
                    />
                  </div>
                  <div className="space-y-1 col-span-2">
                    <label className="text-xs text-zinc-400">Purpose</label>
                    <Input
                      value={formData.purpose || ""}
                      onChange={(e) => setFormData({ ...formData, purpose: e.target.value })}
                    />
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Line Items */}
          <Card>
            <CardHeader className="pb-3 flex flex-row items-center justify-between">
              <CardTitle className="text-sm font-medium text-zinc-300">Line Items</CardTitle>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setLineItems([...lineItems, { description: "", quantity: 1, unit_price: 0, line_total: 0 }])}
                className="h-8 gap-1"
              >
                <Plus className="w-3 h-3" /> Add Item
              </Button>
            </CardHeader>
            <CardContent>
              {lineItems.length === 0 ? (
                <p className="text-sm text-zinc-500 text-center py-4">No line items extracted</p>
              ) : (
                <div className="space-y-3">
                  {lineItems.map((item, index) => (
                    <div key={index} className="flex items-start gap-3 p-3 bg-zinc-900/50 rounded-lg border border-zinc-800">
                      <div className="flex-1 space-y-3">
                        <Input
                          placeholder="Description"
                          value={item.description || ""}
                          onChange={(e) => {
                            const newItems = [...lineItems];
                            newItems[index].description = e.target.value;
                            setLineItems(newItems);
                          }}
                          className="h-8 bg-zinc-950"
                        />
                        <div className="flex gap-3">
                          <div className="w-20">
                            <Input
                              type="number"
                              placeholder="Qty"
                              value={item.quantity || ""}
                              onChange={(e) => {
                                const newItems = [...lineItems];
                                newItems[index].quantity = Number(e.target.value);
                                newItems[index].line_total = (newItems[index].quantity * (newItems[index].unit_price || 0));
                                setLineItems(newItems);
                              }}
                              className="h-8 bg-zinc-950"
                            />
                          </div>
                          <div className="flex-1">
                            <Input
                              type="number"
                              placeholder="Price"
                              value={item.unit_price || ""}
                              onChange={(e) => {
                                const newItems = [...lineItems];
                                newItems[index].unit_price = Number(e.target.value);
                                newItems[index].line_total = ((newItems[index].quantity || 0) * newItems[index].unit_price);
                                setLineItems(newItems);
                              }}
                              className="h-8 bg-zinc-950"
                            />
                          </div>
                          <div className="flex-1">
                            <Input
                              type="number"
                              placeholder="Total"
                              value={item.line_total || ""}
                              onChange={(e) => {
                                const newItems = [...lineItems];
                                newItems[index].line_total = Number(e.target.value);
                                setLineItems(newItems);
                              }}
                              className="h-8 bg-zinc-950 font-medium"
                            />
                          </div>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-zinc-500 hover:text-red-400 hover:bg-red-500/10"
                        onClick={() => {
                          const newItems = [...lineItems];
                          newItems.splice(index, 1);
                          setLineItems(newItems);
                        }}
                      >
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
