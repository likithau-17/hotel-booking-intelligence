# Case Study 8 — Hospitality: Hotel Booking Intelligence

A pure-Python (no Pandas / NumPy / SQL) hotel booking intelligence system
built across three stages: data validation & aggregation, DSA-driven
analysis, and an object-oriented analytics engine.

## Quick start (reproduce from a fresh clone)

Requires Python 3.8+ and the standard library only — no `pip install` needed.

```bash
git clone <this-repo-url>
cd Case_Study_08_hospitality

# 1. (Optional) Regenerate the dataset — a dataset is already committed under data/,
#    this only matters if you want a fresh/different run. Uses a fixed random
#    seed, so it always reproduces the same numbers.
python3 generate_data.py

# 2. Day 1 — validation + fundamental analysis
python3 day_1_analysis.py

# 3. Day 2 — DSA & algorithmic analysis (reruns Day 1 internally, so you'll
#    see both outputs)
python3 day_2_dsa.py

# 4. Day 3 — OOPS-based analytics engine (self-contained; loads data independently)
python3 day_3_oops.py
```

Or all three analysis stages in one shot:

```bash
python3 day_1_analysis.py && python3 day_2_dsa.py && python3 day_3_oops.py
```

Each script prints its full report to stdout. To save output instead of
scrolling: `python3 day_2_dsa.py > day2_output.txt`.

`data/__init__.py` is required (not optional) — `day_2_dsa.py` imports
`guest_preferences` as `from data.guest_preferences import ...`, which needs
`data/` to be a proper Python package.

## Project structure

```
Case_Study_08_hospitality/
├── data/
│   ├── hotels.py               # 31 records (30 unique + 1 injected duplicate)
│   ├── guests.py                # 151 records (150 unique + 1 injected duplicate)
│   ├── rooms.py                  # 101 records (100 unique + 1 injected duplicate)
│   ├── bookings.py                # 601 records (600 unique + 1 injected duplicate)
│   ├── guest_preferences.py        # dict of guest_id -> list[str]
│   └── _injected_issues.txt         # ground-truth log of deliberately injected issues
├── generate_data.py             # dataset generator (re-runnable, seeded)
├── day_1_analysis.py            # validation + fundamental aggregation
├── day_2_dsa.py                 # ranking engines, sequence analysis, complexity
├── day_3_oops.py                 # class-based analytics engine
├── README.md
└── business_insights.md
```

Run each stage independently:

```bash
python day_1_analysis.py
python day_2_dsa.py     # imports and re-runs day_1_analysis internally
python day_3_oops.py    # self-contained; loads data directly into objects
```

`day_2_dsa.py` calls `day_1_analysis.main()` and reuses its cleaned,
analysis-ready datasets rather than re-implementing validation.
`day_3_oops.py` re-loads the raw data itself, because loading data *into
objects* (with per-record exception handling) is itself part of the Day 3
deliverable.

## Approach followed

1. **Generate the dataset** (`generate_data.py`) with realistic value
   distributions, then **deliberately inject** a small, documented set of
   data-quality problems (duplicates, bad references, invalid categorical
   values, bad dates, bad discounts) so the validation phase has real
   issues to catch — mirroring how the brief describes the dataset
   ("intentionally contains a small number of data-quality issues").
2. **Day 1** builds `validate_hotels/guests/rooms/bookings/guest_preferences()`
   functions that identify and report every issue category from Section 11
   of the brief, then produces an "analysis-ready" version of the data:
   duplicates are dropped (keep-first), and bookings/rooms with broken
   references or impossible categorical values are isolated into a
   separate rejected bucket rather than hand-corrected. All Day 1 business
   aggregations (dataset profiling, booking performance, hotel/guest/room/
   channel analysis) run on this cleaned dataset.
3. **Day 2** builds reusable ranking engines (`rank_guests`, `rank_hotels`),
   set-based preference alignment analysis, a guest behavior classifier,
   a nested-loop-vs-dictionary-lookup complexity comparison, booking
   sequence analysis (gaps, consecutive-hotel runs, repeat cancellations),
   peak-period analysis, and a hotel performance segmentation model.
4. **Day 3** re-implements the same domain as classes: `Guest`, `Room`,
   `Booking`, `GuestPreference`, and a `Hotel` class hierarchy
   (`BusinessHotel`, `LuxuryHotel`, `ResortHotel`, `BudgetHotel`,
   `BoutiqueHotel`, `AirportHotel`) with `BookingAnalyzer`, `HotelAnalyzer`,
   and `GuestAnalyzer` as the analytics/service layer.

## Assumptions & data-quality decisions

- **Successful stay** = `booking_status in {Checked-In, Checked-Out}`.
  `Confirmed` bookings represent *demand* rather than a completed stay and
  are only folded in when a question specifically asks about confirmed
  demand (see `CONFIRMED_DEMAND_STATUSES` in `day_1_analysis.py`).
- **Booking nights** = `check_out_date - check_in_date`, in days. A
  booking with `check_out <= check_in`, or unparseable dates, has no valid
  night count (`None`) and is excluded from stay-length and
  revenue-per-night averages rather than being coerced to `0` or `1`
  (which would silently distort the numbers).
- **Gross revenue** = `room.nightly_rate * nights`. **Net revenue** =
  `gross - discount`, floored at `0` (a net revenue below zero would
  indicate a data error in the discount, not a real negative charge).
- **Duplicates** (same primary key) are resolved by keeping the *first*
  occurrence — we do not attempt to merge or guess which copy is
  authoritative, as the brief asks us to avoid manually correcting
  individual records.
