#!/usr/bin/env python3
"""Download Stitch screens from project 508804251248094601 into stitch_assets/."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from streamlit_ui.stitch_loader import get_stitch_project_id, sync_screens_to_cache


def main() -> dict:
    project_id = get_stitch_project_id()
    print(f"Syncing Stitch project {project_id}...")
    manifest = sync_screens_to_cache()
    print(f"Saved {len(manifest)} screen mappings to stitch_assets/manifest.json")
    for key, entry in manifest.items():
        print(f"  {key}: {entry.get('title')} -> {entry.get('file')}")
    return manifest


if __name__ == "__main__":
    main()
