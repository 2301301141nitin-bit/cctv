import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "CCTV SOC Dashboard",
  description: "Real-time AI CCTV Intelligence Dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className={`${inter.className} bg-black text-white overflow-hidden`} suppressHydrationWarning>
        {/* Auth Provider would wrap children here for a full production app */}
        {children}
      </body>
    </html>
  );
}
