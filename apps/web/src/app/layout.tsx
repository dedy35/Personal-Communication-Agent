import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Personal Communication Agent",
  description: "Local-first communication dashboard"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
