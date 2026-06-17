"""Couche d'insights : compare deux snapshots et détecte les changements."""
from datetime import datetime

from models import AvailabilityInsight, InsightReport, PriceInsight


def _label_for(d: dict) -> str:
    """Construit un label lisible depuis un résultat sérialisé."""
    if "segments" in d:  # vol
        segs = d["segments"]
        if segs:
            return f"{segs[0]['origin']}→{segs[-1]['destination']} {d.get('carrier_codes', [''])[0] if 'carrier_codes' in d else ''}"
    if "name" in d:  # hôtel
        return d["name"]
    if "category" in d:  # auto
        return f"{d.get('company', '')} {d['category']}"
    return d.get("offer_id", d.get("property_id", "?"))


def compare_snapshots(
    session_id: str,
    search_type: str,
    old_at: datetime,
    old_results: list[dict],
    new_at: datetime,
    new_results: list[dict],
) -> InsightReport:
    id_key = "offer_id" if search_type in ("flight", "car") else "property_id"

    old_by_id = {r[id_key]: r for r in old_results if id_key in r}
    new_by_id = {r[id_key]: r for r in new_results if id_key in r}

    price_changes: list[PriceInsight] = []
    availability: list[AvailabilityInsight] = []

    for oid, old in old_by_id.items():
        if oid not in new_by_id:
            availability.append(
                AvailabilityInsight(
                    offer_id=oid,
                    label=_label_for(old),
                    event="disappeared",
                    price=old.get("total_price", 0.0),
                    currency=old.get("currency", ""),
                )
            )
        else:
            new = new_by_id[oid]
            old_price = old.get("total_price", 0.0)
            new_price = new.get("total_price", 0.0)
            delta = new_price - old_price
            if abs(delta) >= 1.0:  # ignore les différences de centimes
                pct = (delta / old_price * 100) if old_price else 0.0
                price_changes.append(
                    PriceInsight(
                        offer_id=oid,
                        label=_label_for(old),
                        old_price=old_price,
                        new_price=new_price,
                        delta=delta,
                        pct_change=round(pct, 1),
                        currency=old.get("currency", ""),
                    )
                )

    for oid, new in new_by_id.items():
        if oid not in old_by_id:
            availability.append(
                AvailabilityInsight(
                    offer_id=oid,
                    label=_label_for(new),
                    event="appeared",
                    price=new.get("total_price", 0.0),
                    currency=new.get("currency", ""),
                )
            )

    # Trie les baisses de prix en premier (les plus intéressantes)
    price_changes.sort(key=lambda p: p.delta)

    return InsightReport(
        session_id=session_id,
        search_type=search_type,
        snapshot_old_at=old_at,
        snapshot_new_at=new_at,
        price_changes=price_changes,
        availability=availability,
    )
