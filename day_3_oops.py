"""
day_3_oops.py
-------------
Case Study 8 -- Hospitality: Hotel Booking Intelligence
DAY 3: OOPS -- Build a reusable Hotel Booking Intelligence System.

Class design rationale (documented, per the brief):
  - Guest, Room, Booking are plain entity classes: they hold data plus the
    small amount of behavior that belongs to a single record
    (Booking.calculate_nights(), Booking.is_successful(), etc). This is
    encapsulation -- the math for "is this booking a stay?" lives on the
    booking itself instead of being re-derived by every caller.
  - Hotel uses INHERITANCE because hotel_type meaningfully changes how a
    property should be evaluated: a BudgetHotel's "good performance" bar is
    different from a LuxuryHotel's. Rather than branching on
    `if hotel_type == "Luxury"` throughout the analytics code (which is
    what the Day 1/2 scripts effectively did with threshold constants),
    each subclass overrides `performance_threshold()` and
    `describe_segment()`. This is POLYMORPHISM: analytics code calls
    hotel.performance_threshold() without caring which subclass it has.
  - GuestPreference is a thin wrapper around the guest_preferences.py
    dict-of-lists, adding set-based membership/alignment methods so that
    "is this stay aligned with the guest's preferences" is defined in one
    place instead of being reimplemented by every analyzer.
  - BookingAnalyzer / HotelAnalyzer / GuestAnalyzer are the "service" layer:
    they hold references to collections of entities and expose the
    business-facing query methods the brief asks for
    (get_booking_summary(), get_top_hotels(), get_repeat_guests(), ...).
    Keeping this separate from the entity classes means an entity object
    never needs to know about the *other* datasets -- only the analyzer
    does the cross-dataset work, which keeps Guest/Hotel/Room/Booking
    reusable in isolation.
"""

import sys
import os
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"))

from hotels import hotels as raw_hotels
from guests import guests as raw_guests
from rooms import rooms as raw_rooms
from bookings import bookings as raw_bookings
from guest_preferences import guest_preferences as raw_guest_preferences

DATE_FMT = "%Y-%m-%d"
SUCCESSFUL_STATUSES = {"Checked-In", "Checked-Out"}


# ============================================================================
# CUSTOM EXCEPTIONS
# ============================================================================

class HospitalityDataError(Exception):
    """Base class for all Hotel Booking Intelligence data errors."""


class InvalidBookingError(HospitalityDataError):
    pass


class MissingGuestError(HospitalityDataError):
    pass


class MissingHotelError(HospitalityDataError):
    pass


class InvalidRoomError(HospitalityDataError):
    pass


class InvalidDateRangeError(HospitalityDataError):
    pass


class InvalidRevenueError(HospitalityDataError):
    pass


class InvalidDiscountError(HospitalityDataError):
    pass


# ============================================================================
# ENTITY CLASSES
# ============================================================================

class Guest:
    def __init__(self, guest_id, guest_name, city, signup_date, guest_segment):
        self.guest_id = guest_id
        self.guest_name = guest_name
        self.city = city
        self.signup_date = signup_date
        self.guest_segment = guest_segment

    def __repr__(self):
        return f"Guest({self.guest_id}, {self.guest_name!r}, segment={self.guest_segment})"


class Room:
    VALID_TYPES = {"Standard", "Deluxe", "Executive", "Suite", "Family"}

    def __init__(self, room_id, hotel_id, room_number, room_type, capacity, nightly_rate, room_status):
        if room_type not in self.VALID_TYPES:
            raise InvalidRoomError(f"Room {room_id} has invalid room_type '{room_type}'")
        self.room_id = room_id
        self.hotel_id = hotel_id
        self.room_number = room_number
        self.room_type = room_type
        self.capacity = capacity
        self.nightly_rate = nightly_rate
        self.room_status = room_status

    def __repr__(self):
        return f"Room({self.room_id}, {self.room_type}, hotel={self.hotel_id})"


