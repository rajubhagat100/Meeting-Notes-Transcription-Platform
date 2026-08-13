import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Fireflies.ai Workspace - Meeting Notes & Transcription Platform",
  description: "Browse meeting transcripts, review AI-generated outlines, track action items, and ask questions using contextual LLM chat.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body style={{ minHeight: "100vh" }}>
        {children}
      </body>
    </html>
  );
}
