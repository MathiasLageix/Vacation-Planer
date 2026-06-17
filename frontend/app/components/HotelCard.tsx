"use client";
import type { Hotel } from "../types";

function Stars({ count }: { count: number | null }) {
  if (!count) return null;
  return (
    <span className="text-amber-400 text-sm">
      {"★".repeat(Math.min(count, 5))}
      {"☆".repeat(Math.max(0, 5 - count))}
    </span>
  );
}

export function HotelCard({ hotel, rank }: { hotel: Hotel; rank: number }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 flex items-center gap-6 hover:shadow-md transition-shadow">
      <div className="text-2xl font-bold text-slate-300 w-8 text-center shrink-0">{rank}</div>

      <div className="flex-1 min-w-0">
        <div className="font-semibold text-slate-800 truncate">{hotel.name}</div>
        <Stars count={hotel.stars} />
        {hotel.address && (
          <div className="text-xs text-slate-400 truncate mt-0.5">{hotel.address}</div>
        )}
        <div className="text-xs text-slate-500 mt-1">
          {hotel.check_in} → {hotel.check_out} · {hotel.nights} nuit{hotel.nights > 1 ? "s" : ""}
        </div>
      </div>

      <div className="text-right shrink-0">
        <div className="text-xl font-bold text-slate-800">
          {hotel.price_per_night.toFixed(0)}{" "}
          <span className="text-sm font-normal text-slate-500">{hotel.currency}/nuit</span>
        </div>
        <div className="text-xs text-slate-400">
          Total : {hotel.total_price.toFixed(0)} {hotel.currency}
        </div>
        <a
          href={hotel.deep_link}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-2 inline-block bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-4 py-1.5 rounded-lg transition-colors"
        >
          Voir l'hôtel →
        </a>
      </div>
    </div>
  );
}