class Booking:
    VALID_STATUSES = {"Confirmed", "Cancelled", "Checked-In", "Checked-Out", "No-Show"}
    VALID_CHANNELS = {"Website", "Mobile App", "Travel Agent", "Corporate", "OTA", "Walk-In"}

    def __init__(self, booking_id, guest_id, hotel_id, room_id, booking_date,
                 check_in_date, check_out_date, booking_status, booking_channel,
                 adults, children, discount, room=None):
        self.booking_id = booking_id
        self.guest_id = guest_id
        self.hotel_id = hotel_id
        self.room_id = room_id
        self.booking_date = self._parse_date(booking_date)
        self.check_in_date = self._parse_date(check_in_date)
        self.check_out_date = self._parse_date(check_out_date)

        if booking_status not in self.VALID_STATUSES:
            raise InvalidBookingError(f"Booking {booking_id}: invalid booking_status '{booking_status}'")
        if booking_channel not in self.VALID_CHANNELS:
            raise InvalidBookingError(f"Booking {booking_id}: invalid booking_channel '{booking_channel}'")
        if discount is not None and discount < 0:
            raise InvalidDiscountError(f"Booking {booking_id}: negative discount {discount}")

        self.booking_status = booking_status
        self.booking_channel = booking_channel
        self.adults = adults
        self.children = children
        self.discount = discount or 0.0
        self.room = room  # attached Room object, may be None if invalid reference

    @staticmethod
    def _parse_date(date_str):
        if not date_str or not isinstance(date_str, str):
            return None
        try:
            return datetime.strptime(date_str, DATE_FMT).date()
        except ValueError:
            return None

    def calculate_nights(self):
        if self.check_in_date is None or self.check_out_date is None:
            return None
        if self.check_out_date <= self.check_in_date:
            return None
        return (self.check_out_date - self.check_in_date).days

    def calculate_gross_revenue(self):
        nights = self.calculate_nights()
        if nights is None or self.room is None:
            return 0.0
        return self.room.nightly_rate * nights

    def calculate_net_revenue(self):
        gross = self.calculate_gross_revenue()
        net = gross - self.discount
        return max(net, 0.0)

    def calculate_discount(self):
        return self.discount

    def calculate_lead_time(self):
        if self.booking_date is None or self.check_in_date is None:
            return None
        delta = (self.check_in_date - self.booking_date).days
        return delta if delta >= 0 else None

    def is_cancelled(self):
        return self.booking_status == "Cancelled"

    def is_successful(self):
        return self.booking_status in SUCCESSFUL_STATUSES

    def __repr__(self):
        return f"Booking({self.booking_id}, guest={self.guest_id}, status={self.booking_status})"


class GuestPreference:
    VALID_TAGS = {
        "Standard", "Deluxe", "Executive", "Suite", "Family",
        "Business", "Luxury", "Resort", "Budget", "Boutique", "Airport",
    }

    def __init__(self, guest_id, preferences):
        self.guest_id = guest_id
        self.preferences = set(p for p in preferences if p in self.VALID_TAGS)

    def matches(self, characteristics):
        """True if any of `characteristics` (a set) intersects this guest's preferences."""
        return bool(self.preferences & set(characteristics))

    def is_exploratory(self, characteristics):
        return not self.matches(characteristics) and bool(self.preferences)

    def __repr__(self):
        return f"GuestPreference({self.guest_id}, {sorted(self.preferences)})"


# --- Hotel base class + subclasses (inheritance / polymorphism) -----------

class Hotel:
    """
    Base hotel entity. Subclasses override performance_threshold() and
    describe_segment() because "good performance" means something different
    per hotel type -- this is where polymorphism earns its place rather
    than being introduced for its own sake.
    """
    def __init__(self, hotel_id, hotel_name, city, hotel_type, star_rating,
                 hotel_rating, base_room_rate, hotel_status):
        self.hotel_id = hotel_id
        self.hotel_name = hotel_name
        self.city = city
        self.hotel_type = hotel_type
        self.star_rating = star_rating
        self.hotel_rating = hotel_rating
        self.base_room_rate = base_room_rate
        self.hotel_status = hotel_status

    def performance_threshold(self):
        """Minimum successful-stay rate this hotel type should hit to be a 'strong performer'."""
        return 0.35

    def describe_segment(self):
        return "General-purpose hotel"

    def __repr__(self):
        return f"{type(self).__name__}({self.hotel_id}, {self.hotel_name!r})"


