import { ProfileContextProvider } from "@/components/profile-context";
import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  // metadataBase: new URL("https://ai-sdk-preview-rag.vercel.app"),
  title: "Run Book Maker",
  description:
    "This tool demonstrates creating comprehensive run books by analyzing a product's documentation. It researches and synthesizes documentation to produce a single run book. For now, it only has documentation for Databricks, but more will be added.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <ProfileContextProvider>
          {children}
        </ProfileContextProvider>
      </body>
    </html>
  );
}
