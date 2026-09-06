"""
Project Save / Load.

Session sirf memory mein hoti hai — server band hua to sab gaya. Ye module
poore project (segments, media assignments, saari settings, stickers, texts,
sound effects) ko ek JSON file mein save karta hai, aur baad mein wapas load
kar deta hai — taake kaam kabhi zaya na ho.
"""

import json
import os
import re
import time

PROJECT_EXT = ".vebproj.json"


def _safe_name(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", (name or "").strip())
    name = re.sub(r"\s+", "_", name)
    return name[:80] or "project"


def project_path(projects_dir: str, name: str) -> str:
    return os.path.join(projects_dir, _safe_name(name) + PROJECT_EXT)


def save_project(projects_dir: str, name: str, payload: dict) -> dict:
    """Project ko JSON file mein save karta hai (same naam ho to overwrite)."""
    os.makedirs(projects_dir, exist_ok=True)
    path = project_path(projects_dir, name)

    record = {
        "name": name,
        "saved_at": time.time(),
        "version": 10,
        "data": payload,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)

    return {"name": name, "path": path, "saved_at": record["saved_at"]}


def load_project(projects_dir: str, name: str) -> dict:
    """Saved project wapas parh kar deta hai."""
    path = project_path(projects_dir, name)
    if not os.path.exists(path):
        raise FileNotFoundError("Project nahi mila.")
    with open(path, "r", encoding="utf-8") as f:
        record = json.load(f)
    return record


def list_projects(projects_dir: str) -> list:
    """Saare saved projects ki list (naye pehle)."""
    if not os.path.isdir(projects_dir):
        return []

    items = []
    for filename in os.listdir(projects_dir):
        if not filename.endswith(PROJECT_EXT):
            continue
        full = os.path.join(projects_dir, filename)
        try:
            with open(full, "r", encoding="utf-8") as f:
                record = json.load(f)
            data = record.get("data", {})
            items.append({
                "name": record.get("name", filename[: -len(PROJECT_EXT)]),
                "saved_at": record.get("saved_at", os.path.getmtime(full)),
                "segment_count": len(data.get("segments") or []),
                "has_voice": bool(data.get("voice_file")),
                "has_music": bool(data.get("music_file")),
            })
        except (OSError, json.JSONDecodeError, ValueError):
            continue

    items.sort(key=lambda x: x["saved_at"], reverse=True)
    return items


def delete_project(projects_dir: str, name: str) -> bool:
    path = project_path(projects_dir, name)
    if os.path.exists(path):
        os.remove(path)
        return True
    return False
