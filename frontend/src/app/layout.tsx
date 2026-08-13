import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FinanceIQ — Turn Messy Financial Documents into Structured Data",
  description:
    "Upload invoices, receipts, purchase orders, and expense reports. FinanceIQ uses AI to classify, categorize, and extract structured data — then lets you search, query, and analyze your finances.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-background antialiased">
        {children}
      </body>
    </html>
  );
}
