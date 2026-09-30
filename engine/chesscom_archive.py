"""Reproducible downloader for public Chess.com monthly game archives."""

from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.request
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path


API_ROOT = "https://api.chess.com/pub/player"
USER_AGENT = "AdaptiveChessEngineResearch/1.0 (Chess.com user: YashDutt7)"


@dataclass(frozen=True, slots=True)
class ArchiveSummary:
    username: str
    archive_count: int
    downloaded_games: int
    unique_games: int
    duplicate_games: int
    first_archive: str
    last_archive: str
    by_rules: dict[str, int]
    by_time_class: dict[str, int]
    by_time_control: dict[str, int]
    combined_pgn_sha256: str


def _get_json(url: str, attempts: int = 5) -> dict:
    for attempt in range(attempts):
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code not in {429, 500, 502, 503, 504} or attempt + 1 == attempts:
                raise
        except urllib.error.URLError:
            if attempt + 1 == attempts:
                raise
        time.sleep(2 ** attempt)
    raise RuntimeError("unreachable")


def _identity(game: dict) -> str:
    identity = game.get("uuid") or game.get("url")
    if identity:
        return str(identity)
    return hashlib.sha256(game.get("pgn", "").encode("utf-8")).hexdigest()


def summarize_games(username: str, archive_urls: list[str], games: list[dict], combined_pgn: str) -> ArchiveSummary:
    identities = [_identity(game) for game in games]
    unique_count = len(set(identities))
    return ArchiveSummary(
        username=username,
        archive_count=len(archive_urls),
        downloaded_games=len(games),
        unique_games=unique_count,
        duplicate_games=len(games)-unique_count,
        first_archive=archive_urls[0] if archive_urls else "",
        last_archive=archive_urls[-1] if archive_urls else "",
        by_rules=dict(sorted(Counter(game.get("rules", "unknown") for game in games).items())),
        by_time_class=dict(sorted(Counter(game.get("time_class", "unknown") for game in games).items())),
        by_time_control=dict(sorted(Counter(game.get("time_control", "unknown") for game in games).items())),
        combined_pgn_sha256=hashlib.sha256(combined_pgn.encode("utf-8")).hexdigest(),
    )


def download_player_archive(username: str, output_dir: str | Path) -> ArchiveSummary:
    output = Path(output_dir)
    months = output / "months"
    months.mkdir(parents=True, exist_ok=True)
    profile = _get_json(f"{API_ROOT}/{username}")
    if profile.get("username", "").casefold() != username.casefold():
        raise ValueError(f"Chess.com returned a different user: {profile.get('username')!r}")
    stats = _get_json(f"{API_ROOT}/{username}/stats")
    archive_urls = _get_json(f"{API_ROOT}/{username}/games/archives").get("archives", [])
    games = []
    for index, url in enumerate(archive_urls, 1):
        archive = _get_json(url)
        month_games = archive.get("games", [])
        games.extend(month_games)
        month_name = "/".join(url.rstrip("/").split("/")[-2:]).replace("/", "-")
        (months / f"{month_name}.json").write_text(json.dumps(archive, indent=2), encoding="utf-8")
        print(f"archive {index}/{len(archive_urls)}: {month_name} games={len(month_games)}", flush=True)

    unique = {}
    for game in games:
        unique.setdefault(_identity(game), game)
    ordered = sorted(unique.values(), key=lambda game: (game.get("end_time", 0), _identity(game)))
    all_pgn = "\n\n".join(game["pgn"].strip() for game in ordered if game.get("pgn")) + "\n"
    standard = [game for game in ordered if game.get("rules") == "chess" and game.get("pgn")]
    standard_pgn = "\n\n".join(game["pgn"].strip() for game in standard) + "\n"
    rapid = [game for game in standard if game.get("time_class") == "rapid"]
    rapid_pgn = "\n\n".join(game["pgn"].strip() for game in rapid) + "\n"
    ten_minute = [game for game in rapid if game.get("time_control") == "600"]
    ten_minute_pgn = "\n\n".join(game["pgn"].strip() for game in ten_minute) + "\n"

    (output / "profile.json").write_text(json.dumps(profile, indent=2), encoding="utf-8")
    (output / "stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    (output / "all_games.pgn").write_text(all_pgn, encoding="utf-8")
    (output / "standard_games.pgn").write_text(standard_pgn, encoding="utf-8")
    (output / "rapid_games.pgn").write_text(rapid_pgn, encoding="utf-8")
    (output / "rapid_10min_games.pgn").write_text(ten_minute_pgn, encoding="utf-8")
    summary = summarize_games(username, archive_urls, games, all_pgn)
    manifest = {**asdict(summary), "standard_games": len(standard), "rapid_games": len(rapid), "rapid_10min_games": len(ten_minute)}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return summary
