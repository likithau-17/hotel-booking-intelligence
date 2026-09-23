"""
generate_data.py
-----------------
Generates the 5 raw-Python datasets for Case Study 8 (Hospitality).

IMPORTANT: This generator deliberately injects a small, known number of
data-quality issues (duplicates, invalid references, bad dates, etc.) as
required by Section 11 of the brief ("Data Validation - Mandatory Starting
Phase"). The injected issues are logged to data/_injected_issues.txt so the
validation functions in day_1_analysis.py can be checked against a ground
truth while developing.

Run:  python generate_data.py
"""

import os
import random
import datetime
import pprint

random.seed(42)  # reproducible dataset

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# --- CONSTANTS -------------------------------------------------------------
CITIES = ["Bangalore", "Chennai", "Mumbai", "Delhi", "Hyderabad", "Pune", "Kolkata"]
HOTEL_TYPES = ["Business", "Luxury", "Resort", "Budget", "Boutique", "Airport"]
HOTEL_STATUSES = ["Active", "Active", "Active", "Inactive", "Under Renovation"]
ROOM_TYPES = ["Standard", "Deluxe", "Executive", "Suite", "Family"]
ROOM_STATUSES = ["Available", "Available", "Available", "Maintenance", "Inactive"]
GUEST_SEGMENTS = ["Premium", "Regular", "Occasional", "New", "Corporate"]
BOOKING_STATUSES = ["Confirmed", "Confirmed", "Checked-In", "Checked-Out", "Cancelled", "No-Show"]
BOOKING_CHANNELS = ["Website", "Mobile App", "Travel Agent", "Corporate", "OTA", "Walk-In"]

FIRST_NAMES = ["Ananya", "Rahul", "Priya", "Amit", "Sneha", "Vikram", "Neha", "Rohan",
               "Kavya", "Aditya", "Divya", "Karthik", "Meera", "Sanjay", "Pooja"]
LAST_NAMES = ["Rao", "Sharma", "Patel", "Singh", "Reddy", "Nair", "Gupta", "Jain",
              "Desai", "Iyer", "Menon", "Kapoor", "Chatterjee", "Pillai"]


def random_date(start_year, end_year):
    start = datetime.date(start_year, 1, 1)
    end = datetime.date(end_year, 12, 31)
    delta = end - start
    return start + datetime.timedelta(days=random.randint(0, delta.days))


issues_log = []  # human readable log of injected issues, for our own QA


# --- 1. HOTELS ---------------------------------------------------------
hotels = []
for i in range(30):
    hotel_id = 6001 + i
    h_type = random.choice(HOTEL_TYPES)
    base_rate = round(random.uniform(2000, 15000), -2)
    hotels.append({
        "hotel_id": hotel_id,
        "hotel_name": f"{random.choice(['Grand', 'Royal', 'Taj', 'The', 'City'])} "
                       f"{h_type} {random.choice(['Palace', 'Inn', 'Suites', 'Residency'])}",
        "city": random.choice(CITIES),
        "hotel_type": h_type,
        "star_rating": random.randint(3, 5),
        "hotel_rating": round(random.uniform(3.5, 4.9), 1),
        "base_room_rate": base_rate,
        "hotel_status": random.choice(HOTEL_STATUSES),
    })

# Inject: duplicate hotel record (same hotel_id appears twice)
dup_hotel = dict(hotels[3])
hotels.append(dup_hotel)
issues_log.append(f"Duplicate hotel record injected: hotel_id={dup_hotel['hotel_id']}")

# Inject: missing hotel rating (None)
hotels[7]["hotel_rating"] = None
issues_log.append(f"Missing hotel_rating injected: hotel_id={hotels[7]['hotel_id']}")

# Inject: invalid star rating (out of 1-5 range)
hotels[12]["star_rating"] = 9
issues_log.append(f"Invalid star_rating (9) injected: hotel_id={hotels[12]['hotel_id']}")

hotel_ids = [h["hotel_id"] for h in hotels]


# --- 2. GUESTS -----------------------------------------------------------
guests = []
guest_ids = []
for i in range(150):
    g_id = 7001 + i
    guest_ids.append(g_id)
    guests.append({
        "guest_id": g_id,
        "guest_name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
        "city": random.choice(CITIES),
        "signup_date": str(random_date(2023, 2025)),
        "guest_segment": random.choice(GUEST_SEGMENTS),
    })

# Inject: duplicate guest record
dup_guest = dict(guests[10])
guests.append(dup_guest)
issues_log.append(f"Duplicate guest record injected: guest_id={dup_guest['guest_id']}")


# --- 3. ROOMS --------------------------------------------------------------
rooms = []
for i in range(100):
    r_id = 8001 + i
    h_id = random.choice(hotel_ids)
    r_type = random.choice(ROOM_TYPES)
    base = next(h["base_room_rate"] for h in hotels if h["hotel_id"] == h_id)
    multiplier = {"Standard": 1.0, "Deluxe": 1.2, "Executive": 1.5, "Family": 1.8, "Suite": 2.5}[r_type]

    rooms.append({
        "room_id": r_id,
        "hotel_id": h_id,
        "room_number": f"{random.randint(1, 9)}{random.randint(0, 9)}{random.randint(1, 9)}",
        "room_type": r_type,
        "capacity": 2 if r_type in ["Standard", "Deluxe", "Executive"] else 4,
        "nightly_rate": round(base * multiplier, -2),
        "room_status": random.choice(ROOM_STATUSES),
    })

# Inject: duplicate room id
dup_room = dict(rooms[15])
rooms.append(dup_room)
issues_log.append(f"Duplicate room record injected: room_id={dup_room['room_id']}")

