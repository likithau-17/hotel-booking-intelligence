"""
day_1_analysis.py
------------------
Case Study 8 -- Hospitality: Hotel Booking Intelligence
DAY 1: Data validation + fundamental Python analysis (lists, dicts, loops,
functions, counters, basic aggregations, cross-dataset lookups).

No Pandas / NumPy / SQL is used anywhere in this file.

Run:  python day_1_analysis.py
"""

import sys
import os
from collections import Counter, defaultdict
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"))

from hotels import hotels
from guests import guests
from rooms import rooms
from bookings import bookings
from guest_preferences import guest_preferences

DATE_FMT = "%Y-%m-%d"


def parse_date(date_str):
    """Safely parse a YYYY-MM-DD string. Returns None if invalid/missing."""
    if not date_str or not isinstance(date_str, str):
        return None
    try:
        return datetime.strptime(date_str, DATE_FMT).date()
    except ValueError:
        return None


# ============================================================================
# SECTION 11 -- DATA VALIDATION (MANDATORY STARTING PHASE)
# ============================================================================
#
# Assumptions / documented interpretation:
#   - "Duplicate" records are rows sharing the same primary key
#     (hotel_id / guest_id / room_id / booking_id). We keep the FIRST
#     occurrence and drop later duplicates -- we do not attempt to merge or
#     hand-correct individual fields.
#   - A booking's room_id / guest_id / hotel_id are "invalid" if they don't
#     exist in the corresponding master dataset.
#   - A booking's hotel_id is also flagged "inconsistent" if it disagrees
#     with the hotel_id of the room it references (should always match).
#   - Star ratings must be within 1-5 inclusive; hotel_rating must be a
#     float in 0-5 inclusive (None = missing, flagged separately).
#   - A booking is a "zero/negative-night" booking if
#     check_out_date <= check_in_date (after successful date parsing).
#   - Discount is "negative" if < 0, and "excessive" if it exceeds the
#     gross revenue computed for that booking (nightly_rate * nights).
#   - We do NOT silently overwrite bad data. validate_*() functions return
#     (clean_records, issues_dict) so downstream analysis can choose to
#     work only with clean_records while issues remain fully auditable.


def validate_hotels(hotel_list):
    issues = defaultdict(list)
    seen_ids = set()
    clean = []
    for h in hotel_list:
        hid = h.get("hotel_id")
        if hid in seen_ids:
            issues["duplicate_hotel_id"].append(hid)
            continue
        seen_ids.add(hid)

        if h.get("hotel_rating") is None:
            issues["missing_hotel_rating"].append(hid)
        elif not (0 <= h["hotel_rating"] <= 5):
            issues["invalid_hotel_rating"].append(hid)

        if not (1 <= h.get("star_rating", 0) <= 5):
            issues["invalid_star_rating"].append(hid)

        if h.get("hotel_status") not in ("Active", "Inactive", "Under Renovation"):
            issues["invalid_hotel_status"].append(hid)

        clean.append(h)
    return clean, dict(issues)


def validate_guests(guest_list):
    issues = defaultdict(list)
    seen_ids = set()
    clean = []
    for g in guest_list:
        gid = g.get("guest_id")
        if gid in seen_ids:
            issues["duplicate_guest_id"].append(gid)
            continue
        seen_ids.add(gid)

        if g.get("guest_segment") not in (
            "Premium", "Regular", "Occasional", "New", "Corporate"
        ):
            issues["invalid_guest_segment"].append(gid)

        clean.append(g)
    return clean, dict(issues)


def validate_rooms(room_list, valid_hotel_ids):
    issues = defaultdict(list)
    seen_ids = set()
    clean = []
    valid_room_types = {"Standard", "Deluxe", "Executive", "Suite", "Family"}
    for r in room_list:
        rid = r.get("room_id")
        if rid in seen_ids:
            issues["duplicate_room_id"].append(rid)
            continue
        seen_ids.add(rid)

        if r.get("hotel_id") not in valid_hotel_ids:
            issues["room_invalid_hotel_reference"].append(rid)

        if r.get("room_type") not in valid_room_types:
            issues["invalid_room_type"].append(rid)

        if r.get("room_status") not in ("Available", "Maintenance", "Inactive"):
            issues["invalid_room_status"].append(rid)

        clean.append(r)
    return clean, dict(issues)