- **Structurally invalid bookings/rooms** (invalid guest/hotel/room
  reference, invalid categorical status/channel/type, non-positive night
  count) are *isolated*, not corrected, and excluded from the
  "analysis-ready" dataset used for all business-facing numbers. The
  validation report in Day 1's console output lists every excluded
  record and the reason, so nothing is silently dropped.
- **Guests with no stated preferences** (5 guests, by construction) are
  excluded from preference-alignment / explorer classification, since
  "aligned vs. exploratory" is undefined without a preference profile.

## Thresholds used (Day 2 / Day 3), and why

| Classification | Threshold | Rationale |
|---|---|---|
| High-value guest | net spend ≥ ₹300,000 **and** ≥ 3 successful stays | Combines *value* and *repeat behaviour* so a single large one-off booking doesn't qualify a guest as "high value" |
| Frequent guest | successful stays > 3 | Above the dataset's typical 1–2 successful stays per guest |
| Long-stay guest | average length of stay > 10 nights | Roughly 30% above the overall average (~7.8 nights) |
| Cancellation-prone guest | cancellation rate > 30% | Meaningfully above the portfolio-wide cancellation rate (~16%) |
| Explorer | successful stay outside stated room-type/hotel-type preferences | Direct application of Task 3's alignment definition |
| Hotel: high revenue | top 25% of hotels by net revenue | Quartile-based, so it scales automatically if the hotel count changes |
| Hotel: high successful-stay rate | subclass-specific, see `Hotel.performance_threshold()` (0.30–0.45) | A Budget hotel competes on volume so its bar is higher; a Luxury/Resort/Boutique hotel is lower-volume by nature so its bar is lower |
| Hotel: high/low booking volume | top/bottom 25% by booking count | Quartile-based |
| Hotel: high/low average booking value | above/below the median | Median is robust to the handful of very high-value Suite/Penthouse-type outlier bookings |
| At-risk hotel | cancellation rate > 20% **and** stay rate ≤ its own threshold | Combines a clearly elevated cancellation rate with weak conversion to actual stays |

## Why these data structures

- **List of dicts** (hotels, guests, rooms, bookings) mirrors how this data
  would arrive from an API/export and keeps each record self-contained —
  natural for row-by-row validation and iteration.
- **Dict of lists** (`guest_preferences`) keyed by `guest_id` gives O(1)
  preference lookup per guest during booking-level analysis, and the list
  values are converted to `set()` at the point of use so membership tests
  and intersections (aligned vs. exploratory) are O(1) average case.
- **Dictionaries built as lookup indexes** (`hotel_lookup`, `room_lookup`)
  are constructed once per analysis pass and reused everywhere, turning
  what would otherwise be repeated O(n) linear scans into O(1) lookups —
  see Day 2 Task 5 for a direct nested-loop vs. dict-lookup comparison
  with timings.
- **`Counter`/`defaultdict`** (from `collections`) is used for every
  frequency-counting and grouping operation (bookings by status, by
  channel, by month, etc.) instead of manual `if key in dict` bookkeeping.

## Complexity analysis (Day 2, Task 5)

| Approach | Time | Space |
|---|---|---|
| Nested loop (linear scan per booking) | O(B × (H + R)) | O(1) extra |
| Dictionary lookup (build indexes once) | O(B + H + R) | O(H + R) extra |

At this dataset's scale (≈600 bookings, 30 hotels, 100 rooms) both
approaches run in well under a millisecond and the difference is not
perceptible — but the dictionary approach is still the better default:
it's a single, obvious "build the index, then look things up" pattern
that's easier to reason about and reuse across every other Day 1/2 task.
At 10 million bookings, the nested-loop approach becomes O(n·m) and would
take on the order of hours instead of seconds; the dictionary approach
stays linear, though at that scale it would also need to move off
in-memory Python lists (streaming/batched processing, or a real
database/index) to avoid holding everything in memory at once.

## OOPS class design (Day 3)

- **Entity classes** (`Guest`, `Room`, `Booking`, `GuestPreference`) hold
  the data and the *behavior that belongs to a single record* —
  `booking.calculate_nights()`, `booking.is_successful()`,
  `preference.matches(characteristics)` — so that logic is defined once
  and reused everywhere instead of being reimplemented by every analyzer
  function (this is the encapsulation the brief asks for).
- **`Hotel` uses inheritance** (`BusinessHotel`, `LuxuryHotel`,
  `ResortHotel`, `BudgetHotel`, `BoutiqueHotel`, `AirportHotel`) because
  "what counts as strong performance" genuinely differs by hotel type —
  Day 1/2 needed hard-coded threshold constants to express this; Day 3
  instead overrides `performance_threshold()` and `describe_segment()`
  per subclass, so analytics code (`HotelAnalyzer.get_hotel_performance`)
  calls the same method regardless of which subclass it holds
  (polymorphism), rather than branching on `hotel_type` internally.
- **`BookingAnalyzer` / `HotelAnalyzer` / `GuestAnalyzer`** form the
  service layer that does cross-dataset work; entity objects never need
  to know about datasets other than their own, keeping them reusable in
  isolation (e.g. a `Booking` can compute its own revenue without knowing
  anything about other guests or hotels).
- **Custom exceptions** (`MissingGuestError`, `MissingHotelError`,
  `InvalidRoomError`, `InvalidBookingError`, `InvalidDateRangeError`,
  `InvalidDiscountError`) are raised at the point a bad record is
  discovered during loading, and caught by the loader so one bad row
  doesn't crash the whole load — mirroring the same
  isolate-don't-crash philosophy used in Day 1's validation functions.

## Restrictions honored

No Pandas, NumPy, SQL, Excel formulas, or external analytics libraries are
used anywhere in this project — only `datetime` and `collections` from the
standard library (plus the ordinary Python data structures: lists, dicts,
sets, tuples).
