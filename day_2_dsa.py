"""
day_2_dsa.py
------------
Case Study 8 -- Hospitality: Hotel Booking Intelligence
DAY 2: DSA & Algorithmic Problem Solving.

Reuses the cleaned, analysis-ready datasets produced by day_1_analysis.py
so Day 2 always works on validated data (no re-validation logic here).

Run:  python day_2_dsa.py
"""

import time
from collections import defaultdict
from datetime import date

from day_1_analysis import (
    main as run_day1,
    parse_date,
    booking_nights,
    booking_net_revenue,
    booking_gross_revenue,
    is_successful_stay,
)


# ============================================================================
# TASK 1 & 2: REUSABLE RANKING ENGINES
# ============================================================================
#
# Both engines follow the same pattern: build a per-entity metrics dict once
# (O(n) over bookings), then sort by whichever metric string was requested
# (O(k log k) where k = number of entities). This avoids re-scanning the
# bookings list once per metric.

def _guest_metric_table(guests, bookings, room_lookup):
    table = {g["guest_id"]: {
        "name": g["guest_name"], "revenue": 0.0, "booking_count": 0,
        "successful_stays": 0, "total_nights": 0, "_nights_list": [],
    } for g in guests}

    for b in bookings:
        gid = b["guest_id"]
        if gid not in table:
            continue
        t = table[gid]
        t["booking_count"] += 1
        t["revenue"] += booking_net_revenue(b, room_lookup)
        if is_successful_stay(b):
            t["successful_stays"] += 1
        nights = booking_nights(b)
        if nights:
            t["total_nights"] += nights
            t["_nights_list"].append(nights)

    for t in table.values():
        t["average_booking_value"] = round(t["revenue"] / t["booking_count"], 2) if t["booking_count"] else 0.0
        t["revenue"] = round(t["revenue"], 2)
    return table


def rank_guests(guests, bookings, room_lookup, metric="revenue", top_n=10):
    """
    metric in {"revenue", "booking_count", "successful_stays",
               "total_nights", "average_booking_value"}
    """
    table = _guest_metric_table(guests, bookings, room_lookup)
    if metric not in ("revenue", "booking_count", "successful_stays",
                       "total_nights", "average_booking_value"):
        raise ValueError(f"Unsupported metric: {metric}")
    ranked = sorted(table.items(), key=lambda kv: kv[1][metric], reverse=True)
    return ranked[:top_n]


def _hotel_metric_table(hotels, bookings, room_lookup):
    table = {h["hotel_id"]: {
        "name": h["hotel_name"], "revenue": 0.0, "bookings": 0, "stays": 0,
        "cancelled": 0, "_nights_list": [],
    } for h in hotels}

    for b in bookings:
        hid = b["hotel_id"]
        if hid not in table:
            continue
        t = table[hid]
        t["bookings"] += 1
        t["revenue"] += booking_net_revenue(b, room_lookup)
        if is_successful_stay(b):
            t["stays"] += 1
        if b["booking_status"] == "Cancelled":
            t["cancelled"] += 1
        nights = booking_nights(b)
        if nights:
            t["_nights_list"].append(nights)

    for t in table.values():
        t["cancellation_rate"] = round(t["cancelled"] / t["bookings"], 4) if t["bookings"] else 0.0
        t["average_booking_value"] = round(t["revenue"] / t["bookings"], 2) if t["bookings"] else 0.0
        t["average_length_of_stay"] = (
            round(sum(t["_nights_list"]) / len(t["_nights_list"]), 2) if t["_nights_list"] else 0.0
        )
        t["revenue"] = round(t["revenue"], 2)
    return table


def rank_hotels(hotels, bookings, room_lookup, metric="revenue", top_n=10):
    """
    metric in {"revenue", "bookings", "stays", "cancellation_rate",
               "average_booking_value", "average_length_of_stay"}
    """
    table = _hotel_metric_table(hotels, bookings, room_lookup)
    valid_metrics = {"revenue", "bookings", "stays", "cancellation_rate",
                      "average_booking_value", "average_length_of_stay"}
    if metric not in valid_metrics:
        raise ValueError(f"Unsupported metric: {metric}")
    ranked = sorted(table.items(), key=lambda kv: kv[1][metric], reverse=True)
    return ranked[:top_n]