def validate_bookings(booking_list, valid_hotel_ids, valid_guest_ids, room_lookup):
    issues = defaultdict(list)
    seen_ids = set()
    clean = []
    valid_statuses = {"Confirmed", "Cancelled", "Checked-In", "Checked-Out", "No-Show"}
    valid_channels = {"Website", "Mobile App", "Travel Agent", "Corporate", "OTA", "Walk-In"}

    for b in booking_list:
        bid = b.get("booking_id")
        if bid in seen_ids:
            issues["duplicate_booking_id"].append(bid)
            continue
        seen_ids.add(bid)

        if b.get("guest_id") not in valid_guest_ids:
            issues["invalid_guest_reference"].append(bid)

        if b.get("room_id") not in room_lookup:
            issues["invalid_room_reference"].append(bid)

        if b.get("hotel_id") not in valid_hotel_ids:
            issues["invalid_hotel_reference"].append(bid)
        elif b.get("room_id") in room_lookup and room_lookup[b["room_id"]]["hotel_id"] != b.get("hotel_id"):
            issues["hotel_room_mismatch"].append(bid)

        if b.get("booking_status") not in valid_statuses:
            issues["invalid_booking_status"].append(bid)

        if b.get("booking_channel") not in valid_channels:
            issues["invalid_booking_channel"].append(bid)

        ci, co = parse_date(b.get("check_in_date")), parse_date(b.get("check_out_date"))
        if ci is None or co is None:
            issues["unparseable_dates"].append(bid)
        elif co < ci:
            issues["checkout_before_checkin"].append(bid)
        elif co == ci:
            issues["zero_night_booking"].append(bid)

        discount = b.get("discount", 0) or 0
        if discount < 0:
            issues["negative_discount"].append(bid)
        else:
            room = room_lookup.get(b.get("room_id"))
            if room and ci and co and co > ci:
                nights = (co - ci).days
                gross = room["nightly_rate"] * nights
                if discount > gross:
                    issues["excessive_discount"].append(bid)

        clean.append(b)
    return clean, dict(issues)


def validate_guest_preferences(pref_dict, valid_guest_ids):
    issues = defaultdict(list)
    valid_prefs = {
        "Standard", "Deluxe", "Executive", "Suite", "Family",
        "Business", "Luxury", "Resort", "Budget", "Boutique", "Airport",
    }
    missing_prefs = [gid for gid in valid_guest_ids if gid not in pref_dict]
    if missing_prefs:
        issues["guests_missing_preferences"] = missing_prefs

    for gid, prefs in pref_dict.items():
        if gid not in valid_guest_ids:
            issues["preferences_for_invalid_guest"].append(gid)
        bad = [p for p in prefs if p not in valid_prefs]
        if bad:
            issues["invalid_preference_values"].append((gid, bad))

    return pref_dict, dict(issues)


def run_validation():
    valid_hotel_ids_raw = {h["hotel_id"] for h in hotels}
    valid_guest_ids_raw = {g["guest_id"] for g in guests}
    room_lookup_raw = {r["room_id"]: r for r in rooms}

    clean_hotels, hotel_issues = validate_hotels(hotels)
    clean_guests, guest_issues = validate_guests(guests)
    clean_rooms, room_issues = validate_rooms(rooms, valid_hotel_ids_raw)
    clean_bookings, booking_issues = validate_bookings(
        bookings, valid_hotel_ids_raw, valid_guest_ids_raw, room_lookup_raw
    )
    clean_prefs, pref_issues = validate_guest_preferences(guest_preferences, valid_guest_ids_raw)

    print("=" * 78)
    print("DATA VALIDATION REPORT")
    print("=" * 78)
    for name, issues in [
        ("HOTELS", hotel_issues),
        ("GUESTS", guest_issues),
        ("ROOMS", room_issues),
        ("BOOKINGS", booking_issues),
        ("GUEST_PREFERENCES", pref_issues),
    ]:
        print(f"\n[{name}]")
        if not issues:
            print("  No issues found.")
        for k, v in issues.items():
            count = len(v) if isinstance(v, list) else 1
            print(f"  - {k}: {count} record(s) -> {v}")

    return {
        "hotels": clean_hotels,
        "guests": clean_guests,
        "rooms": clean_rooms,
        "bookings": clean_bookings,
        "guest_preferences": clean_prefs,
    }


