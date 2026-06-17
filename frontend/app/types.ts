export interface FlightSegment {
  origin: string;
  destination: string;
  departure_at: string;
  arrival_at: string;
  carrier_code: string;
  flight_number: string;
  duration_minutes: number;
}

export interface Flight {
  provider: string;
  offer_id: string;
  total_price: number;
  currency: string;
  stops: number;
  segments: FlightSegment[];
  deep_link: string;
}

export interface Hotel {
  provider: string;
  property_id: string;
  name: string;
  stars: number | null;
  price_per_night: number;
  total_price: number;
  currency: string;
  check_in: string;
  check_out: string;
  nights: number;
  address: string;
  deep_link: string;
}

export interface PriceChange {
  offer_id: string;
  label: string;
  old_price: number;
  new_price: number;
  delta: number;
  pct_change: number;
  currency: string;
}

export interface AvailabilityChange {
  offer_id: string;
  label: string;
  event: "appeared" | "disappeared";
  price: number;
  currency: string;
}

export interface Insights {
  session_id: string;
  search_type: string;
  snapshot_old_at: string;
  snapshot_new_at: string;
  price_changes: PriceChange[];
  availability: AvailabilityChange[];
}

export interface SearchFormData {
  // Vols
  origin: string;
  destination: string;
  departure_date: string;
  return_date: string;
  adults: number;
  children: number;
  max_stops: string;
  preferred_carriers: string;
  max_price: string;
  currency: string;
  flexible_days: number;
  // Hébergement
  include_hotel: boolean;
  city_iata: string;
  check_in: string;
  check_out: string;
  hotel_adults: number;
  rooms: number;
  max_price_per_night: string;
  // Auto
  include_car: boolean;
  pickup_location: string;
  dropoff_location: string;
  pickup_datetime: string;
  dropoff_datetime: string;
}
