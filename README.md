# Airbnb Data Warehouse — dbt + BigQuery

![dbt](https://img.shields.io/badge/dbt-Core-FF694B?logo=dbt&logoColor=white)
![BigQuery](https://img.shields.io/badge/BigQuery-Ready-4285F4?logo=googlecloud&logoColor=white)
![DuckDB](https://img.shields.io/badge/DuckDB-Local%20Dev-FFF000?logo=duckdb&logoColor=black)
![SQL](https://img.shields.io/badge/SQL-Analytics-336791?logo=postgresql&logoColor=white)
![Tests](https://img.shields.io/badge/dbt%20tests-19%20passing-brightgreen)


## Problem statement

An Airbnb host or market analyst wants to answer: *which neighbourhoods and
listing types generate the best occupancy and price, and which hosts run the
biggest, best-performing portfolios?* The raw exports (listings, reviews,
daily calendar) are three disconnected CSVs with real-world data quality
issues — placeholder `$0` prices, missing neighbourhood tags, and orphaned
foreign keys. This project turns them into a clean, tested, query-ready
warehouse that a BI tool can sit directly on top of.

## Architecture

```
Source (Inside Airbnb CSV exports)
        |
        v
  Seeds (raw_listings, raw_reviews, raw_calendar)
        |
        v
  Staging  (stg_listings, stg_reviews, stg_calendar)
    -- type casting, null handling, $0-price cleanup
        |
        v
  Intermediate  (int_listing_review_stats, int_listing_occupancy)
    -- per-listing aggregation
        |
        v
  Marts  (mart_listing_performance, mart_neighbourhood_summary,
          mart_host_summary, mart_price_trends)
        |
        v
  BI tool (Power BI / Metabase) <-- feeds into Project 6 of the guide
```

## Tech stack

dbt Core · BigQuery (production target) · DuckDB (zero-setup local dev target) · SQL · YAML

## Repo layout

```
seeds/       raw_listings.csv, raw_reviews.csv, raw_calendar.csv (+ schema doc)
models/staging/       1:1 cleaned views over the seeds
models/intermediate/  per-listing aggregates
models/marts/         final tables for BI / analytics
generate_data.py      regenerates the synthetic seed data (swap for real Inside Airbnb data any time)
profiles.yml                  local DuckDB profile (used by default)
profiles.bigquery.yml.example production BigQuery profile — rename to go live
```

## Setup — quick start (DuckDB, no cloud account needed)

```bash
pip install dbt-core dbt-duckdb
export DBT_PROFILES_DIR=.        # use the profiles.yml in this repo
dbt seed     # load the 3 raw CSVs (300 listings / 2,203 reviews / 4,800 calendar-days)
dbt run      # build all 8 models
dbt test     # run all 19 data tests
dbt docs generate && dbt docs serve   # browse the lineage graph + column docs
```

## Setup — production (BigQuery)

```bash
pip install dbt-bigquery
gcloud auth application-default login
# create a BigQuery dataset named airbnb_dwh in your GCP project
cp profiles.bigquery.yml.example profiles.yml   # edit YOUR_GCP_PROJECT_ID
dbt seed && dbt run && dbt test
```

No models change between targets — only the profile.

## Using real data instead of the synthetic sample

The seeds ship as realistic **synthetic** data (see `generate_data.py`) so
the project runs immediately with no downloads. To swap in a real city:

1. Download `listings.csv`, `reviews.csv`, `calendar.csv` for any city from
   [insideairbnb.com/get-the-data](https://insideairbnb.com/get-the-data/)
2. Rename/trim columns to match `seeds/raw_*.csv` headers (Inside Airbnb's
   real export is a superset of what's used here)
3. Replace the files in `seeds/` and re-run `dbt seed --full-refresh`

## Data quality, on purpose

The synthetic generator seeds a few realistic issues so the test suite has
something to actually catch:

- 4 listings with a `$0` placeholder price → nulled out in `stg_listings`, tracked via `price_tier = 'unknown'`
- 6 listings with a blank `neighbourhood_group` → cleaned via `nullif(trim(...), '')`
- 3 reviews referencing a `listing_id` that doesn't exist → caught by a `relationships` test (`severity: warn`)

Running `dbt test` should show **18 pass / 1 warn** — the warn is that
orphan-review check working as intended.

## Sample output — `mart_neighbourhood_summary`

| neighbourhood_group | neighbourhood | listing_count | avg_price_usd | avg_occupancy_rate_pct |
|---|---|---:|---:|---:|
| Staten Island | Tompkinsville | 31 | 152.58 | 48.1 |
| Staten Island | St. George | 30 | 130.97 | 53.0 |
| Bronx | Fordham | 25 | 138.92 | 44.5 |
| Bronx | Mott Haven | 22 | 140.95 | 51.4 |
| Brooklyn | Park Slope | 15 | 155.80 | 55.5 |

## Sample output — `mart_price_trends`

Weekly average price and occupancy, split by room type and neighbourhood
group — built from the calendar data so pricing can be tracked over time
instead of only as a single snapshot.

| week_start_date | room_type | neighbourhood_group | avg_price_usd | occupancy_rate_pct |
|---|---|---|---:|---:|
| 2026-08-31 | Entire home/apt | Bronx | 183.73 | 50.0 |
| 2026-08-31 | Entire home/apt | Brooklyn | 243.29 | 60.4 |
| 2026-08-31 | Entire home/apt | Manhattan | 186.57 | 46.7 |
| 2026-09-07 | Entire home/apt | Bronx | 178.41 | 38.6 |

## Next steps to extend this for the portfolio

- Add a `snapshot` on `stg_listings` to track price/availability changes over time (SCD Type 2)
- Add `dbt-expectations` or Great Expectations on top for richer validation (this is Project 7 in the guide)
- Point Power BI / Metabase at `mart_listing_performance` and `mart_neighbourhood_summary` (Project 6)
- Deploy `dbt run`/`dbt test` on a GitHub Actions schedule for CI
 