# ============================================================================
# BUSINESS DEFINITIONS (shared helpers)
# ============================================================================

SUCCESSFUL_STATUSES = {"Checked-In", "Checked-Out"}          # "actual stay" happened
CONFIRMED_DEMAND_STATUSES = {"Confirmed", "Checked-In", "Checked-Out"}  # includes confirmed demand


def booking_nights(b):
    """Return nights for a booking, or None if dates are invalid/zero/negative."""
    ci, co = parse_date(b.get("check_in_date")), parse_date(b.get("check_out_date"))
    if ci is None or co is None or co <= ci:
        return None
    return (co - ci).days


def booking_gross_revenue(b, room_lookup):
    room = room_lookup.get(b.get("room_id"))
    nights = booking_nights(b)
    if room is None or nights is None:
        return 0.0
    return room["nightly_rate"] * nights


def booking_net_revenue(b, room_lookup):
    gross = booking_gross_revenue(b, room_lookup)
    discount = b.get("discount", 0) or 0
    net = gross - discount
    return max(net, 0.0)  # a net revenue below zero is not meaningful


def is_successful_stay(b):
    return b.get("booking_status") in SUCCESSFUL_STATUSES


def is_confirmed_demand(b):
    return b.get("booking_status") in CONFIRMED_DEMAND_STATUSES


# ============================================================================
# TASK 1: DATASET PROFILING
# ============================================================================

def dataset_profile(hotels_, guests_, rooms_, bookings_):
    profile = {
        "num_hotels": len(hotels_),
        "num_guests": len(guests_),
        "num_rooms": len(rooms_),
        "num_bookings": len(bookings_),
        "guests_by_city": dict(Counter(g["city"] for g in guests_)),
        "hotels_by_city": dict(Counter(h["city"] for h in hotels_)),
        "hotels_by_type": dict(Counter(h["hotel_type"] for h in hotels_)),
        "hotels_by_star_rating": dict(Counter(h["star_rating"] for h in hotels_)),
        "rooms_by_type": dict(Counter(r["room_type"] for r in rooms_)),
        "guests_by_segment": dict(Counter(g["guest_segment"] for g in guests_)),
        "bookings_by_status": dict(Counter(b["booking_status"] for b in bookings_)),
        "bookings_by_channel": dict(Counter(b["booking_channel"] for b in bookings_)),
    }

    hotel_lookup = {h["hotel_id"]: h for h in hotels_}
    room_lookup = {r["room_id"]: r for r in rooms_}

    bookings_by_hotel = Counter(b["hotel_id"] for b in bookings_)
    bookings_by_room_type = Counter(
        room_lookup[b["room_id"]]["room_type"] for b in bookings_ if b["room_id"] in room_lookup
    )
    bookings_by_city = Counter(
        hotel_lookup[b["hotel_id"]]["city"] for b in bookings_ if b["hotel_id"] in hotel_lookup
    )
    bookings_by_channel2 = Counter(b["booking_channel"] for b in bookings_)

    profile["bookings_by_hotel"] = dict(bookings_by_hotel)
    profile["bookings_by_room_type"] = dict(bookings_by_room_type)
    profile["bookings_by_city"] = dict(bookings_by_city)
    profile["bookings_by_channel_check"] = dict(bookings_by_channel2)
    return profile


