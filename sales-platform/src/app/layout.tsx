import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { TRPCProvider } from "@/components/TRPCProvider";
import { NavBar } from "@/components/NavBar";
import { auth } from "@/lib/auth";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Sales Intelligence Platform",
  description: "AI-powered enterprise sales assistant powered by IBM watsonx",
};

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await auth();

  return (
    <html lang="en">
      <body className={inter.className}>
        <TRPCProvider>
          {session?.user && <NavBar user={session.user} />}
          <main className="min-h-screen bg-gray-50">{children}</main>
        </TRPCProvider>
      </body>
    </html>
  );
}