# Inject: room referencing an invalid (non-existent) hotel
rooms[20]["hotel_id"] = 9999
issues_log.append(f"Room with invalid hotel_id (9999) injected: room_id={rooms[20]['room_id']}")

# Inject: invalid room_type
rooms[25]["room_type"] = "Penthouse"
issues_log.append(f"Invalid room_type ('Penthouse') injected: room_id={rooms[25]['room_id']}")


# --- 4. BOOKINGS -----------------------------------------------------------
bookings = []
for i in range(600):
    b_id = 90001 + i
    guest = random.choice(guest_ids)
    room = random.choice(rooms)

    book_date = random_date(2025, 2026)
    check_in = book_date + datetime.timedelta(days=random.randint(1, 60))
    check_out = check_in + datetime.timedelta(days=random.randint(1, 14))

    bookings.append({
        "booking_id": b_id,
        "guest_id": guest,
        "hotel_id": room["hotel_id"],
        "room_id": room["room_id"],
        "booking_date": str(book_date),
        "check_in_date": str(check_in),
        "check_out_date": str(check_out),
        "booking_status": random.choice(BOOKING_STATUSES),
        "booking_channel": random.choice(BOOKING_CHANNELS),
        "adults": random.randint(1, room["capacity"]),
        "children": random.randint(0, 2) if room["capacity"] > 2 else 0,
        "discount": round(random.uniform(0, 1500), -2) if random.random() > 0.5 else 0.0,
    })

# Inject: duplicate booking_id
dup_booking = dict(bookings[50])
bookings.append(dup_booking)
issues_log.append(f"Duplicate booking_id injected: booking_id={dup_booking['booking_id']}")

# Inject: check-out before check-in
bookings[60]["check_in_date"] = "2026-05-20"
bookings[60]["check_out_date"] = "2026-05-15"
issues_log.append(f"Check-out before check-in injected: booking_id={bookings[60]['booking_id']}")

# Inject: zero-night booking
bookings[70]["check_in_date"] = "2026-06-10"
bookings[70]["check_out_date"] = "2026-06-10"
issues_log.append(f"Zero-night booking injected: booking_id={bookings[70]['booking_id']}")

# Inject: negative discount
bookings[80]["discount"] = -500.0
issues_log.append(f"Negative discount injected: booking_id={bookings[80]['booking_id']}")

# Inject: excessive discount (greater than plausible gross revenue)
bookings[90]["discount"] = 999999.0
issues_log.append(f"Excessive discount injected: booking_id={bookings[90]['booking_id']}")

# Inject: invalid guest_id reference
bookings[100]["guest_id"] = 70999
issues_log.append(f"Invalid guest_id reference injected: booking_id={bookings[100]['booking_id']}")

# Inject: invalid room_id reference
bookings[110]["room_id"] = 89999
issues_log.append(f"Invalid room_id reference injected: booking_id={bookings[110]['booking_id']}")

# Inject: invalid hotel_id reference (inconsistent with room's hotel)
bookings[120]["hotel_id"] = 9999
issues_log.append(f"Invalid hotel_id reference injected: booking_id={bookings[120]['booking_id']}")

# Inject: invalid booking_status
bookings[130]["booking_status"] = "Pending-Review"
issues_log.append(f"Invalid booking_status injected: booking_id={bookings[130]['booking_id']}")

# Inject: invalid booking_channel
bookings[140]["booking_channel"] = "Phone"
issues_log.append(f"Invalid booking_channel injected: booking_id={bookings[140]['booking_id']}")

# Inject: two bookings on the exact same date for the same guest (multiple bookings same date)
bookings[150]["guest_id"] = bookings[151]["guest_id"]
bookings[150]["booking_date"] = bookings[151]["booking_date"]
issues_log.append(
    f"Multiple bookings same date for same guest injected: "
    f"guest_id={bookings[150]['guest_id']}, booking_date={bookings[150]['booking_date']}"
)


# --- 5. GUEST PREFERENCES ---------------------------------------------------
guest_preferences = {}
preference_pool = ROOM_TYPES + HOTEL_TYPES
for g_id in guest_ids:
    guest_preferences[g_id] = random.sample(preference_pool, random.randint(2, 4))

# Inject: invalid preference value
guest_preferences[guest_ids[5]].append("Penthouse")
issues_log.append(f"Invalid preference value injected for guest_id={guest_ids[5]}")

# Inject: guest with missing preferences entirely -> remove a few guests from the dict
for gid_to_remove in guest_ids[-5:]:
    if gid_to_remove in guest_preferences:
        del guest_preferences[gid_to_remove]
issues_log.append(f"Guests with missing preferences injected: {guest_ids[-5:]}")


# --- WRITE FILES -------------------------------------------------------
def write_to_file(filename, var_name, data):
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, "w") as f:
        formatted_data = pprint.pformat(data, sort_dicts=False, width=100)
        f.write(f"{var_name} = {formatted_data}\n")
    print(f"Saved: {filepath}")


write_to_file("hotels.py", "hotels", hotels)
write_to_file("guests.py", "guests", guests)
write_to_file("rooms.py", "rooms", rooms)
write_to_file("bookings.py", "bookings", bookings)
write_to_file("guest_preferences.py", "guest_preferences", guest_preferences)

with open(os.path.join(DATA_DIR, "_injected_issues.txt"), "w") as f:
    f.write("Known data-quality issues intentionally injected into this dataset\n")
    f.write("(for validating day_1_analysis.py's validate_*() functions):\n\n")
    for line in issues_log:
        f.write(f"- {line}\n")

print(f"\nTotal records -> hotels: {len(hotels)}, guests: {len(guests)}, "
      f"rooms: {len(rooms)}, bookings: {len(bookings)}, "
      f"guest_preferences: {len(guest_preferences)}")
print("Generation complete.")