# ============================================================================
# TASK 2: BOOKING PERFORMANCE ANALYSIS
# ============================================================================

def booking_performance(bookings_, room_lookup):
    total = len(bookings_)
    status_counts = Counter(b["booking_status"] for b in bookings_)
    confirmed = status_counts.get("Confirmed", 0)
    cancelled = status_counts.get("Cancelled", 0)
    checked_in = status_counts.get("Checked-In", 0)
    checked_out = status_counts.get("Checked-Out", 0)
    no_show = status_counts.get("No-Show", 0)

    cancellation_rate = cancelled / total if total else 0.0

    nights_list = [booking_nights(b) for b in bookings_]
    valid_nights = [n for n in nights_list if n is not None]
    total_nights = sum(valid_nights)
    avg_stay = total_nights / len(valid_nights) if valid_nights else 0.0

    gross_list = [booking_gross_revenue(b, room_lookup) for b in bookings_]
    discount_list = [b.get("discount", 0) or 0 for b in bookings_]
    net_list = [booking_net_revenue(b, room_lookup) for b in bookings_]

    total_gross = sum(gross_list)
    total_discount = sum(discount_list)
    total_net = sum(net_list)
    avg_booking_revenue = total_net / total if total else 0.0

    rev_per_night = [
        booking_net_revenue(b, room_lookup) / n
        for b, n in zip(bookings_, nights_list) if n
    ]
    avg_rev_per_night = sum(rev_per_night) / len(rev_per_night) if rev_per_night else 0.0

    successful = sum(1 for b in bookings_ if is_successful_stay(b))
    pct_actual_stay = successful / total * 100 if total else 0.0

    return {
        "total_bookings": total,
        "confirmed_bookings": confirmed,
        "cancelled_bookings": cancelled,
        "checked_in_bookings": checked_in,
        "checked_out_bookings": checked_out,
        "no_show_bookings": no_show,
        "cancellation_rate": round(cancellation_rate, 4),
        "total_booking_nights": total_nights,
        "average_length_of_stay": round(avg_stay, 2),
        "total_gross_revenue": round(total_gross, 2),
        "total_discount": round(total_discount, 2),
        "total_net_revenue": round(total_net, 2),
        "average_booking_revenue": round(avg_booking_revenue, 2),
        "average_revenue_per_night": round(avg_rev_per_night, 2),
        "pct_bookings_resulting_in_actual_stay": round(pct_actual_stay, 2),
    }


# ============================================================================
# TASK 3: HOTEL ANALYSIS
# ============================================================================

def hotel_analysis(hotels_, bookings_, room_lookup):
    stats = {h["hotel_id"]: {
        "hotel_name": h["hotel_name"],
        "hotel_rating": h.get("hotel_rating"),
        "total_bookings": 0, "successful_stays": 0, "cancelled_bookings": 0,
        "no_show_bookings": 0, "total_room_nights": 0, "total_revenue": 0.0,
        "_revenue_values": [], "_nights_values": [],
    } for h in hotels_}

    for b in bookings_:
        hid = b["hotel_id"]
        if hid not in stats:
            continue
        s = stats[hid]
        s["total_bookings"] += 1
        if is_successful_stay(b):
            s["successful_stays"] += 1
        if b["booking_status"] == "Cancelled":
            s["cancelled_bookings"] += 1
        if b["booking_status"] == "No-Show":
            s["no_show_bookings"] += 1

        nights = booking_nights(b)
        net = booking_net_revenue(b, room_lookup)
        s["total_revenue"] += net
        s["_revenue_values"].append(net)
        if nights:
            s["total_room_nights"] += nights
            s["_nights_values"].append(nights)

    for hid, s in stats.items():
        tb = s["total_bookings"]
        s["cancellation_rate"] = round(s["cancelled_bookings"] / tb, 4) if tb else 0.0
        s["average_booking_value"] = round(sum(s["_revenue_values"]) / tb, 2) if tb else 0.0
        s["average_length_of_stay"] = (
            round(sum(s["_nights_values"]) / len(s["_nights_values"]), 2) if s["_nights_values"] else 0.0
        )
        s["total_revenue"] = round(s["total_revenue"], 2)
        del s["_revenue_values"]
        del s["_nights_values"]

    return stats