# ============================================================================
# TASK 3: GUEST PREFERENCE ANALYSIS (sets, membership testing)
# ============================================================================

def preference_alignment_analysis(guests, bookings, rooms, hotels, guest_preferences, room_lookup):
    hotel_lookup = {h["hotel_id"]: h for h in hotels}

    aligned_guest_ids = set()
    exploratory_guest_ids = set()
    aligned_bookings, exploratory_bookings = [], []

    for b in bookings:
        if not is_successful_stay(b):
            continue
        gid = b["guest_id"]
        prefs = set(guest_preferences.get(gid, []))
        if not prefs:
            continue  # can't classify a guest with no stated preferences

        room = room_lookup.get(b["room_id"])
        hotel = hotel_lookup.get(b["hotel_id"])
        if not room or not hotel:
            continue

        characteristics = {room["room_type"], hotel["hotel_type"]}
        if characteristics & prefs:          # set intersection -> aligned
            aligned_guest_ids.add(gid)
            aligned_bookings.append(b)
        else:                                # set difference -> exploratory
            exploratory_guest_ids.add(gid)
            exploratory_bookings.append(b)

    def summarize(guest_ids, booking_subset):
        revenue = sum(booking_net_revenue(b, room_lookup) for b in booking_subset)
        nights = [booking_nights(b) for b in booking_subset if booking_nights(b)]
        return {
            "num_guests": len(guest_ids),
            "num_bookings": len(booking_subset),
            "successful_stays": len(booking_subset),  # already filtered to successful
            "total_revenue": round(revenue, 2),
            "average_booking_value": round(revenue / len(booking_subset), 2) if booking_subset else 0.0,
            "average_length_of_stay": round(sum(nights) / len(nights), 2) if nights else 0.0,
        }

    return {
        "preference_aligned": summarize(aligned_guest_ids, aligned_bookings),
        "exploratory": summarize(exploratory_guest_ids, exploratory_bookings),
        "_aligned_guest_ids": aligned_guest_ids,
        "_exploratory_guest_ids": exploratory_guest_ids,
    }


# ============================================================================
# TASK 4: GUEST BEHAVIOR CLASSIFICATION
# ============================================================================
#
# Thresholds (documented assumptions, tuned to this dataset's scale):
#   HIGH_VALUE_SPEND_THRESHOLD   = 300,000 net revenue AND >=3 successful stays
#   FREQUENT_STAYS_THRESHOLD     = successful_stays > 3
#   LONG_STAY_NIGHTS_THRESHOLD   = average_length_of_stay > 10 nights
#   CANCELLATION_PRONE_THRESHOLD = cancellation_rate > 0.30
#   Explorer = guest_id present in the "exploratory" set from Task 3.
# A guest may belong to more than one category -- these are independent tags.

HIGH_VALUE_SPEND_THRESHOLD = 300_000
HIGH_VALUE_MIN_STAYS = 3
FREQUENT_STAYS_THRESHOLD = 3
LONG_STAY_NIGHTS_THRESHOLD = 10
CANCELLATION_PRONE_THRESHOLD = 0.30


def classify_guests(guests, bookings, room_lookup, exploratory_guest_ids):
    table = _guest_metric_table(guests, bookings, room_lookup)
    # cancellation rate needs a dedicated pass
    cancels = defaultdict(int)
    totals = defaultdict(int)
    for b in bookings:
        gid = b["guest_id"]
        totals[gid] += 1
        if b["booking_status"] == "Cancelled":
            cancels[gid] += 1

    classification = defaultdict(list)
    for gid, t in table.items():
        tb = totals.get(gid, 0)
        cancel_rate = cancels.get(gid, 0) / tb if tb else 0.0
        avg_stay = (sum(t["_nights_list"]) / len(t["_nights_list"])) if t["_nights_list"] else 0.0

        if t["revenue"] >= HIGH_VALUE_SPEND_THRESHOLD and t["successful_stays"] >= HIGH_VALUE_MIN_STAYS:
            classification["high_value"].append(gid)
        if t["successful_stays"] > FREQUENT_STAYS_THRESHOLD:
            classification["frequent"].append(gid)
        if avg_stay > LONG_STAY_NIGHTS_THRESHOLD:
            classification["long_stay"].append(gid)
        if cancel_rate > CANCELLATION_PRONE_THRESHOLD:
            classification["cancellation_prone"].append(gid)
        if gid in exploratory_guest_ids:
            classification["explorer"].append(gid)

    return dict(classification)


