"""Ingest one day of NFL games into an immutable Parquet file.

Usage:
    python src/pipeline.py                     # yesterday (US Eastern)
    python src/pipeline.py --date 2026-09-14   # a specific date

Exit codes:
    0  file written, file already existed, or no games that day
    1  some games aren't finished yet, so nothing was written
"""

import argparse
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from sources import nfl

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / nfl.SPORT


def yesterday_eastern() -> date:
    """Yesterday's date on the US Eastern calendar, which is what ESPN uses."""
    return (datetime.now(ZoneInfo("America/New_York")) - timedelta(days=1)).date()


def to_dataframe(rows: list[dict]) -> pd.DataFrame:
    """Build the DataFrame with explicit types so Parquet stores them correctly."""
    df = pd.DataFrame(rows)
    df["event_date"] = pd.to_datetime(df["event_date"], utc=True)

    df["home_score"] = df["home_score"].astype("Int64")
    df["away_score"] = df["away_score"].astype("Int64")
    for col in ["event_id", "status", "home_team", "away_team", "venue"]:
        df[col] = df[col].astype("string")
    return df


def run(game_date: date) -> int:
    out_path = RAW_DIR / f"{game_date.isoformat()}.parquet"


    if out_path.exists():
        print(f"{out_path.name} already exists, skipping.")
        return 0

    rows = nfl.flatten(nfl.fetch_scoreboard(game_date))

    if not rows:
        print(f"No NFL games on {game_date}. Nothing to write.")
        return 0


    unsettled = [r for r in rows if r["status"] not in nfl.SETTLED_STATUSES]
    if unsettled:
        print(
            f"{len(unsettled)} of {len(rows)} games on {game_date} aren't final yet. "
            "Nothing written; rerun later."
        )
        return 1

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    to_dataframe(rows).to_parquet(out_path, index=False)
    print(f"Wrote {len(rows)} games to {out_path.name}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest NFL games for one date.")
    parser.add_argument(
        "--date",
        type=date.fromisoformat,
        default=None,
        help="YYYY-MM-DD (US Eastern). Defaults to yesterday.",
    )
    args = parser.parse_args()
    sys.exit(run(args.date or yesterday_eastern()))


if __name__ == "__main__":
    main()
