import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Toaster } from "sonner";

import { MotionProvider } from "@/src/components/ui/motion-provider";
import { AppQueryProvider } from "@/src/components/ui/query-provider";
import { ThemeProvider } from "@/src/components/ui/theme-provider";
import { I18nProvider } from "@/src/i18n/provider";
import "./globals.css";

const appFont = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "StockPilot AI",
  description:
    "Локальное AI-рабочее пространство для продаж, запасов, прогнозирования и закупок.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="ru"
      suppressHydrationWarning
      data-scroll-behavior="smooth"
      className={`${appFont.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <I18nProvider>
          <AppQueryProvider>
            <ThemeProvider>
              <MotionProvider>
                {children}
                <Toaster richColors position="top-right" />
              </MotionProvider>
            </ThemeProvider>
          </AppQueryProvider>
        </I18nProvider>
      </body>
    </html>
  );
}
