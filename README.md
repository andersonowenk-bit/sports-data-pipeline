# sports-data-pipeline

Pulls NFL scores from ESPN every morning, saves each day's games as a Parquet file, and will eventually load them into a DuckDB warehouse with data quality checks on top. It's NFL only for now, but the code is split up so another sport can be added as its own module later.

The daily job has been live since September 21, 2026. Every game day shows up in the commit history as a commit from `github-actions[bot]`.

**Status:** ingestion is running daily. The warehouse and quality checks are next.

## Why I built it

A lot of portfolio pipelines load one CSV one time and stop there. I wanted something that runs on its own against a live API, because that's where the harder problems show up. What happens if the job runs twice? What if a game is still going when it fires? What if ESPN changes the response? This project is me working through those.

## How it works

```
ESPN scoreboard API
      |
      v
ingest job                          GitHub Actions, daily at 12:00 UTC (7am Central)
      |
      v
data/raw/nfl/YYYY-MM-DD.parquet     one file per day, never edited
      |
      v
DuckDB warehouse                    not built yet
      |
      v
quality checks                      not built yet
```

Each morning the job grabs the previous day's games. On days with no games, which is most weekdays, it doesn't write anything. On game days it writes one Parquet file for that date and commits it back to the repo.

Raw files never get overwritten. If I break a transform later, I can rebuild everything downstream from these files instead of re-pulling months of data from the API.

## Data source

ESPN's public scoreboard endpoint. No API key or login, and one request a day is nowhere near any limit.

```
GET https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates=YYYYMMDD
```

It's not an official, documented API, so the response could change without notice. That's part of why schema drift handling is on the roadmap.

## What gets stored

One row per game:

| Column | Type | Notes |
|---|---|---|
| `event_id` | string | ESPN's game ID, used as the primary key |
| `event_date` | timestamp | Kickoff time in UTC |
| `status` | string | `STATUS_FINAL`, `STATUS_POSTPONED`, or `STATUS_CANCELED` |
| `home_team` | string | Full team name |
| `away_team` | string | Full team name |
| `home_score` | integer | Null if the game never started |
| `away_score` | integer | Null if the game never started |
| `venue` | string | Stadium name |

## Decisions and tradeoffs

**Parquet instead of CSV.** CSV doesn't keep types, so a missing score turns into an empty string and breaks any math on that column. Parquet keeps nulls as nulls, and the files stay small even with a new one every game day.

**Unfinished days don't get written.** If any game from that date is still scheduled or in progress, the job writes nothing and fails on purpose. Since raw files are never edited, saving a half-finished day would lock in the wrong scores permanently.

**Dates use Eastern time.** ESPN groups games by the Eastern calendar day, so the pipeline does too. A Sunday night game that kicks off at 8:20pm ET goes in Sunday's file, even though its UTC `event_date` says Monday.

**Reruns are safe.** If a file for that date already exists, the job skips it. Running it twice gives the same result as running it once, so a retry can't create duplicate data.

**DuckDB for the warehouse (planned).** There's no server to run and no credentials to set up in GitHub Actions, and the whole database is one file. The SQL is close enough to Postgres that switching later wouldn't mean a rewrite.

## Planned quality checks

| Check | Rule | If it fails |
|---|---|---|
| Uniqueness | One row per `event_id` | Job fails |
| Not null | `event_id`, `event_date`, and both team names | Job fails |
| Freshness | Last successful run within 36 hours | Job fails |
| Range | Scores between 0 and 100 | Warning only |

Freshness is based on the last successful run, not the newest game date. Most Tuesdays and Wednesdays have no games, so a game-date check would fail every week.

## Running it locally

```bash
git clone https://github.com/andersonowenk-bit/sports-data-pipeline.git
cd sports-data-pipeline

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# yesterday's games
python src/pipeline.py

# a specific date
python src/pipeline.py --date 2026-09-14
```

## Repo layout

```
sports-data-pipeline/
├── .github/workflows/daily.yml   the scheduled job
├── src/
│   ├── sources/nfl.py            ESPN client, turns the JSON into rows
│   └── pipeline.py               entry point, decides what gets written
├── data/raw/nfl/                 one Parquet file per game day
├── requirements.txt
└── README.md
```

## Roadmap

- [x] Ingestion script with Parquet output
- [x] Separate source module so a second sport can be added without refactoring
- [x] Daily scheduled run with GitHub Actions
- [ ] DuckDB warehouse with incremental loading
- [ ] Watermark tracking so only new dates get loaded
- [ ] Data quality checks that fail the job
- [ ] Backfill script for past seasons
- [ ] Streamlit dashboard
- [ ] Handling for new or changed fields in the ESPN response

## License

MIT