# ============================================================================
# TASK 5: SEARCH & OPTIMIZATION -- NESTED LOOP vs DICTIONARY LOOKUP
# ============================================================================

def lookup_nested_loop(bookings, hotels, rooms):
    """O(B * (H + R)) -- for every booking, linearly scan hotels and rooms."""
    results = []
    for b in bookings:
        hotel = None
        for h in hotels:
            if h["hotel_id"] == b["hotel_id"]:
                hotel = h
                break
        room = None
        for r in rooms:
            if r["room_id"] == b["room_id"]:
                room = r
                break
        results.append((b["booking_id"], hotel, room))
    return results


def lookup_dict_based(bookings, hotels, rooms):
    """O(B + H + R) -- build lookup dicts once, then O(1) access per booking."""
    hotel_lookup = {h["hotel_id"]: h for h in hotels}
    room_lookup = {r["room_id"]: r for r in rooms}
    results = []
    for b in bookings:
        hotel = hotel_lookup.get(b["hotel_id"])
        room = room_lookup.get(b["room_id"])
        results.append((b["booking_id"], hotel, room))
    return results


def benchmark_lookup_approaches(bookings, hotels, rooms):
    t0 = time.perf_counter()
    lookup_nested_loop(bookings, hotels, rooms)
    t_nested = time.perf_counter() - t0

    t0 = time.perf_counter()
    lookup_dict_based(bookings, hotels, rooms)
    t_dict = time.perf_counter() - t0

    return {"nested_loop_seconds": t_nested, "dict_lookup_seconds": t_dict}


# ============================================================================
# TASK 6: BOOKING SEQUENCE ANALYSIS
# ============================================================================

def booking_sequence_analysis(guests, bookings, room_lookup):
    """
    For each guest: sort bookings chronologically by booking_date, then walk
    the sequence to compute gaps (in days) between consecutive bookings,
    detect consecutive same-hotel / same-room-type runs, and repeated
    cancellations.
    """
    by_guest = defaultdict(list)
    for b in bookings:
        d = parse_date(b.get("booking_date"))
        if d:
            by_guest[b["guest_id"]].append((d, b))

    guest_sequences = {}
    most_consecutive_same_hotel = (None, 0)
    shortest_gap = (None, None)  # (guest_id, gap_days)
    longest_gap = (None, None)

    for gid, entries in by_guest.items():
        entries.sort(key=lambda pair: pair[0])
        ordered_bookings = [b for _, b in entries]
        dates = [d for d, _ in entries]

        gaps = [(dates[i] - dates[i - 1]).days for i in range(1, len(dates))]

        # longest run of consecutive bookings at the same hotel
        run, best_run = 1, 1
        for i in range(1, len(ordered_bookings)):
            if ordered_bookings[i]["hotel_id"] == ordered_bookings[i - 1]["hotel_id"]:
                run += 1
                best_run = max(best_run, run)
            else:
                run = 1
        if best_run > most_consecutive_same_hotel[1]:
            most_consecutive_same_hotel = (gid, best_run)

        if gaps:
            g_min, g_max = min(gaps), max(gaps)
            if shortest_gap[1] is None or g_min < shortest_gap[1]:
                shortest_gap = (gid, g_min)
            if longest_gap[1] is None or g_max > longest_gap[1]:
                longest_gap = (gid, g_max)

        hotel_changes = sum(
            1 for i in range(1, len(ordered_bookings))
            if ordered_bookings[i]["hotel_id"] != ordered_bookings[i - 1]["hotel_id"]
        )

        room_types = []
        for b in ordered_bookings:
            room = room_lookup.get(b["room_id"])
            room_types.append(room["room_type"] if room else None)
        same_room_type_repeats = sum(
            1 for i in range(1, len(room_types))
            if room_types[i] == room_types[i - 1] and room_types[i] is not None
        )

        cancellations = sum(1 for b in ordered_bookings if b["booking_status"] == "Cancelled")

        guest_sequences[gid] = {
            "num_bookings": len(ordered_bookings),
            "gaps_days": gaps,
            "longest_consecutive_same_hotel_run": best_run,
            "hotel_changes_between_consecutive_bookings": hotel_changes,
            "same_room_type_repeat_count": same_room_type_repeats,
            "cancellation_count": cancellations,
        }

    repeatedly_cancel = sorted(
        [(gid, s["cancellation_count"]) for gid, s in guest_sequences.items() if s["cancellation_count"] > 1],
        key=lambda kv: kv[1], reverse=True,
    )
    changed_hotel_frequently = sorted(
        [(gid, s["hotel_changes_between_consecutive_bookings"]) for gid, s in guest_sequences.items()
         if s["hotel_changes_between_consecutive_bookings"] > 0],
        key=lambda kv: kv[1], reverse=True,
    )
    repeated_room_type = sorted(
        [(gid, s["same_room_type_repeat_count"]) for gid, s in guest_sequences.items()
         if s["same_room_type_repeat_count"] > 0],
        key=lambda kv: kv[1], reverse=True,
    )

    return {
        "guest_sequences": guest_sequences,
        "guest_with_most_consecutive_bookings": most_consecutive_same_hotel,
        "guest_with_shortest_gap": shortest_gap,
        "guest_with_longest_gap": longest_gap,
        "guests_who_repeatedly_cancel": repeatedly_cancel[:10],
        "guests_who_changed_hotel_frequently": changed_hotel_frequently[:10],
        "guests_who_repeat_room_type": repeated_room_type[:10],
    }


