# Sports Data Pipeline

A scheduled data pipeline that ingests NFL and NCAA wrestling results
daily, lands them as Parquet, loads them into DuckDB, and validates
them before they're queryable.

**[Live dashboard](#)** | **[Latest run](#)**

![screenshot placeholder]

## What it does

Runs every morning at 7am Central via GitHub Actions. Pulls the
previous day's results, writes an immutable raw file, loads only
new records into the warehouse, and fails loudly if the data
doesn't pass quality checks.

## Architecture

[diagram goes here]

## Design decisions

**Why DuckDB over Postgres.** [fill in later]

**Why a source interface.** Adding a new sport means writing one
class and changing one line.

## Data quality

| Check | Rule |
| --- | --- |
| Uniqueness | One row per event id |
| Freshness | Latest load within 36 hours |
| Completeness | No null team names or dates |

## Running it locally

​```bash
git clone ...
​```

## What I'd do differently

[fill in at the end, and be honest here]
