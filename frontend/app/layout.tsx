import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Vacation Planer",
  description: "Trouvez vols, hébergements et voitures avec insights de prix en temps réel.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body className={`${inter.className} bg-slate-50 min-h-screen`}>
        <header className="bg-white border-b border-slate-200 px-6 py-4">
          <div className="max-w-5xl mx-auto flex items-center gap-3">
            <svg className="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 12 3.269 3.125A59.769 59.769 0 0 1 21.485 12 59.768 59.768 0 0 1 3.27 20.875L5.999 12Zm0 0h7.5" />
            </svg>
            <span className="font-semibold text-slate-800 text-lg tracking-tight">
              Vacation Planer
            </span>
            <span className="ml-2 text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full font-medium">
              Beta
            </span>
          </div>
        </header>
        <main className="max-w-5xl mx-auto px-6 py-10">{children}</main>
      </body>
    </html>
  );
}