def hotel_insights(hotel_stats):
    ranked_by_revenue = sorted(hotel_stats.items(), key=lambda kv: kv[1]["total_revenue"], reverse=True)
    ranked_by_stays = sorted(hotel_stats.items(), key=lambda kv: kv[1]["successful_stays"], reverse=True)
    ranked_by_rating = sorted(
        [(hid, s) for hid, s in hotel_stats.items() if s["hotel_rating"] is not None],
        key=lambda kv: kv[1]["hotel_rating"], reverse=True
    )
    ranked_by_cancel = sorted(hotel_stats.items(), key=lambda kv: kv[1]["cancellation_rate"], reverse=True)

    avg_volume = sum(s["total_bookings"] for s in hotel_stats.values()) / len(hotel_stats)
    avg_value = sum(s["average_booking_value"] for s in hotel_stats.values()) / len(hotel_stats)

    high_rev_low_vol = [
        (hid, s) for hid, s in hotel_stats.items()
        if s["total_revenue"] > 0 and s["total_bookings"] < avg_volume and s["average_booking_value"] > avg_value
    ]
    high_vol_low_value = [
        (hid, s) for hid, s in hotel_stats.items()
        if s["total_bookings"] > avg_volume and s["average_booking_value"] < avg_value
    ]

    return {
        "top_10_by_revenue": ranked_by_revenue[:10],
        "top_10_by_stays": ranked_by_stays[:10],
        "highest_rated": ranked_by_rating[:10],
        "highest_cancellation_rate": ranked_by_cancel[:10],
        "high_revenue_low_volume": high_rev_low_vol,
        "high_volume_low_value": high_vol_low_value,
    }


# ============================================================================
# TASK 4: GUEST ANALYSIS
# ============================================================================

def guest_analysis(guests_, bookings_, room_lookup):
    stats = {g["guest_id"]: {
        "guest_name": g["guest_name"], "total_bookings": 0, "successful_stays": 0,
        "cancelled_bookings": 0, "total_nights_stayed": 0, "total_spending": 0.0,
        "_revenue_values": [], "_nights_values": [],
    } for g in guests_}

    for b in bookings_:
        gid = b["guest_id"]
        if gid not in stats:
            continue
        s = stats[gid]
        s["total_bookings"] += 1
        if is_successful_stay(b):
            s["successful_stays"] += 1
            nights = booking_nights(b)
            if nights:
                s["total_nights_stayed"] += nights
        if b["booking_status"] == "Cancelled":
            s["cancelled_bookings"] += 1

        net = booking_net_revenue(b, room_lookup)
        s["total_spending"] += net
        s["_revenue_values"].append(net)
        nights_any = booking_nights(b)
        if nights_any:
            s["_nights_values"].append(nights_any)

    for gid, s in stats.items():
        tb = s["total_bookings"]
        s["average_booking_value"] = round(sum(s["_revenue_values"]) / tb, 2) if tb else 0.0
        s["average_length_of_stay"] = (
            round(sum(s["_nights_values"]) / len(s["_nights_values"]), 2) if s["_nights_values"] else 0.0
        )
        s["total_spending"] = round(s["total_spending"], 2)
        del s["_revenue_values"]
        del s["_nights_values"]

    return stats


