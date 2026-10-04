"""
Generates synthetic sample data shaped exactly like the real Inside Airbnb
export (https://insideairbnb.com/get-the-data/) so the dbt project runs
out of the box. Swap these seed CSVs for a real city's Inside Airbnb export
when you want to work with real data -- the schema matches, so no model
changes are needed.
"""
import csv
import random
from datetime import date, timedelta

random.seed(42)

NEIGHBOURHOOD_GROUPS = {
    "Manhattan": ["Harlem", "Chelsea", "East Village", "Upper West Side", "Midtown"],
    "Brooklyn": ["Williamsburg", "Bushwick", "Park Slope", "Bedford-Stuyvesant", "Greenpoint"],
    "Queens": ["Astoria", "Long Island City", "Flushing", "Ridgewood"],
    "Bronx": ["Mott Haven", "Fordham", "Riverdale"],
    "Staten Island": ["St. George", "Tompkinsville"],
}
ROOM_TYPES = ["Entire home/apt", "Private room", "Shared room", "Hotel room"]
FIRST_NAMES = ["Aisha", "Raj", "Maria", "Liam", "Wei", "Fatima", "Carlos", "Emma",
               "Noah", "Priya", "Yuki", "Omar", "Sofia", "Ethan", "Ananya", "Lucas"]

N_HOSTS = 120
N_LISTINGS = 300
N_REVIEWS = 2200
CALENDAR_DAYS = 60
TODAY = date(2026, 9, 1)

hosts = [(1000 + i, f"{random.choice(FIRST_NAMES)}{i}") for i in range(N_HOSTS)]

listings = []
for lid in range(1, N_LISTINGS + 1):
    host_id, host_name = random.choice(hosts)
    group = random.choice(list(NEIGHBOURHOOD_GROUPS.keys()))
    neighbourhood = random.choice(NEIGHBOURHOOD_GROUPS[group])
    room_type = random.choices(ROOM_TYPES, weights=[55, 35, 7, 3])[0]
    base_price = {"Entire home/apt": 180, "Private room": 90,
                  "Shared room": 45, "Hotel room": 220}[room_type]
    price = max(25, int(random.gauss(base_price, base_price * 0.35)))
    number_of_reviews = random.randint(0, 180)
    has_reviews = number_of_reviews > 0
    last_review = (TODAY - timedelta(days=random.randint(1, 700))).isoformat() if has_reviews else ""
    reviews_per_month = round(random.uniform(0.01, 4.5), 2) if has_reviews else 0.0
    listings.append({
        "listing_id": lid,
        "host_id": host_id,
        "host_name": host_name,
        "neighbourhood_group": group,
        "neighbourhood": neighbourhood,
        "latitude": round(40.55 + random.random() * 0.35, 6),
        "longitude": round(-74.05 + random.random() * 0.35, 6),
        "room_type": room_type,
        "price": price,
        "minimum_nights": random.choice([1, 1, 2, 3, 5, 7, 30]),
        "number_of_reviews": number_of_reviews,
        "last_review": last_review,
        "reviews_per_month": reviews_per_month,
        "calculated_host_listings_count": None,  # filled below
        "availability_365": random.randint(0, 365),
    })

host_counts = {}
for l in listings:
    host_counts[l["host_id"]] = host_counts.get(l["host_id"], 0) + 1
for l in listings:
    l["calculated_host_listings_count"] = host_counts[l["host_id"]]

# a few intentional data-quality gaps, same as real Inside Airbnb exports,
# so the dbt tests in this project have something real to catch
for l in random.sample(listings, 6):
    l["neighbourhood_group"] = ""
for l in random.sample(listings, 4):
    l["price"] = 0

with open("seeds/raw_listings.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(listings[0].keys()))
    w.writeheader()
    w.writerows(listings)

reviewers = [(2000 + i, f"{random.choice(FIRST_NAMES)}") for i in range(400)]
reviews = []
review_id = 1
weighted_listings = [l for l in listings for _ in range(l["number_of_reviews"] or 0)]
for _ in range(N_REVIEWS):
    if not weighted_listings:
        break
    listing = random.choice(weighted_listings)
    reviewer_id, reviewer_name = random.choice(reviewers)
    review_date = TODAY - timedelta(days=random.randint(1, 730))
    reviews.append({
        "review_id": review_id,
        "listing_id": listing["listing_id"],
        "review_date": review_date.isoformat(),
        "reviewer_id": reviewer_id,
        "reviewer_name": reviewer_name,
    })
    review_id += 1

# a handful of orphan reviews pointing at a listing_id that doesn't exist,
# to give the referential-integrity test something to flag
for _ in range(3):
    reviews.append({
        "review_id": review_id,
        "listing_id": 99999,
        "review_date": (TODAY - timedelta(days=10)).isoformat(),
        "reviewer_id": 2001,
        "reviewer_name": "Ghost",
    })
    review_id += 1

with open("seeds/raw_reviews.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(reviews[0].keys()))
    w.writeheader()
    w.writerows(reviews)

calendar_rows = []
sample_listings = random.sample(listings, 80)  # keep calendar seed a manageable size
for l in sample_listings:
    for d in range(CALENDAR_DAYS):
        day = TODAY + timedelta(days=d)
        available = random.random() > (l["availability_365"] / 365 * -1 + 1) * 0 + random.uniform(0.3, 0.7)
        calendar_rows.append({
            "listing_id": l["listing_id"],
            "date": day.isoformat(),
            "available": "t" if available else "f",
            "price": max(20, int(l["price"] * random.uniform(0.9, 1.3))),
        })

with open("seeds/raw_calendar.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(calendar_rows[0].keys()))
    w.writeheader()
    w.writerows(calendar_rows)

print(f"listings={len(listings)} reviews={len(reviews)} calendar_rows={len(calendar_rows)}")
