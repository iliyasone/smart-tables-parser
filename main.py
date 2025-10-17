"""CLI entrypoint to export Smart Tables statistics for one or more matches."""

if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

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
) -> dict[str, dict[str, list[tuple[str, str] | str]]]:
    """Fetch stats, persist available data, and track per-stat outcomes."""

    match_dir = OUTPUT_ROOT / str(match_id)
    match_dir.mkdir(parents=True, exist_ok=True)
    stat_odds_dir = match_dir / "stat-odds"
    stat_odds_dir.mkdir(parents=True, exist_ok=True)
    chart_dir = match_dir / "charts"
    chart_dir.mkdir(parents=True, exist_ok=True)

    summary: dict[str, dict[str, list[Any]]] = {
        "stat_odds": {"retrieved": [], "missing": [], "errors": []},
        "charts": {"retrieved": [], "missing": [], "errors": []},
    }

    for stat in stats:
        try:
            payload = client.get_stat_odds(match_id=match_id, stat=stat)
            if payload is None:
                summary["stat_odds"]["missing"].append(stat)
            else:
                destination = stat_odds_dir / f"{stat}.json"
                with destination.open("w", encoding="utf-8") as fp:
                    json.dump(payload, fp, ensure_ascii=False, indent=4)
                summary["stat_odds"]["retrieved"].append(stat)
        except Exception as exc:
            summary["stat_odds"]["errors"].append((stat, str(exc)))

        try:
            chart_payload = client.get_chart(match_id=match_id, stat=stat)
            if chart_payload is None:
                summary["charts"]["missing"].append(stat)
            else:
                chart_destination = chart_dir / f"{stat}.json"
                with chart_destination.open("w", encoding="utf-8") as fp:
                    json.dump(chart_payload, fp, ensure_ascii=False, indent=4)
                summary["charts"]["retrieved"].append(stat)
        except Exception as exc:
            summary["charts"]["errors"].append((stat, str(exc)))

    return summary

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download Smart Tables stats for one or more matches.",
    )
    parser.add_argument(
        "--match_ids",
        required=True,
        help=(
            "Comma-separated list of match identifiers to export (no whitespace is "
            "required, but tolerated)."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    client = build_client()
    match_ids = [match_id.strip() for match_id in args.match_ids.split(",") if match_id.strip()]
    for match_id in match_ids:
        summary = export_match_stats(client, match_id)
        print(f"Match {match_id} results:")
        for key, label in (("stat_odds", "stat-odds"), ("charts", "charts")):
            retrieved = ", ".join(summary[key]["retrieved"]) or "none"
            missing = ", ".join(summary[key]["missing"]) or "none"
            print(f"  {label} retrieved: {retrieved}")
            print(f"  {label} missing (server error): {missing}")
            if summary[key]["errors"]:
                print(f"  {label} errors:")
                for stat, message in summary[key]["errors"]:
                    print(f"    {stat}: {message}")
            else:
                print(f"  {label} errors: none")


if __name__ == "__main__":
    main()
