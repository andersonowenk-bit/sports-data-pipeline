# NFL Data Pipeline

A scheduled data pipeline that ingests NFL game results every morning, lands them as immutable Parquet files, loads them into a DuckDB warehouse, and validates them before they are queryable.

Built to run unattended. The daily job has been running since August 2026.

<!-- Once you have the dashboard live, replace this line with the link.
     Once you have a screenshot, put it right here, above the fold. -->

**Status:** ingestion running daily | warehouse in progress

---

## Why this exists

Most portfolio pipelines run once against a static CSV. This one runs on a schedule against a live API, which means it has to handle the things real pipelines handle: reruns, missing days, upstream schema changes, and games that are still in progress when the job fires.

## How it works

```
ESPN Scoreboard API
        |
        v
   ingest job          (GitHub Actions, daily 12:00 UTC)
        |
        v
   data/raw/nfl/       (Parquet, one file per date, never modified)
        |
        v
   DuckDB warehouse    (incremental load, deduplicated on event_id)
        |
        v
   quality checks      (job fails if any check fails)
```

The job runs at 12:00 UTC, which is 7:00am Central, and pulls the previous day's slate. Raw files are written once and never edited, so the warehouse can always be rebuilt from scratch.

## Data source

ESPN's public scoreboard endpoint. No API key, no authentication, no rate limit issues at one request per day.

```
GET https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates=YYYYMMDD
```

## Schema

| Column | Type | Notes |
| --- | --- | --- |
| `event_id` | string | Primary key, stable across reruns |
| `event_date` | timestamp | Kickoff, UTC |
| `status` | string | `STATUS_FINAL`, `STATUS_IN_PROGRESS`, `STATUS_SCHEDULED` |
| `home_team` | string | Full display name |
| `away_team` | string | Full display name |
| `home_score` | integer | Null until the game starts |
| `away_score` | integer | Null until the game starts |
| `venue` | string | Stadium name |

## Data quality checks

| Check | Rule | On failure |
| --- | --- | --- |
| Uniqueness | One row per `event_id` | Job fails |
| Not null | `event_id`, `event_date`, both team names | Job fails |
| Freshness | Most recent load within 36 hours | Job fails |
| Range | Scores between 0 and 100 | Warning |

## Design decisions

**Parquet for the raw layer, not CSV.** Parquet preserves types, so a null score stays null instead of becoming an empty string that breaks arithmetic later. It also compresses well, which matters when the repo accumulates a file per day.

**Immutable raw files.** The ingest job never rewrites a file that already exists. If a transform has a bug, the fix is to rerun the transform, not to re-pull months of data from an API that may have changed.

**DuckDB over Postgres.** No server to run, no credentials to manage in CI, and the entire warehouse is a single file. The SQL is standard enough that moving to Postgres later is a configuration change rather than a rewrite.

**Idempotent by design.** Running the job twice for the same date produces the same result. This is the property that makes a pipeline safe to retry, and it is the first thing that breaks in naive implementations.

## Running it locally

```bash
git clone https://github.com/YOUR_USERNAME/nfl-data-pipeline.git
cd nfl-data-pipeline

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Ingest yesterday's games
python src/pipeline.py

# Ingest a specific date
python src/pipeline.py --date 2026-09-14
```

## Repository layout

```
nfl-data-pipeline/
├── .github/workflows/daily.yml   Scheduled ingest job
├── src/
│   ├── sources/nfl.py            API client and flattening logic
│   └── pipeline.py               Orchestration entry point
├── data/raw/nfl/                 Immutable Parquet landing zone
├── requirements.txt
└── README.md
```

## Roadmap

- [x] Daily scheduled ingestion to Parquet
- [x] Source abstraction so a second sport can be added without refactoring
- [ ] DuckDB warehouse with incremental loading
- [ ] Watermark tracking so only new dates are pulled
- [ ] Automated data quality checks that fail the build
- [ ] Backfill script for historical seasons
- [ ] Streamlit dashboard with live deployment
- [ ] Schema drift handling when the upstream API adds fields

## What I would do differently

<!-- Fill this in at the end. Be specific and be honest. Examples of the
     kind of thing that reads well:
     - what you would change about the schema now that you have used it
     - a tool you picked that turned out to be the wrong call
     - something you built that you did not end up needing
     Interviewers ask about this section more than any other. -->

## License

MIT
