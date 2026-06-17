"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { FlightCard } from "../components/FlightCard";
import { HotelCard } from "../components/HotelCard";
import { InsightsSection } from "../components/InsightBadge";
import type { Flight, Hotel, Insights } from "../types";

type Status = "loading" | "streaming" | "done" | "error";

function Spinner() {
  return (
    <div className="flex items-center gap-3 text-slate-500">
      <svg className="animate-spin w-5 h-5 text-indigo-500" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
      </svg>
      <span className="text-sm">Recherche en cours…</span>
    </div>
  );
}

function Section({ title, children }: { title: string; icon?: string; children: React.ReactNode }) {
  return (
    <div>
      <h2 className="text-lg font-semibold text-slate-800 mb-3">{title}</h2>
      {children}
    </div>
  );
}

export default function ResultsPage() {
  const router = useRouter();
  const [status, setStatus] = useState<Status>("loading");
  const [flights, setFlights] = useState<Flight[]>([]);
  const [hotels, setHotels] = useState<Hotel[]>([]);
  const [flightInsights, setFlightInsights] = useState<Insights | null>(null);
  const [hotelInsights, setHotelInsights] = useState<Insights | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [summary, setSummary] = useState<Record<string, unknown>>({});

  useEffect(() => {
    const criteria = sessionStorage.getItem("search_criteria");
    const sum = sessionStorage.getItem("search_summary");
    if (!criteria) {
      router.replace("/");
      return;
    }
    if (sum) { try { setSummary(JSON.parse(sum)); } catch { /* sessionStorage corrupt, use defaults */ } }

    let controller: AbortController | null = null;

    async function doSearch() {
      controller = new AbortController();
      setStatus("streaming");

      try {
        const res = await fetch("/api/search", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: criteria,
          signal: controller.signal,
        });

        if (!res.ok || !res.body) {
          setErrorMsg(`Erreur serveur : ${res.status}`);
          setStatus("error");
          return;
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let currentEvent = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const chunks = buffer.split("\n\n");
          buffer = chunks.pop() ?? "";

          for (const chunk of chunks) {
            const lines = chunk.split("\n");
            let eventType = currentEvent;
            let dataLine = "";

            for (const line of lines) {
              if (line.startsWith("event:")) eventType = line.slice(6).trim();
              else if (line.startsWith("data:")) dataLine = line.slice(5).trim();
            }

            if (!dataLine) continue;
            try {
              const msg = JSON.parse(dataLine);
              switch (eventType) {
                case "flights":
                  setFlights(msg.data ?? []);
                  break;
                case "hotels":
                  setHotels(msg.data ?? []);
                  break;
                case "insights":
                  if (msg.type === "flight") setFlightInsights(msg.data);
                  else if (msg.type === "hotel") setHotelInsights(msg.data);
                  break;
                case "done":
                  setStatus("done");
                  break;
                case "error":
                  setErrorMsg(msg.message ?? "Erreur inconnue");
                  setStatus("error");
                  break;
              }
              currentEvent = eventType;
            } catch {
              // non-JSON, skip
            }
          }
        }
        setStatus("done");
      } catch (err: unknown) {
        if ((err as { name?: string }).name !== "AbortError") {
          setErrorMsg(String(err));
          setStatus("error");
        }
      }
    }

    doSearch();
    return () => controller?.abort();
  }, [router]);

  const originStr = summary.origin as string;
  const destStr = summary.destination as string;
  const depDate = summary.departure_date as string;
  const retDate = summary.return_date as string | undefined;

  return (
    <div className="space-y-8">
      {/* Header résultats */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            {originStr && destStr ? `${originStr} → ${destStr}` : "Résultats"}
          </h1>
          {depDate && (
            <p className="text-slate-500 text-sm mt-0.5">
              {depDate}{retDate ? ` → ${retDate}` : " (aller simple)"} · {String(summary.adults ?? 1)} adulte(s)
            </p>
          )}
        </div>
        <button
          onClick={() => router.push("/")}
          className="text-sm text-indigo-600 hover:underline min-h-[44px] px-3 -mx-3 focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 rounded-lg outline-none"
        >
          ← Nouvelle recherche
        </button>
      </div>

      {/* État de la recherche */}
      {(status === "loading" || status === "streaming") && <Spinner />}

      {status === "error" && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">
          {errorMsg ?? "Une erreur est survenue."}
        </div>
      )}

      {/* Vols */}
      {flights.length > 0 && (
        <Section title={`Vols (${flights.length})`} icon="✈️">
          <div className="space-y-3">
            {flights.map((f, i) => (
              <FlightCard key={f.offer_id} flight={f} rank={i + 1} />
            ))}
          </div>
          {flightInsights && (
            <InsightsSection insights={flightInsights} title="vols" />
          )}
        </Section>
      )}

      {/* Hébergements */}
      {hotels.length > 0 && (
        <Section title={`Hébergements (${hotels.length})`} icon="🏨">
          <div className="space-y-3">
            {hotels.map((h, i) => (
              <HotelCard key={h.property_id} hotel={h} rank={i + 1} />
            ))}
          </div>
          {hotelInsights && (
            <InsightsSection insights={hotelInsights} title="hôtels" />
          )}
        </Section>
      )}

      {/* Aucun résultat */}
      {status === "done" && flights.length === 0 && hotels.length === 0 && (
        <div className="text-center py-16 text-slate-400">
          <svg className="mx-auto mb-4 w-12 h-12 text-slate-300" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 15.803a7.5 7.5 0 0 0 10.607 0Z" />
          </svg>
          <p className="text-lg font-medium text-slate-600">Aucun résultat trouvé</p>
          <p className="text-sm mt-1">Essayez d'élargir vos critères (dates, budget, escales).</p>
        </div>
      )}
    </div>
  );
}
