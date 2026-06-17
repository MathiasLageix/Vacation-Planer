"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import type { SearchFormData } from "../types";

const today = new Date().toISOString().split("T")[0];

const DEFAULT: SearchFormData = {
  origin: "",
  destination: "",
  departure_date: "",
  return_date: "",
  adults: 1,
  children: 0,
  max_stops: "",
  preferred_carriers: "",
  max_price: "",
  currency: "CAD",
  flexible_days: 0,
  include_hotel: false,
  city_iata: "",
  check_in: "",
  check_out: "",
  hotel_adults: 1,
  rooms: 1,
  max_price_per_night: "",
  include_car: false,
  pickup_location: "",
  dropoff_location: "",
  pickup_datetime: "",
  dropoff_datetime: "",
};

function Label({ children }: { children: React.ReactNode }) {
  return <label className="block text-sm font-medium text-slate-700 mb-1">{children}</label>;
}

function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none min-h-[44px]"
    />
  );
}

function Section({ title, children }: { title: string; icon?: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6">
      <h2 className="text-base font-semibold text-slate-800 mb-4">{title}</h2>
      {children}
    </div>
  );
}

export function SearchForm() {
  const [form, setForm] = useState<SearchFormData>(DEFAULT);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  function set(key: keyof SearchFormData, value: string | number | boolean) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const body: Record<string, unknown> = {
      flight: {
        origin: form.origin.toUpperCase(),
        destination: form.destination.toUpperCase(),
        departure_date: form.departure_date,
        return_date: form.return_date || null,
        adults: form.adults,
        children: form.children,
        max_stops: form.max_stops !== "" ? Number(form.max_stops) : null,
        preferred_carriers: form.preferred_carriers
          ? form.preferred_carriers.split(",").map((c) => c.trim().toUpperCase())
          : [],
        max_price: form.max_price !== "" ? Number(form.max_price) : null,
        currency: form.currency,
        flexible_days: form.flexible_days,
      },
    };

    if (form.include_hotel) {
      body.hotel = {
        city_iata: (form.city_iata || form.destination).toUpperCase(),
        check_in: form.check_in || form.departure_date,
        check_out: form.check_out || form.return_date || "",
        adults: form.hotel_adults,
        rooms: form.rooms,
        max_price_per_night: form.max_price_per_night !== "" ? Number(form.max_price_per_night) : null,
        currency: form.currency,
      };
    }

    if (form.include_car) {
      body.car = {
        pickup_location: form.pickup_location.toUpperCase(),
        dropoff_location: (form.dropoff_location || form.pickup_location).toUpperCase(),
        pickup_datetime: form.pickup_datetime,
        dropoff_datetime: form.dropoff_datetime,
        currency: form.currency,
      };
    }

    try {
      // Store criteria in sessionStorage so results page can read them
      sessionStorage.setItem("search_criteria", JSON.stringify(body));
      sessionStorage.setItem("search_summary", JSON.stringify({
        origin: form.origin,
        destination: form.destination,
        departure_date: form.departure_date,
        return_date: form.return_date,
        adults: form.adults,
        include_hotel: form.include_hotel,
      }));
      router.push("/results");
    } catch (err) {
      setError(String(err));
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Vols */}
      <Section title="Vols" icon="✈️">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
          <div>
            <Label>Aéroport de départ (ex : YUL)</Label>
            <Input
              placeholder="YUL"
              value={form.origin}
              onChange={(e) => set("origin", e.target.value)}
              maxLength={3}
              required
            />
          </div>
          <div>
            <Label>Aéroport d'arrivée (ex : CDG)</Label>
            <Input
              placeholder="CDG"
              value={form.destination}
              onChange={(e) => set("destination", e.target.value)}
              maxLength={3}
              required
            />
          </div>
          <div>
            <Label>Date de départ</Label>
            <Input
              type="date"
              min={today}
              value={form.departure_date}
              onChange={(e) => set("departure_date", e.target.value)}
              required
            />
          </div>
          <div>
            <Label>Date de retour (optionnel)</Label>
            <Input
              type="date"
              min={form.departure_date || today}
              value={form.return_date}
              onChange={(e) => set("return_date", e.target.value)}
            />
          </div>
          <div>
            <Label>Adultes</Label>
            <Input
              type="number"
              min={1}
              max={9}
              value={form.adults}
              onChange={(e) => set("adults", Number(e.target.value))}
            />
          </div>
          <div>
            <Label>Enfants (0–11 ans)</Label>
            <Input
              type="number"
              min={0}
              max={8}
              value={form.children}
              onChange={(e) => set("children", Number(e.target.value))}
            />
          </div>
          <div>
            <Label>Devise</Label>
            <Input
              value={form.currency}
              onChange={(e) => set("currency", e.target.value)}
              maxLength={3}
            />
          </div>
          <div>
            <Label>Budget max (optionnel)</Label>
            <Input
              type="number"
              min={0}
              placeholder="ex: 1200"
              value={form.max_price}
              onChange={(e) => set("max_price", e.target.value)}
            />
          </div>
          <div>
            <Label>Escales max (optionnel)</Label>
            <Input
              type="number"
              min={0}
              max={3}
              placeholder="0 = direct"
              value={form.max_stops}
              onChange={(e) => set("max_stops", e.target.value)}
            />
          </div>
          <div>
            <Label>Flexibilité ±jours</Label>
            <Input
              type="number"
              min={0}
              max={5}
              value={form.flexible_days}
              onChange={(e) => set("flexible_days", Number(e.target.value))}
            />
          </div>
          <div>
            <Label>Compagnies préférées (optionnel)</Label>
            <Input
              placeholder="ex : AC, AF"
              value={form.preferred_carriers}
              onChange={(e) => set("preferred_carriers", e.target.value)}
            />
          </div>
        </div>
      </Section>

      {/* Hébergement */}
      <Section title="Hébergement" icon="🏨">
        <label className="flex items-center gap-3 cursor-pointer mb-4 min-h-[44px]">
          <input
            type="checkbox"
            checked={form.include_hotel}
            onChange={(e) => set("include_hotel", e.target.checked)}
            className="rounded w-5 h-5 shrink-0 accent-indigo-600"
          />
          <span className="text-sm text-slate-700">Inclure la recherche d'hébergement</span>
        </label>
        {form.include_hotel && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <Label>Ville de destination (ex : PAR)</Label>
              <Input
                placeholder="PAR"
                value={form.city_iata}
                onChange={(e) => set("city_iata", e.target.value)}
                maxLength={3}
              />
            </div>
            <div>
              <Label>Budget max/nuit (optionnel)</Label>
              <Input
                type="number"
                min={0}
                placeholder="ex: 200"
                value={form.max_price_per_night}
                onChange={(e) => set("max_price_per_night", e.target.value)}
              />
            </div>
            <div>
              <Label>Arrivée à l'hôtel</Label>
              <Input
                type="date"
                value={form.check_in || form.departure_date}
                onChange={(e) => set("check_in", e.target.value)}
              />
            </div>
            <div>
              <Label>Départ de l'hôtel</Label>
              <Input
                type="date"
                value={form.check_out || form.return_date}
                onChange={(e) => set("check_out", e.target.value)}
              />
            </div>
          </div>
        )}
      </Section>

      {/* Autos */}
      <Section title="Location de voiture" icon="🚗">
        <label className="flex items-center gap-3 cursor-pointer mb-4 min-h-[44px]">
          <input
            type="checkbox"
            checked={form.include_car}
            onChange={(e) => set("include_car", e.target.checked)}
            className="rounded w-5 h-5 shrink-0 accent-indigo-600"
          />
          <span className="text-sm text-slate-700">Inclure la location de voiture</span>
        </label>
        {form.include_car && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <Label>Lieu de prise en charge (ex : CDG)</Label>
              <Input
                placeholder={form.destination || "CDG"}
                value={form.pickup_location}
                onChange={(e) => set("pickup_location", e.target.value)}
                maxLength={3}
              />
            </div>
            <div>
              <Label>Lieu de retour (ex : CDG)</Label>
              <Input
                placeholder={form.pickup_location || "CDG"}
                value={form.dropoff_location}
                onChange={(e) => set("dropoff_location", e.target.value)}
                maxLength={3}
              />
            </div>
            <div>
              <Label>Date/heure de prise en charge</Label>
              <Input
                type="datetime-local"
                value={form.pickup_datetime}
                onChange={(e) => set("pickup_datetime", e.target.value)}
              />
            </div>
            <div>
              <Label>Date/heure de retour</Label>
              <Input
                type="datetime-local"
                value={form.dropoff_datetime}
                onChange={(e) => set("dropoff_datetime", e.target.value)}
              />
            </div>
          </div>
        )}
      </Section>

      {error && (
        <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-3">
          {error}
        </div>
      )}

      <button
        type="submit"
        disabled={loading}
        className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 text-white font-semibold py-3 rounded-xl text-base transition-colors focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 outline-none"
      >
        {loading ? "Préparation…" : "Rechercher"}
      </button>
    </form>
  );
}