class BusinessHotel(Hotel):
    def performance_threshold(self):
        return 0.40  # business travellers are expected to actually check in

    def describe_segment(self):
        return "Business hotel: weekday corporate demand"


class LuxuryHotel(Hotel):
    def performance_threshold(self):
        return 0.30  # lower volume but far higher average booking value

    def describe_segment(self):
        return "Luxury hotel: high average booking value, lower volume"


class ResortHotel(Hotel):
    def performance_threshold(self):
        return 0.30  # seasonal / leisure, more lead time and volatility

    def describe_segment(self):
        return "Resort hotel: seasonal leisure demand"


class BudgetHotel(Hotel):
    def performance_threshold(self):
        return 0.45  # budget hotels compete on volume, so a low stay rate hurts more

    def describe_segment(self):
        return "Budget hotel: high volume, price-sensitive demand"


class BoutiqueHotel(Hotel):
    def performance_threshold(self):
        return 0.30

    def describe_segment(self):
        return "Boutique hotel: niche, lower volume"


class AirportHotel(Hotel):
    def performance_threshold(self):
        return 0.40  # transit stays are usually short and confirmed close to arrival

    def describe_segment(self):
        return "Airport hotel: short-stay transit demand"


HOTEL_TYPE_CLASS_MAP = {
    "Business": BusinessHotel,
    "Luxury": LuxuryHotel,
    "Resort": ResortHotel,
    "Budget": BudgetHotel,
    "Boutique": BoutiqueHotel,
    "Airport": AirportHotel,
}


def make_hotel(record):
    """Factory function: picks the right Hotel subclass based on hotel_type."""
    cls = HOTEL_TYPE_CLASS_MAP.get(record["hotel_type"], Hotel)
    return cls(
        hotel_id=record["hotel_id"], hotel_name=record["hotel_name"], city=record["city"],
        hotel_type=record["hotel_type"], star_rating=record["star_rating"],
        hotel_rating=record.get("hotel_rating"), base_room_rate=record["base_room_rate"],
        hotel_status=record["hotel_status"],
    )


# ============================================================================
# DATA LOADING LAYER -- turns raw dicts into validated objects,
# isolating bad records with documented exception handling instead of
# letting one bad row crash the whole load.
# ============================================================================

def load_entities():
    hotel_objs, hotel_errors = {}, []
    for h in raw_hotels:
        if h["hotel_id"] in hotel_objs:
            continue  # duplicate hotel_id, skip (documented in Day 1)
        try:
            hotel_objs[h["hotel_id"]] = make_hotel(h)
        except HospitalityDataError as e:
            hotel_errors.append(str(e))

    guest_objs, guest_errors = {}, []
    for g in raw_guests:
        if g["guest_id"] in guest_objs:
            continue
        guest_objs[g["guest_id"]] = Guest(**g)

    room_objs, room_errors = {}, []
    for r in raw_rooms:
        if r["room_id"] in room_objs:
            continue
        if r["hotel_id"] not in hotel_objs:
            room_errors.append(f"Room {r['room_id']} references missing hotel {r['hotel_id']}")
            continue
        try:
            room_objs[r["room_id"]] = Room(**r)
        except InvalidRoomError as e:
            room_errors.append(str(e))

    booking_objs, booking_errors = {}, []
    for b in raw_bookings:
        if b["booking_id"] in booking_objs:
            continue
        try:
            if b["guest_id"] not in guest_objs:
                raise MissingGuestError(f"Booking {b['booking_id']}: missing guest {b['guest_id']}")
            if b["hotel_id"] not in hotel_objs:
                raise MissingHotelError(f"Booking {b['booking_id']}: missing hotel {b['hotel_id']}")
            room = room_objs.get(b["room_id"])
            if room is None:
                raise InvalidRoomError(f"Booking {b['booking_id']}: missing/invalid room {b['room_id']}")

            booking = Booking(
                booking_id=b["booking_id"], guest_id=b["guest_id"], hotel_id=b["hotel_id"],
                room_id=b["room_id"], booking_date=b["booking_date"],
                check_in_date=b["check_in_date"], check_out_date=b["check_out_date"],
                booking_status=b["booking_status"], booking_channel=b["booking_channel"],
                adults=b["adults"], children=b["children"], discount=b["discount"], room=room,
            )
            if booking.calculate_nights() is None:
                raise InvalidDateRangeError(
                    f"Booking {b['booking_id']}: invalid date range "
                    f"({b['check_in_date']} -> {b['check_out_date']})"
                )
            booking_objs[b["booking_id"]] = booking
        except HospitalityDataError as e:
            booking_errors.append(str(e))

    pref_objs = {
        gid: GuestPreference(gid, prefs)
        for gid, prefs in raw_guest_preferences.items()
        if gid in guest_objs
    }

    errors = {
        "hotels": hotel_errors, "rooms": room_errors, "bookings": booking_errors,
    }
    return hotel_objs, guest_objs, room_objs, booking_objs, pref_objs, errors


