# Business Insights — Hotel Booking Intelligence
### Presented to: Hotel Group Business Head
### Basis: 579 of 600 bookings retained after validation (21 excluded as structurally invalid — see README/data-quality notes), 30 hotels, 150 guests, 98 valid rooms.

---

## 1. Guest Performance

- The top 5 guests by net spend (**Rohan Rao – ₹10,25,400**, **Sneha Menon –
  ₹10,19,600**, **Sanjay Jain – ₹9,78,700**, **Meera Menon – ₹9,57,300**,
  **Meera Pillai – ₹9,14,900**) are not simply the guests with the most
  bookings — they combine multiple successful stays with longer-than-average
  length of stay.
- **136 of 150 guests (≈91%) are repeat guests** (more than one booking),
  which is a strong loyalty signal at the portfolio level.
- **16 guests** meet our "high-value" bar (≥ ₹3,00,000 net spend **and**
  ≥ 3 successful stays) — this is the segment most worth protecting with
  loyalty perks.
- **35 guests (≈23%)** are cancellation-prone (cancel rate > 30%), and
  **4 guests** have *only* cancelled bookings — never once completed a
  stay. **39 guests overall** have never completed a stay, which is worth
  investigating (are these genuinely low-intent bookers, or is something
  in the booking flow letting them down?).
- What differentiates high-value guests: repeat behaviour + longer average
  stays, not just booking frequency — 3 guests booked 9 times each but
  don't necessarily lead on revenue, confirming that **frequency alone is
  a weak proxy for value**.

## 2. Hotel Performance

- **City Business Residency (Chennai)** is the clear revenue leader at
  **₹48.97L**, followed by **Grand Business Palace (Bangalore, ₹40.29L)**
  and **The Business Palace (Bangalore, ₹32.99L)** — Business-type hotels
  dominate the top of the revenue table.
- Hotels requiring attention (highest cancellation rates): **Taj Airport
  Inn – Hyderabad (36.4%)**, **Grand Business Palace (29.3%)**, **Grand
  Airport Palace (27.3%)**, and a second **Taj Airport Inn** location
  (26.7%) — Airport-type properties show up disproportionately here,
  suggesting transit bookings are more prone to last-minute cancellation
  than leisure or business bookings.
- Using hotel-type-aware performance thresholds (a Budget hotel is held to
  a higher stay-conversion bar than a Luxury hotel, since it competes on
  volume), several hotels are flagged **at-risk** — combining a high
  cancellation rate with a stay-conversion rate below their own segment's
  bar. These hotels should be reviewed first for overbooking practices,
  pricing, or guest-experience issues.
- A distinct **high-demand / low-average-value** cluster exists — hotels
  filling rooms but not maximizing revenue per booking — a pricing /
  upsell opportunity rather than a demand problem.

## 3. Room Demand

| Room type | Bookings | Revenue | Avg. booking value | Cancellation rate |
|---|---|---|---|---|
| Standard | 134 (most booked) | ₹74.49L | ₹55,593 | 13.4% |
| Executive | 122 | ₹1.06Cr | ₹87,025 | 13.9% |
| Deluxe | 114 | ₹1.04Cr | ₹90,856 | 17.5% |
| Suite | 110 | **₹1.36Cr (highest revenue)** | **₹1,24,030 (highest value)** | 16.4% |
| Family | 99 | ₹99.47L | ₹1,00,475 | **20.2% (highest cancellation)** |

- **Standard rooms drive the most volume**, but **Suites drive the most
  revenue** despite fewer bookings — a strong premium-upsell signal.
  Encouraging a portion of Standard-room demand toward Deluxe/Suite (e.g.
  targeted upgrade offers at booking time) is a direct revenue lever.
- **Family rooms cancel most often** — worth checking whether pricing,
  capacity mismatches, or refund policy are driving this.

## 4. Booking Behavior

| Channel | Bookings | Revenue | Avg. value | Cancellation rate |
|---|---|---|---|---|
| Website | 95 | **₹97.15L (highest revenue)** | ₹1,02,258 | 15.8% |
| Corporate | 87 | ₹91.88L | **₹1,05,608 (highest avg. value)** | 12.6% (lowest) |
| Travel Agent | 98 | ₹89.37L | ₹91,196 | 14.3% |
| Walk-In | 104 (most bookings) | ₹83.60L | ₹80,384 | **23.1% (highest cancellation)** |
| OTA | 103 | ₹79.48L | ₹77,162 | 14.6% |
| Mobile App | 92 | ₹78.67L | ₹85,513 | 15.2% |

- **Website bookings generate the most total revenue**, and **Corporate
  bookings carry the highest average value and the lowest cancellation
  rate** — Corporate is the most "trustworthy" channel from a revenue
  and reliability standpoint.
