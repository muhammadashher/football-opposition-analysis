"""Download StatsBomb open data for every match a team played in a competition.

Usage: python src/download_data.py            (defaults: Spain, UEFA Euro 2024)
Data: StatsBomb Open Data, https://github.com/statsbomb/open-data (free for non-commercial use with attribution).
"""
import json
import sys
import urllib.request
from pathlib import Path

BASE = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"
ROOT = Path(__file__).resolve().parents[1] / "data"


def fetch(url, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        urllib.request.urlretrieve(url, path)
    return json.loads(path.read_text(encoding="utf-8"))


def main(team="Spain", competition_id=55, season_id=282):
    matches = fetch(f"{BASE}/matches/{competition_id}/{season_id}.json",
                    ROOT / f"matches_{competition_id}_{season_id}.json")
    ids = [m["match_id"] for m in matches
           if team in (m["home_team"]["home_team_name"], m["away_team"]["away_team_name"])]
    for mid in ids:
        fetch(f"{BASE}/events/{mid}.json", ROOT / "events" / f"{mid}.json")
        fetch(f"{BASE}/lineups/{mid}.json", ROOT / "lineups" / f"{mid}.json")
    print(f"Downloaded {len(ids)} matches for {team}")


if __name__ == "__main__":
    main(*sys.argv[1:2])