# ============================================================================
# ANALYTICS LAYER
# ============================================================================

class BookingAnalyzer:
    def __init__(self, bookings):
        self.bookings = list(bookings)

    def get_booking_summary(self):
        total = len(self.bookings)
        status_counts = defaultdict(int)
        for b in self.bookings:
            status_counts[b.booking_status] += 1
        nights = [b.calculate_nights() for b in self.bookings]
        valid_nights = [n for n in nights if n]
        net_revenue = sum(b.calculate_net_revenue() for b in self.bookings)
        return {
            "total_bookings": total,
            "status_breakdown": dict(status_counts),
            "total_net_revenue": round(net_revenue, 2),
            "average_length_of_stay": round(sum(valid_nights) / len(valid_nights), 2) if valid_nights else 0.0,
        }

    def get_cancellation_rate(self):
        total = len(self.bookings)
        if total == 0:
            return 0.0
        cancelled = sum(1 for b in self.bookings if b.is_cancelled())
        return round(cancelled / total, 4)

    def get_peak_booking_period(self):
        counts = defaultdict(int)
        for b in self.bookings:
            if b.booking_date:
                key = f"{b.booking_date.year}-{b.booking_date.month:02d}"
                counts[key] += 1
        if not counts:
            return None
        return max(counts.items(), key=lambda kv: kv[1])


class HotelAnalyzer:
    def __init__(self, hotels, bookings):
        self.hotels = hotels  # dict hotel_id -> Hotel
        self.bookings = list(bookings)

    def _per_hotel_stats(self):
        stats = {hid: {"bookings": [], } for hid in self.hotels}
        for b in self.bookings:
            if b.hotel_id in stats:
                stats[b.hotel_id]["bookings"].append(b)
        return stats

    def get_top_hotels(self, metric="revenue", top_n=10):
        stats = self._per_hotel_stats()
        scored = []
        for hid, s in stats.items():
            bs = s["bookings"]
            revenue = sum(b.calculate_net_revenue() for b in bs)
            stays = sum(1 for b in bs if b.is_successful())
            value = {"revenue": revenue, "bookings": len(bs), "stays": stays}.get(metric, revenue)
            scored.append((hid, round(value, 2)))
        scored.sort(key=lambda kv: kv[1], reverse=True)
        return scored[:top_n]

    def get_hotel_performance(self, hotel_id):
        hotel = self.hotels.get(hotel_id)
        if hotel is None:
            raise MissingHotelError(f"No hotel with id {hotel_id}")
        bs = [b for b in self.bookings if b.hotel_id == hotel_id]
        total = len(bs)
        stays = sum(1 for b in bs if b.is_successful())
        cancelled = sum(1 for b in bs if b.is_cancelled())
        revenue = sum(b.calculate_net_revenue() for b in bs)
        stay_rate = stays / total if total else 0.0
        return {
            "hotel_id": hotel_id,
            "hotel_name": hotel.hotel_name,
            "segment": hotel.describe_segment(),
            "total_bookings": total,
            "successful_stays": stays,
            "cancelled_bookings": cancelled,
            "stay_rate": round(stay_rate, 4),
            "revenue": round(revenue, 2),
            "meets_performance_threshold": stay_rate >= hotel.performance_threshold(),
            "performance_threshold_used": hotel.performance_threshold(),
        }

    def get_room_performance(self, rooms):
        stats = defaultdict(lambda: {"bookings": 0, "revenue": 0.0})
        for b in self.bookings:
            if b.room is None:
                continue
            rt = b.room.room_type
            stats[rt]["bookings"] += 1
            stats[rt]["revenue"] += b.calculate_net_revenue()
        for rt in stats:
            stats[rt]["revenue"] = round(stats[rt]["revenue"], 2)
        return dict(stats)


