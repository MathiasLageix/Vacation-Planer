"use client";
import type { Flight } from "../types";

function formatDuration(minutes: number) {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return `${h}h${m > 0 ? m + "m" : ""}`;
}

function formatTime(iso: string) {
  return iso.slice(11, 16);
}

export function FlightCard({ flight, rank }: { flight: Flight; rank: number }) {
  const first = flight.segments[0];
  const last = flight.segments[flight.segments.length - 1];
  const totalMinutes = flight.segments.reduce((s, seg) => s + seg.duration_minutes, 0);
  const carriers = Array.from(new Set(flight.segments.map((s) => s.carrier_code)));

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 flex items-center gap-6 hover:shadow-md transition-shadow">
      {/* Rang */}
      <div className="text-2xl font-bold text-slate-300 w-8 text-center shrink-0">
        {rank}
      </div>

      {/* Compagnie + vol */}
      <div className="w-24 shrink-0">
        <div className="text-sm font-semibold text-slate-700">{carriers.join(", ")}</div>
        <div className="text-xs text-slate-400">{first.flight_number}</div>
      </div>

      {/* Trajet */}
      <div className="flex items-center gap-3 flex-1">
        <div className="text-center">
          <div className="text-lg font-bold text-slate-800">{formatTime(first.departure_at)}</div>
          <div className="text-xs text-slate-500">{first.origin}</div>
        </div>
        <div className="flex-1 flex flex-col items-center">
          <div className="text-xs text-slate-400">{formatDuration(totalMinutes)}</div>
          <div className="w-full h-px bg-slate-200 relative my-1">
            <div className="absolute right-0 top-1/2 -translate-y-1/2 w-1.5 h-1.5 bg-slate-400 rounded-full" />
          </div>
          <div className="text-xs text-slate-500">
            {flight.stops === 0 ? (
              <span className="text-green-600 font-medium">Direct</span>
            ) : (
              <span className="text-amber-600">{flight.stops} escale{flight.stops > 1 ? "s" : ""}</span>
            )}
          </div>
        </div>
        <div className="text-center">
          <div className="text-lg font-bold text-slate-800">{formatTime(last.arrival_at)}</div>
          <div className="text-xs text-slate-500">{last.destination}</div>
        </div>
      </div>

      {/* Prix + CTA */}
      <div className="text-right shrink-0">
        <div className="text-xl font-bold text-slate-800">
          {flight.total_price.toFixed(0)}{" "}
          <span className="text-sm font-normal text-slate-500">{flight.currency}</span>
        </div>
        <a
          href={flight.deep_link}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-2 inline-block bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-4 py-1.5 rounded-lg transition-colors"
        >
          Voir le prix →
        </a>
      </div>
    </div>
  );
}
