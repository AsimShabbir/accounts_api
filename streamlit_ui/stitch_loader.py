"""Google Stitch project loader — fetch screens, theme, and cached HTML."""

from __future__ import annotations

import json
import re
from pathlib import Path

import requests

from streamlit_ui.config import get_setting

STITCH_MCP_URL = "https://stitch.googleapis.com/mcp"
DEFAULT_PROJECT_ID = "508804251248094601"
ASSETS_DIR = Path(__file__).resolve().parent.parent / "stitch_assets"
MANIFEST_FILE = ASSETS_DIR / "manifest.json"
THEME_FILE = ASSETS_DIR / "design_theme.json"

SCREEN_ALIASES: dict[str, list[str]] = {
    "login": ["login", "sign in", "sign-in", "signin", "auth"],
    "dashboard": ["dashboard", "financial dashboard", "financial", "home", "overview"],
    "chart_of_accounts": ["chart of accounts", "accounts", "coa"],
    "vouchers": ["voucher", "vouchers", "journal"],
    "reports": ["report", "reports", "ledger", "trial balance"],
}


def get_stitch_project_id() -> str:
    return get_setting("STITCH_PROJECT_ID", DEFAULT_PROJECT_ID)


def get_stitch_api_key() -> str:
    return get_setting("STITCH_API_KEY", "")


def _call_stitch_tool(tool_name: str, arguments: dict) -> dict | None:
    api_key = get_stitch_api_key()
    if not api_key:
        return None

    try:
        response = requests.post(
            STITCH_MCP_URL,
            headers={"Content-Type": "application/json", "X-Goog-Api-Key": api_key},
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": arguments},
            },
            timeout=60,
        )
        if response.status_code != 200:
            return None
        data = response.json()
        if data.get("result", {}).get("isError"):
            return None
        return data
    except Exception:
        return None


def _parse_tool_text(result: dict | None) -> dict | list | None:
    if not result:
        return None
    for item in result.get("result", {}).get("content", []):
        if isinstance(item, dict) and item.get("type") == "text":
            try:
                return json.loads(item.get("text", "{}"))
            except json.JSONDecodeError:
                return {"raw": item.get("text", "")}
    return None


def get_project() -> dict | None:
    project_id = get_stitch_project_id()
    result = _call_stitch_tool("get_project", {"name": f"projects/{project_id}"})
    return _parse_tool_text(result)


def list_stitch_screens() -> list[dict]:
    result = _call_stitch_tool("list_screens", {"projectId": get_stitch_project_id()})
    parsed = _parse_tool_text(result)
    if isinstance(parsed, dict):
        return parsed.get("screens", [])
    if isinstance(parsed, list):
        return parsed
    return []


def get_screen(screen_id: str) -> dict | None:
    project_id = get_stitch_project_id()
    result = _call_stitch_tool(
        "get_screen",
        {
            "name": f"projects/{project_id}/screens/{screen_id}",
            "projectId": project_id,
            "screenId": screen_id,
        },
    )
    parsed = _parse_tool_text(result)
    return parsed if isinstance(parsed, dict) else None


def download_url(url: str) -> str:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return response.text


def _screen_title(screen: dict) -> str:
    for key in ("title", "displayName", "name"):
        value = screen.get(key, "")
        if value:
            return str(value).split("/")[-1]
    return str(screen.get("id", ""))


def _screen_id(screen: dict) -> str:
    raw = screen.get("id") or screen.get("screenId") or screen.get("name", "")
    return str(raw).split("/")[-1]


def match_screen(alias: str, screens: list[dict] | None = None) -> dict | None:
    keywords = SCREEN_ALIASES.get(alias, [alias])
    candidates = screens if screens is not None else list_stitch_screens()

    for screen in candidates:
        title = _screen_title(screen).lower()
        if any(kw in title for kw in keywords):
            return screen

    if alias == "login" and candidates:
        return candidates[0]
    if alias == "dashboard" and len(candidates) > 1:
        return candidates[1]
    if alias == "dashboard" and candidates:
        return candidates[0]
    return None


def load_manifest() -> dict:
    if MANIFEST_FILE.is_file():
        return json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    return {}