- **Walk-In bookings cancel most often (23.1%)** and carry the lowest
  average value — consistent with walk-ins being lower-commitment,
  price-sensitive, last-minute bookings.

## 5. Cancellation

- Portfolio-wide cancellation rate: **16.1%** (93 of 579 valid bookings).
- **Guest level:** guest **7046** cancelled 3 times — the most of any
  guest — followed by several guests with 2 cancellations each.
- **Hotel level:** **Taj Airport Inn (Hyderabad)** at 36.4% is the
  single biggest outlier — more than double the portfolio average.
- **Channel level:** **Walk-In** at 23.1% is the weakest channel;
  **Corporate** at 12.6% is the strongest.
- **Seasonality:** the month with the highest cancellation *rate* is
  **April 2026 (31.6%)** — worth checking against any operational or
  pricing changes planned for that period.

## 6. Seasonality

- Booking demand is fairly steady year-round with two visible peaks:
  **February 2026 (30 bookings)**, tied with **January 2026 and August
  2026 (30 bookings each)** — no single dominant "high season," which
  suggests demand is driven more by individual hotel/channel promotions
  than by strong seasonal travel patterns in this dataset.
- **Average booking lead time is ~31 days** — guests are typically
  booking about a month ahead of check-in, useful for setting the
  window for early-bird pricing or overbooking buffers.
- Wednesdays and Thursdays are the busiest booking days of the week;
  Mondays are the quietest.

## 7. Customer Loyalty

- **91% of guests are repeat bookers** (136 of 150) — a strong
  loyalty base to build a formal rewards program on.
- Guests **7028** shows the most consecutive same-hotel bookings, and
  several guests show repeated same-room-type bookings — evidence of
  a meaningful "regulars" segment with predictable preferences, which
  is a natural target for personalized offers (e.g. pre-selecting
  their usual room type).
- Gaps between a guest's bookings range from **same-day repeat
  bookings** up to **657 days** between stays for the guest with the
  longest gap — the loyalty base spans both frequent short-cycle
  bookers and occasional long-cycle bookers, and a one-size-fits-all
  loyalty program would likely under-serve one of these groups.

## 8. Preference Alignment

- Successful stays split almost evenly: **88 aligned stays** (64
  guests) vs. **90 exploratory stays** (67 guests) — guests are just
  as likely to try something outside their stated preferences as to
  stick with them.
- Revenue and average booking value are nearly identical between the two
  groups (₹90,107 aligned vs. ₹89,429 exploratory average booking
  value) — **exploring outside stated preferences does not come at a
  revenue cost**, so there's little downside (and some upside, in
  cross-sell terms) to actively recommending different room/hotel
  types to guests rather than only reinforcing their stated
  preferences.

---

## Business Recommendations

1. **Target the Airport-hotel cancellation problem directly.** Airport
   properties (led by Taj Airport Inn at 36.4%) show cancellation rates
   more than double the portfolio average. Investigate whether flexible
   transit-booking policies, overbooking, or pricing are the driver, and
   consider a non-refundable discounted-rate option for this segment to
   reduce cancellation exposure.

2. **Shift Walk-In demand toward pre-booked channels.** Walk-In bookings
   have both the highest cancellation rate (23.1%) and the lowest average
   value. A modest walk-in surcharge, or incentives to pre-book via the
   Website/App even a day ahead, would likely reduce cancellations and
   lift average booking value simultaneously.

3. **Use targeted upsell offers to shift Standard-room demand toward
   Suite/Deluxe.** Standard is the most-booked room type but the lowest
   average value; Suites deliver 2.2x the average booking value with a
   comparable (not higher) cancellation rate. Given preference-alignment
   data shows guests are already open to exploring outside their stated
   preferences without any revenue penalty, an active upgrade-offer flow
   at booking time is a low-risk, high-upside lever.

4. **Build a formal loyalty program on the 91% repeat-guest base**, with
   two distinct tracks: a frequent-booker track (guests with short
   inter-booking gaps and repeated same-room-type bookings) and a
   win-back / re-engagement track (guests with long gaps between stays,
   up to 657 days) — a single generic loyalty tier would under-serve one
   of these groups.

5. **Prioritize the Corporate channel for account-management investment.**
   It already has the highest average booking value and the lowest
   cancellation rate of any channel — dedicated account management or
   negotiated corporate rates should have the best ROI of any
   channel-investment option.

---

*Methodology note: "successful stay" is defined as `Checked-In` or
`Checked-Out`; `Confirmed` bookings are treated as pending demand, not a
completed stay, and are excluded from revenue/spend figures above unless
otherwise noted. Full definitions, thresholds, and validation details are
documented in `README.md`.*