# ============================================================================
# TASK 7: PEAK BOOKING PERIOD ANALYSIS
# ============================================================================

def peak_booking_period_analysis(bookings, room_lookup):
    by_month = defaultdict(int)
    by_week = defaultdict(int)
    by_dow = defaultdict(int)
    revenue_by_month = defaultdict(float)
    cancelled_by_month = defaultdict(int)
    total_by_month = defaultdict(int)
    lead_times = []

    DOW_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    for b in bookings:
        bd = parse_date(b.get("booking_date"))
        ci = parse_date(b.get("check_in_date"))
        if bd is None:
            continue
        month_key = f"{bd.year}-{bd.month:02d}"
        week_key = f"{bd.isocalendar()[0]}-W{bd.isocalendar()[1]:02d}"
        dow_key = DOW_NAMES[bd.weekday()]

        by_month[month_key] += 1
        by_week[week_key] += 1
        by_dow[dow_key] += 1
        total_by_month[month_key] += 1

        revenue_by_month[month_key] += booking_net_revenue(b, room_lookup)
        if b["booking_status"] == "Cancelled":
            cancelled_by_month[month_key] += 1

        if ci and ci >= bd:
            lead_times.append((ci - bd).days)

    cancellation_rate_by_month = {
        m: round(cancelled_by_month[m] / total_by_month[m], 4) for m in total_by_month
    }

    peak_month = max(by_month.items(), key=lambda kv: kv[1]) if by_month else (None, 0)
    peak_cancel_month = (
        max(cancellation_rate_by_month.items(), key=lambda kv: kv[1])
        if cancellation_rate_by_month else (None, 0)
    )
    avg_lead_time = round(sum(lead_times) / len(lead_times), 2) if lead_times else 0.0

    return {
        "bookings_by_month": dict(sorted(by_month.items())),
        "bookings_by_week": dict(sorted(by_week.items())),
        "bookings_by_day_of_week": dict(by_dow),
        "revenue_by_month": {k: round(v, 2) for k, v in sorted(revenue_by_month.items())},
        "cancellation_rate_by_month": cancellation_rate_by_month,
        "average_booking_lead_time_days": avg_lead_time,
        "peak_demand_month": peak_month,
        "peak_cancellation_month": peak_cancel_month,
    }


# ============================================================================
# TASK 8: HOTEL PERFORMANCE OPTIMIZATION
# ============================================================================
#
# Thresholds (documented assumptions):
#   High revenue        = top 25% of hotels by revenue
#   High successful-stay rate = successful_stays / total_bookings > 0.35
#   High booking volume  = top 25% of hotels by booking count
#   Low booking volume    = bottom 25% of hotels by booking count
#   Low / high average booking value = below / above the median