def guest_insights(guest_stats):
    top_spenders = sorted(guest_stats.items(), key=lambda kv: kv[1]["total_spending"], reverse=True)[:10]
    top_bookers = sorted(guest_stats.items(), key=lambda kv: kv[1]["total_bookings"], reverse=True)[:10]
    repeat_guests = [(gid, s) for gid, s in guest_stats.items() if s["total_bookings"] > 1]
    only_cancelled = [
        (gid, s) for gid, s in guest_stats.items()
        if s["total_bookings"] > 0 and s["cancelled_bookings"] == s["total_bookings"]
    ]
    never_stayed = [(gid, s) for gid, s in guest_stats.items() if s["total_bookings"] > 0 and s["successful_stays"] == 0]

    stay_values = [s["average_length_of_stay"] for s in guest_stats.values() if s["average_length_of_stay"] > 0]
    if stay_values:
        mean_stay = sum(stay_values) / len(stay_values)
        threshold = mean_stay * 2  # "unusually long" = more than double the population average
    else:
        threshold = 0
    unusually_long_stay = [
        (gid, s) for gid, s in guest_stats.items() if s["average_length_of_stay"] > threshold
    ]

    return {
        "top_10_spenders": top_spenders,
        "top_10_by_bookings": top_bookers,
        "repeat_guests_count": len(repeat_guests),
        "guests_only_cancelled": only_cancelled,
        "guests_never_completed_stay": never_stayed,
        "unusually_long_stay_threshold_nights": round(threshold, 2),
        "unusually_long_stay_guests": unusually_long_stay,
    }


# ============================================================================
# TASK 5: ROOM (ROOM-TYPE) ANALYSIS
# ============================================================================

def room_type_analysis(rooms_, bookings_, room_lookup):
    room_types = sorted({r["room_type"] for r in rooms_})
    stats = {rt: {
        "num_rooms": 0, "num_bookings": 0, "num_successful_stays": 0,
        "total_room_nights": 0, "revenue": 0.0, "_rates": [], "_revenue_values": [],
        "_nights_values": [],
    } for rt in room_types}

    for r in rooms_:
        stats[r["room_type"]]["num_rooms"] += 1
        stats[r["room_type"]]["_rates"].append(r["nightly_rate"])

    for b in bookings_:
        room = room_lookup.get(b["room_id"])
        if not room:
            continue
        rt = room["room_type"]
        if rt not in stats:
            continue
        s = stats[rt]
        s["num_bookings"] += 1
        if is_successful_stay(b):
            s["num_successful_stays"] += 1
        nights = booking_nights(b)
        net = booking_net_revenue(b, room_lookup)
        s["revenue"] += net
        s["_revenue_values"].append(net)
        if nights:
            s["total_room_nights"] += nights
            s["_nights_values"].append(nights)
        if b["booking_status"] == "Cancelled":
            s.setdefault("_cancelled", 0)
            s["_cancelled"] = s.get("_cancelled", 0) + 1

    for rt, s in stats.items():
        s["average_nightly_rate"] = round(sum(s["_rates"]) / len(s["_rates"]), 2) if s["_rates"] else 0.0
        s["average_booking_value"] = (
            round(sum(s["_revenue_values"]) / s["num_bookings"], 2) if s["num_bookings"] else 0.0
        )
        s["average_length_of_stay"] = (
            round(sum(s["_nights_values"]) / len(s["_nights_values"]), 2) if s["_nights_values"] else 0.0
        )
        s["cancellation_rate"] = round(s.get("_cancelled", 0) / s["num_bookings"], 4) if s["num_bookings"] else 0.0
        s["revenue"] = round(s["revenue"], 2)
        for k in ("_rates", "_revenue_values", "_nights_values", "_cancelled"):
            s.pop(k, None)

    return stats


def room_type_insights(room_stats):
    most_popular = max(room_stats.items(), key=lambda kv: kv[1]["num_bookings"])
    highest_revenue = max(room_stats.items(), key=lambda kv: kv[1]["revenue"])
    highest_cancel = max(room_stats.items(), key=lambda kv: kv[1]["cancellation_rate"])
    longest_stay = max(room_stats.items(), key=lambda kv: kv[1]["average_length_of_stay"])
    return {
        "most_popular_room_type": most_popular,
        "highest_revenue_room_type": highest_revenue,
        "highest_cancellation_room_type": highest_cancel,
        "longest_avg_stay_room_type": longest_stay,
    }


