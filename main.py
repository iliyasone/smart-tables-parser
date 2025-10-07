"""CLI entrypoint to export Smart Tables statistics for a single match."""

if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

import argparse
import json
from pathlib import Path
from typing import Iterable

from smarttables import SmartTablesClient, build_client


STATS: tuple[str, ...] = (
    "fouls",
    "throwins",
    "shotstarget",
    "goalkicks",
    "yellowcards",
    "offsides",
    "shots",
)

OUTPUT_ROOT = Path("out")


def export_match_stats(
    client: SmartTablesClient,
    match_id: str | int,
    *,
    stats: Iterable[str] = STATS,
) -> None:
    """Fetch each stat and persist it under out/{match_id}/{stat}.json."""

    match_dir = OUTPUT_ROOT / str(match_id)
    match_dir.mkdir(parents=True, exist_ok=True)
    for stat in stats:
        try:
            payload = client.get_stat_odds(match_id=match_id, stat=stat)
            destination = match_dir / f"{stat}.json"
            with destination.open("w", encoding="utf-8") as fp:
                json.dump(payload, fp, ensure_ascii=False, indent=4)
        except Exception as e:
            print("No stat %s for the match %s" % stat % match_id)
            print(e)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download Smart Tables stats for a single match.",
    )
    parser.add_argument(
        "--match_id",
        required=True,
        help="Identifier of the match to export (required).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    client = build_client()
    export_match_stats(client, args.match_id)


if __name__ == "__main__":
    main()