def hotel_performance_optimization(hotels, bookings, room_lookup):
    table = _hotel_metric_table(hotels, bookings, room_lookup)
    for hid, t in table.items():
        t["stay_rate"] = round(t["stays"] / t["bookings"], 4) if t["bookings"] else 0.0

    revenues = sorted((t["revenue"] for t in table.values()), reverse=True)
    volumes = sorted((t["bookings"] for t in table.values()), reverse=True)
    avg_values = sorted(t["average_booking_value"] for t in table.values())

    def percentile(sorted_desc_list, pct):
        idx = max(0, int(len(sorted_desc_list) * pct) - 1)
        return sorted_desc_list[idx]

    high_revenue_cutoff = percentile(revenues, 0.25)
    high_volume_cutoff = percentile(volumes, 0.25)
    low_volume_cutoff = sorted(volumes)[max(0, int(len(volumes) * 0.25) - 1)]
    median_value = avg_values[len(avg_values) // 2] if avg_values else 0

    categories = defaultdict(list)
    for hid, t in table.items():
        high_revenue = t["revenue"] >= high_revenue_cutoff
        high_stay_rate = t["stay_rate"] > 0.35
        high_volume = t["bookings"] >= high_volume_cutoff
        low_volume = t["bookings"] <= low_volume_cutoff
        low_value = t["average_booking_value"] < median_value
        high_value = t["average_booking_value"] >= median_value
        high_cancel = t["cancellation_rate"] > 0.20
        low_stay_rate = t["stay_rate"] <= 0.35

        if high_revenue and high_stay_rate:
            categories["high_performer"].append(hid)
        if high_volume and low_value:
            categories["high_demand_low_revenue"].append(hid)
        if low_volume and high_value:
            categories["low_demand_high_value"].append(hid)
        if high_cancel and low_stay_rate:
            categories["at_risk"].append(hid)

    return {
        "categories": dict(categories),
        "thresholds": {
            "high_revenue_cutoff": round(high_revenue_cutoff, 2),
            "high_volume_cutoff": high_volume_cutoff,
            "low_volume_cutoff": low_volume_cutoff,
            "median_average_booking_value": round(median_value, 2),
        },
    }


# ============================================================================
# MAIN
# ============================================================================

def main():
    day1_results = run_day1()
    cleaned = day1_results["cleaned"]
    print("\n\n" + "#" * 78)
    print("DAY 2 -- DSA & ALGORITHMIC PROBLEM SOLVING")
    print("#" * 78)

    # Rebuild the same analysis-ready datasets used at the end of day 1
    from day_1_analysis import build_analysis_ready_datasets
    hotels_, guests_, rooms_, bookings_ = build_analysis_ready_datasets(cleaned)
    room_lookup = {r["room_id"]: r for r in rooms_}
    from data.guest_preferences import guest_preferences

    print("\n" + "=" * 78)
    print("TASK 1: GUEST RANKING ENGINE")
    print("=" * 78)
    for metric in ["revenue", "booking_count", "successful_stays"]:
        top3 = rank_guests(guests_, bookings_, room_lookup, metric=metric, top_n=3)
        print(f"Top 3 guests by {metric}: {[(gid, t[metric]) for gid, t in top3]}")

    print("\n" + "=" * 78)
    print("TASK 2: HOTEL RANKING ENGINE")
    print("=" * 78)
    for metric in ["revenue", "bookings", "cancellation_rate"]:
        top3 = rank_hotels(hotels_, bookings_, room_lookup, metric=metric, top_n=3)
        print(f"Top 3 hotels by {metric}: {[(hid, t[metric]) for hid, t in top3]}")

    print("\n" + "=" * 78)
    print("TASK 3: GUEST PREFERENCE ANALYSIS")
    print("=" * 78)
    pref_results = preference_alignment_analysis(
        guests_, bookings_, rooms_, day1_results["cleaned"]["hotels"], guest_preferences, room_lookup
    )
    print("Preference-aligned guests:", pref_results["preference_aligned"])
    print("Exploratory guests:", pref_results["exploratory"])

    print("\n" + "=" * 78)
    print("TASK 4: GUEST BEHAVIOR CLASSIFICATION")
    print("=" * 78)
    classification = classify_guests(guests_, bookings_, room_lookup, pref_results["_exploratory_guest_ids"])
    for cat, ids in classification.items():
        print(f"{cat}: {len(ids)} guests")

    print("\n" + "=" * 78)
    print("TASK 5: SEARCH & OPTIMIZATION -- NESTED LOOP vs DICT LOOKUP")
    print("=" * 78)
    bench = benchmark_lookup_approaches(bookings_, hotels_, rooms_)
    print(bench)
    print(
        "Nested loop: O(B*(H+R)) time, O(1) extra space. "
        "Dict lookup: O(B+H+R) time, O(H+R) extra space for the lookup dicts. "
        "At 600 bookings / 30 hotels / 100 rooms the difference is not "
        "perceptible, but dict lookup is still preferred for maintainability "
        "and correctness (single source of truth for the join key). "
        "At 10 million bookings, nested loop becomes O(n*m) and would be "
        "orders of magnitude slower / impractical; dict lookup stays linear "
        "and remains the only viable approach, though it would then also "
        "need batching/streaming due to memory pressure."
    )

    print("\n" + "=" * 78)
    print("TASK 6: BOOKING SEQUENCE ANALYSIS")
    print("=" * 78)
    seq = booking_sequence_analysis(guests_, bookings_, room_lookup)
    print("Guest with most consecutive same-hotel bookings:", seq["guest_with_most_consecutive_bookings"])
    print("Guest with shortest gap between bookings (days):", seq["guest_with_shortest_gap"])
    print("Guest with longest gap between bookings (days):", seq["guest_with_longest_gap"])
    print("Guests who repeatedly cancel (top 5):", seq["guests_who_repeatedly_cancel"][:5])
    print("Guests who changed hotel frequently (top 5):", seq["guests_who_changed_hotel_frequently"][:5])
    print("Guests who repeat room type (top 5):", seq["guests_who_repeat_room_type"][:5])

    print("\n" + "=" * 78)
    print("TASK 7: PEAK BOOKING PERIOD ANALYSIS")
    print("=" * 78)
    peak = peak_booking_period_analysis(bookings_, room_lookup)
    print("Bookings by month:", peak["bookings_by_month"])
    print("Bookings by day of week:", peak["bookings_by_day_of_week"])
    print("Average booking lead time (days):", peak["average_booking_lead_time_days"])
    print("Peak demand month:", peak["peak_demand_month"])
    print("Peak cancellation month:", peak["peak_cancellation_month"])

    print("\n" + "=" * 78)
    print("TASK 8: HOTEL PERFORMANCE OPTIMIZATION")
    print("=" * 78)
    perf_opt = hotel_performance_optimization(hotels_, bookings_, room_lookup)
    print("Thresholds used:", perf_opt["thresholds"])
    for cat, ids in perf_opt["categories"].items():
        print(f"{cat}: {ids}")

    print("\n" + "=" * 78)
    print("TASK 9: EDGE-CASE CHECKS (smoke tests)")
    print("=" * 78)
    assert booking_nights({"check_in_date": "2026-01-05", "check_out_date": "2026-01-05"}) is None
    assert booking_nights({"check_in_date": "2026-01-10", "check_out_date": "2026-01-05"}) is None
    assert booking_nights({"check_in_date": None, "check_out_date": "2026-01-05"}) is None
    assert rank_guests([], [], {}, metric="revenue", top_n=5) == []
    assert rank_hotels([], [], {}, metric="revenue", top_n=5) == []
    print("All edge-case smoke tests passed: zero/negative-night bookings, "
          "missing dates, and empty-dataset ranking all handled without "
          "raising unhandled exceptions.")

    return {
        "day1": day1_results,
        "hotels_": hotels_, "guests_": guests_, "rooms_": rooms_, "bookings_": bookings_,
        "room_lookup": room_lookup, "guest_preferences": guest_preferences,
        "pref_results": pref_results, "classification": classification,
        "sequence_analysis": seq, "peak_analysis": peak,
        "hotel_performance_optimization": perf_opt,
    }


if __name__ == "__main__":
    main()