# ============================================================================
# TASK 6: BOOKING CHANNEL ANALYSIS
# ============================================================================

def channel_analysis(bookings_, room_lookup):
    channels = sorted({b["booking_channel"] for b in bookings_})
    stats = {c: {
        "total_bookings": 0, "successful_stays": 0, "cancelled": 0,
        "revenue": 0.0, "_revenue_values": [], "_nights_values": [],
    } for c in channels}

    for b in bookings_:
        c = b["booking_channel"]
        if c not in stats:
            continue
        s = stats[c]
        s["total_bookings"] += 1
        if is_successful_stay(b):
            s["successful_stays"] += 1
        if b["booking_status"] == "Cancelled":
            s["cancelled"] += 1
        net = booking_net_revenue(b, room_lookup)
        s["revenue"] += net
        s["_revenue_values"].append(net)
        nights = booking_nights(b)
        if nights:
            s["_nights_values"].append(nights)

    for c, s in stats.items():
        tb = s["total_bookings"]
        s["cancellation_rate"] = round(s["cancelled"] / tb, 4) if tb else 0.0
        s["average_booking_value"] = round(sum(s["_revenue_values"]) / tb, 2) if tb else 0.0
        s["average_stay"] = (
            round(sum(s["_nights_values"]) / len(s["_nights_values"]), 2) if s["_nights_values"] else 0.0
        )
        s["revenue"] = round(s["revenue"], 2)
        del s["_revenue_values"]
        del s["_nights_values"]

    return stats


def channel_insights(channel_stats):
    highest_revenue_channel = max(channel_stats.items(), key=lambda kv: kv[1]["revenue"])
    highest_cancel_channel = max(channel_stats.items(), key=lambda kv: kv[1]["cancellation_rate"])
    return {
        "highest_revenue_channel": highest_revenue_channel,
        "highest_cancellation_channel": highest_cancel_channel,
    }


# ============================================================================
# MAIN
# ============================================================================

def build_analysis_ready_datasets(cleaned):
    """
    Beyond de-duplication (handled inside validate_*), business analysis
    should not be skewed by records that reference things which don't
    exist, or that carry impossible categorical values. Rather than
    hand-correcting individual rows (explicitly disallowed by the brief),
    we isolate them into a separate 'rejected' bucket and analyze only the
    remaining, structurally-sound records. Every rejected record is still
    fully visible in the validation report above -- nothing is silently
    discarded without a trace.
    """
    hotels_ = cleaned["hotels"]
    guests_ = cleaned["guests"]
    rooms_ = cleaned["rooms"]
    bookings_ = cleaned["bookings"]

    valid_hotel_ids = {h["hotel_id"] for h in hotels_}
    valid_guest_ids = {g["guest_id"] for g in guests_}
    valid_room_types = {"Standard", "Deluxe", "Executive", "Suite", "Family"}
    rooms_clean = [r for r in rooms_ if r["hotel_id"] in valid_hotel_ids and r["room_type"] in valid_room_types]
    valid_room_ids = {r["room_id"] for r in rooms_clean}

    valid_statuses = {"Confirmed", "Cancelled", "Checked-In", "Checked-Out", "No-Show"}
    valid_channels = {"Website", "Mobile App", "Travel Agent", "Corporate", "OTA", "Walk-In"}

    bookings_clean = []
    rejected_bookings = []
    for b in bookings_:
        ci, co = parse_date(b.get("check_in_date")), parse_date(b.get("check_out_date"))
        ok = (
            b.get("guest_id") in valid_guest_ids
            and b.get("hotel_id") in valid_hotel_ids
            and b.get("room_id") in valid_room_ids
            and b.get("booking_status") in valid_statuses
            and b.get("booking_channel") in valid_channels
            and ci is not None and co is not None and co > ci
        )
        (bookings_clean if ok else rejected_bookings).append(b)

    print(f"\n[ANALYSIS-READY FILTER] {len(bookings_clean)} of {len(bookings_)} "
          f"bookings retained for business analysis; "
          f"{len(rejected_bookings)} rejected as structurally invalid "
          f"(see validation report above for reasons).")

    return hotels_, guests_, rooms_clean, bookings_clean