class GuestAnalyzer:
    def __init__(self, guests, bookings, preferences):
        self.guests = guests  # dict guest_id -> Guest
        self.bookings = list(bookings)
        self.preferences = preferences  # dict guest_id -> GuestPreference

    def _per_guest_bookings(self):
        by_guest = defaultdict(list)
        for b in self.bookings:
            by_guest[b.guest_id].append(b)
        return by_guest

    def get_top_guests(self, metric="spending", top_n=10):
        by_guest = self._per_guest_bookings()
        scored = []
        for gid, bs in by_guest.items():
            spending = sum(b.calculate_net_revenue() for b in bs)
            value = {"spending": spending, "bookings": len(bs)}.get(metric, spending)
            scored.append((gid, round(value, 2)))
        scored.sort(key=lambda kv: kv[1], reverse=True)
        return scored[:top_n]

    def get_guest_spending(self, guest_id):
        if guest_id not in self.guests:
            raise MissingGuestError(f"No guest with id {guest_id}")
        bs = [b for b in self.bookings if b.guest_id == guest_id]
        return round(sum(b.calculate_net_revenue() for b in bs), 2)

    def get_repeat_guests(self):
        by_guest = self._per_guest_bookings()
        return {gid: len(bs) for gid, bs in by_guest.items() if len(bs) > 1}

    def get_cancellation_prone_guests(self, threshold=0.30):
        by_guest = self._per_guest_bookings()
        result = {}
        for gid, bs in by_guest.items():
            if not bs:
                continue
            rate = sum(1 for b in bs if b.is_cancelled()) / len(bs)
            if rate > threshold:
                result[gid] = round(rate, 4)
        return result

    def get_preference_aligned_guests(self, hotels):
        by_guest = self._per_guest_bookings()
        aligned, exploratory = {}, {}
        for gid, bs in by_guest.items():
            pref = self.preferences.get(gid)
            if pref is None or not pref.preferences:
                continue
            aligned_count, exploratory_count = 0, 0
            for b in bs:
                if not b.is_successful() or b.room is None:
                    continue
                hotel = hotels.get(b.hotel_id)
                characteristics = {b.room.room_type}
                if hotel:
                    characteristics.add(hotel.hotel_type)
                if pref.matches(characteristics):
                    aligned_count += 1
                else:
                    exploratory_count += 1
            if aligned_count or exploratory_count:
                if aligned_count >= exploratory_count:
                    aligned[gid] = aligned_count
                else:
                    exploratory[gid] = exploratory_count
        return {"aligned": aligned, "exploratory": exploratory}


# ============================================================================
# DEMO / MAIN
# ============================================================================

