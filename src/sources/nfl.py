"""ESPN NFL scoreboard client.

Two jobs only:
  1. fetch_scoreboard(game_date) pulls the raw JSON for one day
  2. flatten(payload) turns that JSON into one flat row per game

Nothing in here writes files. That separation is what lets a second
sport be added later as another module with the same two functions.
"""

from datetime import date

import requests

SPORT = "nfl"
URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"

# Statuses that will never change again, so the day is safe to write.
SETTLED_STATUSES = {"STATUS_FINAL", "STATUS_POSTPONED", "STATUS_CANCELED"}


def fetch_scoreboard(game_date: date) -> dict:
    """Return ESPN's raw scoreboard JSON for one date.

    ESPN's `dates` parameter uses the US Eastern calendar day.
    """
    response = requests.get(
        URL,
        params={"dates": game_date.strftime("%Y%m%d")},
        timeout=30,
    )
    response.raise_for_status()  # a 4xx/5xx stops the job instead of writing bad data
    return response.json()


def _to_int(value):
    """ESPN sends scores as strings like "24". Convert, or None if missing."""
    if value is None or value == "":
        return None
    return int(value)


def flatten(payload: dict) -> list[dict]:
    """Turn the nested ESPN payload into a list of flat game rows."""
    rows = []

    for event in payload.get("events", []):
        competition = event["competitions"][0]
        status = event["status"]["type"]["name"]

        # Competitors come as a list; pick them out by home/away, not position.
        teams = {c["homeAway"]: c for c in competition["competitors"]}
        home, away = teams["home"], teams["away"]

        # ESPN reports 0-0 for games that haven't kicked off. Store null instead,
        # so "no score yet" can't be confused with an actual 0-0 game.
        started = status != "STATUS_SCHEDULED"

        rows.append(
            {
                "event_id": str(event["id"]),
                "event_date": event["date"],
                "status": status,
                "home_team": home["team"]["displayName"],
                "away_team": away["team"]["displayName"],
                "home_score": _to_int(home.get("score")) if started else None,
                "away_score": _to_int(away.get("score")) if started else None,
                "venue": competition.get("venue", {}).get("fullName"),
            }
        )

    return rows
