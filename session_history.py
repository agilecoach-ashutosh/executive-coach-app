"""Explicit, local-only saving of text sessions. Never stores keys or audio."""
from __future__ import annotations
import json
import os
import re
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

MAX_BYTES = 10 * 1024 * 1024
VISIBLE_SCENARIO_FIELDS = ("id", "title", "persona", "environment", "visible_problem", "pack", "difficulty", "practice_focus")


def history_directory():
    if sys.platform == "win32":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home()/"AppData"/"Local"))
    elif sys.platform == "darwin":
        root = Path.home()/"Library"/"Application Support"
    else:
        root = Path(os.environ.get("XDG_DATA_HOME", Path.home()/".local"/"share"))
    return root/"PresenceCoach"/"history"


def validate_record(data):
    if not isinstance(data, dict) or data.get("version") != 1:
        raise ValueError("Unsupported session file.")
    if data.get("mode") not in {"coach", "coachee"}:
        raise ValueError("Invalid session mode.")
    rows = data.get("rows")
    if not isinstance(rows, list) or len(rows) > 20000:
        raise ValueError("Invalid session transcript.")
    for row in rows:
        if not isinstance(row, (list, tuple)) or len(row) != 3 or not all(isinstance(x, str) for x in row):
            raise ValueError("Invalid transcript turn.")
        if row[1] not in {"Coach", "Coachee", "Session note"}:
            raise ValueError("Invalid transcript speaker.")
    for field in ("title", "saved_at", "review"):
        if not isinstance(data.get(field), str):
            raise ValueError(f"Invalid session {field}.")
    if data.get("level") not in {None, "ACC", "PCC", "MCC"}:
        raise ValueError("Invalid review level.")
    if data["review"] and not data.get("level"):
        raise ValueError("Review level is missing.")
    if not isinstance(data.get("duration_seconds"), (int, float)) or not 0 <= data["duration_seconds"] <= 604800:
        raise ValueError("Invalid session duration.")
    scenario = data.get("scenario")
    if scenario is not None and (not isinstance(scenario, dict) or any(
            key not in VISIBLE_SCENARIO_FIELDS or not isinstance(value, str) for key, value in scenario.items())):
        raise ValueError("Invalid visible scenario information.")
    return data


class SessionHistory:
    def __init__(self, directory=None):
        self.directory = Path(directory) if directory is not None else history_directory()

    def _path(self, identifier):
        if not isinstance(identifier, str) or not re.fullmatch(r"[0-9a-f]{32}", identifier):
            raise ValueError("Invalid saved session identifier.")
        return self.directory/f"{identifier}.json"

    def save(self, *, mode, rows, review="", level=None, duration_seconds=0, scenario=None):
        visible = {key: str(scenario[key]) for key in VISIBLE_SCENARIO_FIELDS if key in scenario} if scenario else None
        record = validate_record({"version": 1, "mode": mode, "rows": list(rows), "review": review,
            "level": level, "duration_seconds": duration_seconds, "scenario": visible,
            "title": (visible or {}).get("title", "Coaching conversation"),
            "saved_at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
        content = json.dumps(record, ensure_ascii=False).encode("utf-8")
        if len(content) > MAX_BYTES:
            raise ValueError("This session is too large to save locally.")
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        identifier = uuid.uuid4().hex
        target = self._path(identifier)
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(dir=self.directory, delete=False) as out:
                temp_path = Path(out.name)
                out.write(content)
            os.replace(temp_path, target)
        finally:
            if temp_path and temp_path.exists():
                temp_path.unlink()
        return identifier

    def load(self, identifier):
        path = self._path(identifier)
        if path.stat().st_size > MAX_BYTES:
            raise ValueError("This saved session is too large.")
        return validate_record(json.loads(path.read_text(encoding="utf-8")))

    def list_sessions(self):
        sessions = []
        if not self.directory.exists():
            return sessions
        for path in self.directory.glob("*.json"):
            try:
                data = self.load(path.stem)
                sessions.append({"id": path.stem, "title": data["title"], "saved_at": data["saved_at"],
                                 "mode": data["mode"], "level": data["level"]})
            except (OSError, ValueError, TypeError):
                continue
        return sorted(sessions, key=lambda item: item["saved_at"], reverse=True)

    def delete(self, identifier):
        self._path(identifier).unlink()
