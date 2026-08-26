"""Hub upload: instrada alle skill esistenti senza duplicare i secret."""
from __future__ import annotations

import os
import shutil


def execute(params=None):
    params = params or {}
    target = str(params.get("target") or "local").lower().strip()
    path = params.get("path") or params.get("file") or ""

    if target == "github":
        return {
            "status": "SUCCESS",
            "target": "github",
            "message": "Usa skill github-manager / gh. Non fare push di .env o chiavi.",
            "hint": ".agents/skills/github-manager/scripts/push_project.ps1",
        }

    if target in ("huggingface", "hf"):
        return {
            "status": "SUCCESS",
            "target": "huggingface",
            "message": "Usa huggingface-manager (hf_client.py) con HF_TOKEN da env.",
        }

    if target in ("drive", "google_drive"):
        try:
            from skills_vault.google_drive_vault_sync.skill import execute as drive_exec
            return {"status": "SUCCESS", "target": "drive", "result": drive_exec(params)}
        except Exception as exc:
            return {"status": "ERROR", "target": "drive", "message": str(exc)}

    if target == "youtube":
        try:
            from skills_vault.youtube_data_publisher.skill import execute as yt_exec
            return {"status": "SUCCESS", "target": "youtube", "result": yt_exec(params)}
        except Exception as exc:
            return {"status": "ERROR", "target": "youtube", "message": str(exc)}

    if target in ("media", "shorts"):
        try:
            from skills_vault.smart_media_uploader.skill import execute as media_exec
            return {"status": "SUCCESS", "target": "media", "result": media_exec(params)}
        except Exception as exc:
            return {"status": "ERROR", "target": "media", "message": str(exc)}

    # locale
    dest_dir = os.path.join(os.path.dirname(__file__), "..", "..", "public", "uploads")
    os.makedirs(dest_dir, exist_ok=True)
    if path and os.path.isfile(path):
        dest = os.path.join(dest_dir, os.path.basename(path))
        shutil.copy2(path, dest)
        return {"status": "SUCCESS", "target": "local", "saved": dest}
    return {
        "status": "ERROR",
        "message": "Specifica target (github|huggingface|drive|youtube|media|local) e path file.",
    }