def main():
    cleaned = run_validation()
    hotels_, guests_, rooms_, bookings_ = build_analysis_ready_datasets(cleaned)

    room_lookup = {r["room_id"]: r for r in rooms_}

    print("\n" + "=" * 78)
    print("TASK 1: DATASET PROFILING")
    print("=" * 78)
    profile = dataset_profile(hotels_, guests_, rooms_, bookings_)
    for k, v in profile.items():
        print(f"{k}: {v}")

    print("\n" + "=" * 78)
    print("TASK 2: BOOKING PERFORMANCE ANALYSIS")
    print("=" * 78)
    perf = booking_performance(bookings_, room_lookup)
    for k, v in perf.items():
        print(f"{k}: {v}")
    print(
        "\nInterpretation: an 'actual hotel stay' = booking_status in "
        "{Checked-In, Checked-Out}. Confirmed-but-not-yet-arrived bookings "
        "represent demand, not a completed stay, so they are excluded here."
    )

    print("\n" + "=" * 78)
    print("TASK 3: HOTEL ANALYSIS")
    print("=" * 78)
    h_stats = hotel_analysis(hotels_, bookings_, room_lookup)
    h_ins = hotel_insights(h_stats)
    print("Top 5 hotels by revenue:")
    for hid, s in h_ins["top_10_by_revenue"][:5]:
        print(f"  {hid} ({s['hotel_name']}): revenue={s['total_revenue']}")
    print("Top 5 hotels by highest cancellation rate:")
    for hid, s in h_ins["highest_cancellation_rate"][:5]:
        print(f"  {hid} ({s['hotel_name']}): cancellation_rate={s['cancellation_rate']}")

    print("\n" + "=" * 78)
    print("TASK 4: GUEST ANALYSIS")
    print("=" * 78)
    g_stats = guest_analysis(guests_, bookings_, room_lookup)
    g_ins = guest_insights(g_stats)
    print("Top 5 guests by spending:")
    for gid, s in g_ins["top_10_spenders"][:5]:
        print(f"  {gid} ({s['guest_name']}): spending={s['total_spending']}")
    print(f"Repeat guests (>1 booking): {g_ins['repeat_guests_count']}")
    print(f"Guests with only cancelled bookings: {len(g_ins['guests_only_cancelled'])}")
    print(f"Guests who never completed a stay: {len(g_ins['guests_never_completed_stay'])}")

    print("\n" + "=" * 78)
    print("TASK 5: ROOM-TYPE ANALYSIS")
    print("=" * 78)
    r_stats = room_type_analysis(rooms_, bookings_, room_lookup)
    for rt, s in r_stats.items():
        print(f"{rt}: {s}")
    r_ins = room_type_insights(r_stats)
    for k, v in r_ins.items():
        print(f"{k}: {v[0]}")

    print("\n" + "=" * 78)
    print("TASK 6: BOOKING CHANNEL ANALYSIS")
    print("=" * 78)
    c_stats = channel_analysis(bookings_, room_lookup)
    for c, s in c_stats.items():
        print(f"{c}: {s}")
    c_ins = channel_insights(c_stats)
    print(f"Highest revenue channel: {c_ins['highest_revenue_channel']}")
    print(f"Highest cancellation channel: {c_ins['highest_cancellation_channel']}")

    return {
        "cleaned": cleaned,
        "profile": profile,
        "performance": perf,
        "hotel_stats": h_stats,
        "hotel_insights": h_ins,
        "guest_stats": g_stats,
        "guest_insights": g_ins,
        "room_stats": r_stats,
        "room_insights": r_ins,
        "channel_stats": c_stats,
        "channel_insights": c_ins,
    }


if __name__ == "__main__":
    main()