def main():
    hotel_objs, guest_objs, room_objs, booking_objs, pref_objs, errors = load_entities()

    print("=" * 78)
    print("DAY 3 -- OOPS DATA LOAD REPORT")
    print("=" * 78)
    print(f"Hotels loaded: {len(hotel_objs)}  (errors: {len(errors['hotels'])})")
    print(f"Rooms loaded: {len(room_objs)}  (errors: {len(errors['rooms'])})")
    print(f"Bookings loaded: {len(booking_objs)}  (errors: {len(errors['bookings'])})")
    print(f"Guests loaded: {len(guest_objs)}")
    print(f"Guest preferences loaded: {len(pref_objs)}")
    if errors["bookings"]:
        print(f"\nSample booking load errors (first 5 of {len(errors['bookings'])}):")
        for msg in errors["bookings"][:5]:
            print(f"  - {msg}")

    bookings_list = list(booking_objs.values())

    booking_analyzer = BookingAnalyzer(bookings_list)
    hotel_analyzer = HotelAnalyzer(hotel_objs, bookings_list)
    guest_analyzer = GuestAnalyzer(guest_objs, bookings_list, pref_objs)

    print("\n" + "=" * 78)
    print("BookingAnalyzer.get_booking_summary()")
    print("=" * 78)
    print(booking_analyzer.get_booking_summary())
    print("Cancellation rate:", booking_analyzer.get_cancellation_rate())
    print("Peak booking period:", booking_analyzer.get_peak_booking_period())

    print("\n" + "=" * 78)
    print("HotelAnalyzer")
    print("=" * 78)
    top_hotels = hotel_analyzer.get_top_hotels(metric="revenue", top_n=5)
    print("Top 5 hotels by revenue:", top_hotels)
    example_hotel_id = top_hotels[0][0]
    print(f"get_hotel_performance({example_hotel_id}):",
          hotel_analyzer.get_hotel_performance(example_hotel_id))
    print("Room performance:", hotel_analyzer.get_room_performance(room_objs))

    print("\n" + "=" * 78)
    print("GuestAnalyzer")
    print("=" * 78)
    top_guests = guest_analyzer.get_top_guests(metric="spending", top_n=5)
    print("Top 5 guests by spending:", top_guests)
    example_guest_id = top_guests[0][0]
    print(f"get_guest_spending({example_guest_id}):",
          guest_analyzer.get_guest_spending(example_guest_id))
    repeat = guest_analyzer.get_repeat_guests()
    print(f"Repeat guests: {len(repeat)}")
    cancel_prone = guest_analyzer.get_cancellation_prone_guests()
    print(f"Cancellation-prone guests (>30% cancel rate): {len(cancel_prone)}")
    pref_aligned = guest_analyzer.get_preference_aligned_guests(hotel_objs)
    print(f"Preference-aligned guests: {len(pref_aligned['aligned'])}, "
          f"Exploratory-leaning guests: {len(pref_aligned['exploratory'])}")

    print("\n" + "=" * 78)
    print("POLYMORPHISM DEMO -- performance_threshold() per hotel type")
    print("=" * 78)
    seen_types = set()
    for hotel in hotel_objs.values():
        if hotel.hotel_type not in seen_types:
            seen_types.add(hotel.hotel_type)
            print(f"{type(hotel).__name__} ({hotel.hotel_name}): "
                  f"{hotel.describe_segment()}; threshold={hotel.performance_threshold()}")

    print("\n" + "=" * 78)
    print("EXCEPTION HANDLING DEMO")
    print("=" * 78)
    try:
        guest_analyzer.get_guest_spending(999999)
    except MissingGuestError as e:
        print(f"Caught expected MissingGuestError: {e}")
    try:
        hotel_analyzer.get_hotel_performance(999999)
    except MissingHotelError as e:
        print(f"Caught expected MissingHotelError: {e}")
    try:
        Room(99999, 6001, "101", "Penthouse", 2, 5000.0, "Available")
    except InvalidRoomError as e:
        print(f"Caught expected InvalidRoomError: {e}")
    try:
        Booking(99999, 7001, 6001, 8001, "2026-01-01", "2026-01-01", "2026-01-01",
                "Pending-Review", "Website", 2, 0, 0.0)
    except InvalidBookingError as e:
        print(f"Caught expected InvalidBookingError: {e}")

    return {
        "hotel_objs": hotel_objs, "guest_objs": guest_objs, "room_objs": room_objs,
        "booking_objs": booking_objs, "pref_objs": pref_objs, "errors": errors,
        "booking_analyzer": booking_analyzer, "hotel_analyzer": hotel_analyzer,
        "guest_analyzer": guest_analyzer,
    }


if __name__ == "__main__":
    main()