def get_cached_html(alias: str) -> str | None:
    manifest = load_manifest()
    entry = manifest.get(alias)
    if not entry:
        path = ASSETS_DIR / f"{alias}.html"
        if path.is_file():
            return path.read_text(encoding="utf-8")
        return None

    file_name = entry.get("file", f"{alias}.html")
    path = ASSETS_DIR / file_name
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return None


def get_design_theme() -> dict:
    if THEME_FILE.is_file():
        return json.loads(THEME_FILE.read_text(encoding="utf-8"))

    project = get_project()
    if isinstance(project, dict):
        theme = project.get("designTheme") or project.get("design_theme")
        if theme:
            return theme
    return {}


def extract_css_from_html(html: str) -> str:
    blocks: list[str] = []
    for match in re.finditer(r"<style[^>]*>(.*?)</style>", html, re.DOTALL | re.IGNORECASE):
        blocks.append(match.group(1))
    return "\n".join(blocks)


def sync_screens_to_cache() -> dict:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    api_key = get_stitch_api_key()
    if not api_key:
        raise RuntimeError("STITCH_API_KEY is required. Get one from stitch.withgoogle.com/settings")

    project = get_project()
    if isinstance(project, dict):
        theme = project.get("designTheme") or project.get("design_theme")
        if theme:
            THEME_FILE.write_text(json.dumps(theme, indent=2), encoding="utf-8")

    screens = list_stitch_screens()
    if not screens:
        raise RuntimeError(f"No screens found for Stitch project {get_stitch_project_id()}")

    manifest: dict[str, dict] = {}
    all_css: list[str] = []

    for screen in screens:
        screen_id = _screen_id(screen)
        detail = get_screen(screen_id)
        if not detail:
            continue

        html_url = None
        html_block = detail.get("htmlCode") or detail.get("html_code") or {}
        if isinstance(html_block, dict):
            html_url = html_block.get("downloadUrl") or html_block.get("download_url")

        if not html_url:
            continue

        html = download_url(html_url)
        safe_name = re.sub(r"[^\w\-]+", "_", _screen_title(screen).lower()).strip("_") or screen_id
        file_name = f"{safe_name}.html"
        (ASSETS_DIR / file_name).write_text(html, encoding="utf-8")
        all_css.append(extract_css_from_html(html))

        manifest[safe_name] = {
            "screen_id": screen_id,
            "title": _screen_title(screen),
            "file": file_name,
        }

        for alias, keywords in SCREEN_ALIASES.items():
            title = _screen_title(screen).lower()
            if alias not in manifest and any(kw in title for kw in keywords):
                manifest[alias] = {
                    "screen_id": screen_id,
                    "title": _screen_title(screen),
                    "file": file_name,
                }

    if "login" not in manifest and screens:
        first = screens[0]
        sid = _screen_id(first)
        safe = re.sub(r"[^\w\-]+", "_", _screen_title(first).lower()).strip("_") or sid
        manifest["login"] = manifest.get(safe, {"screen_id": sid, "title": _screen_title(first), "file": f"{safe}.html"})

    if "dashboard" not in manifest:
        for screen in screens[1:] if len(screens) > 1 else screens:
            sid = _screen_id(screen)
            for key, entry in manifest.items():
                if entry.get("screen_id") == sid and key != "login":
                    manifest["dashboard"] = entry
                    break

    MANIFEST_FILE.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (ASSETS_DIR / "theme.css").write_text("\n".join(all_css), encoding="utf-8")
    return manifest


def resolve_screen_html(alias: str) -> tuple[str | None, str]:
    cached = get_cached_html(alias)
    if cached:
        return cached, "cache"

    if not get_stitch_api_key():
        return None, "missing"

    screen = match_screen(alias)
    if not screen:
        return None, "missing"

    detail = get_screen(_screen_id(screen))
    if not detail:
        return None, "missing"

    html_block = detail.get("htmlCode") or detail.get("html_code") or {}
    html_url = html_block.get("downloadUrl") or html_block.get("download_url") if isinstance(html_block, dict) else None
    if not html_url:
        return None, "missing"

    return download_url(html_url), "live"
