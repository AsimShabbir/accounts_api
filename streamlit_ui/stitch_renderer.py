"""Render Google Stitch screens inside Streamlit with live API wiring."""

from __future__ import annotations

import json
import re

import streamlit as st
import streamlit.components.v1 as components

from streamlit_ui.api_client import get_api_base_url
from streamlit_ui.stitch_loader import (
    ASSETS_DIR,
    extract_css_from_html,
    get_cached_html,
    get_design_theme,
    get_stitch_api_key,
    get_stitch_project_id,
    resolve_screen_html,
)


def stitch_available(alias: str) -> bool:
    html, _ = resolve_screen_html(alias)
    return html is not None


def stitch_setup_message(alias: str) -> str:
    return (
        f"Stitch screen **{alias}** is not available yet for project `{get_stitch_project_id()}`.\n\n"
        "1. Add your API key to `.env`: `STITCH_API_KEY=...` (from stitch.withgoogle.com/settings)\n"
        "2. Run: `python scripts/sync_stitch_screens.py`"
    )


def hide_streamlit_chrome() -> None:
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] { display: none !important; }
            [data-testid="stHeader"] { display: none !important; }
            [data-testid="stToolbar"] { display: none !important; }
            [data-testid="stDecoration"] { display: none !important; }
            .stApp, .main, .block-container {
                padding: 0 !important;
                margin: 0 !important;
                max-width: 100% !important;
            }
            .block-container { padding-top: 0 !important; }
            iframe { border: none !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def inject_stitch_theme() -> None:
    theme = get_design_theme()
    theme_css_path = ASSETS_DIR / "theme.css"
    extra_css = ""

    if theme_css_path.is_file():
        extra_css = theme_css_path.read_text(encoding="utf-8")
    else:
        for alias in ("login", "dashboard"):
            html = get_cached_html(alias)
            if html:
                extra_css += extract_css_from_html(html)

    theme_vars = ""
    if theme:
        colors = theme.get("colors") or theme.get("colorScheme") or {}
        if isinstance(colors, dict):
            for key, value in colors.items():
                safe_key = re.sub(r"[^a-zA-Z0-9_-]", "-", str(key))
                theme_vars += f"  --stitch-{safe_key}: {value};\n"

    st.markdown(
        f"""
        <style>
            :root {{
                {theme_vars}
            }}
            {extra_css}
            .stApp {{
                background: var(--stitch-background, #0f172a);
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _inject_before_body_close(html: str, injection: str) -> str:
    if "</body>" in html.lower():
        return re.sub(r"</body>", f"{injection}</body>", html, count=1, flags=re.IGNORECASE)
    return html + injection


def build_login_html(api_base_url: str) -> str | None:
    html, _ = resolve_screen_html("login")
    if not html:
        return None

    bridge = f"""
<script>
(function() {{
  const API_BASE = {json.dumps(api_base_url)};

  function findEmailInput() {{
    return document.querySelector('input[type=email], input[name*=email i], input[placeholder*=email i], input[type=text]');
  }}
  function findPasswordInput() {{
    return document.querySelector('input[type=password]');
  }}
  function findSubmitButton() {{
    return document.querySelector('button[type=submit], input[type=submit], button');
  }}

  async function handleLogin(event) {{
    if (event) event.preventDefault();
    const email = findEmailInput();
    const password = findPasswordInput();
    if (!email || !password) return;

    const btn = findSubmitButton();
    if (btn) btn.disabled = true;

    try {{
      const res = await fetch(API_BASE + '/api/v1/auth/login', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{
          username_or_email: email.value,
          password: password.value
        }})
      }});
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Login failed');
      const q = new URLSearchParams();
      q.set('access_token', data.access_token);
      q.set('refresh_token', data.refresh_token);
      q.set('user', JSON.stringify(data.user));
      window.top.location.href = window.top.location.pathname + '?' + q.toString();
    }} catch (err) {{
      alert(err.message || 'Login failed');
      if (btn) btn.disabled = false;
    }}
  }}

  document.addEventListener('DOMContentLoaded', function() {{
    const form = document.querySelector('form');
    if (form) form.addEventListener('submit', handleLogin);
    const btn = findSubmitButton();
    if (btn && !form) btn.addEventListener('click', handleLogin);
  }});
}})();
</script>
"""
    return _inject_before_body_close(html, bridge)


def build_dashboard_html(api_base_url: str, access_token: str, user: dict) -> str | None:
    html, _ = resolve_screen_html("dashboard")
    if not html:
        return None

    user_name = user.get("full_name") or user.get("username") or "User"

    live_script = f"""
<script>
(function() {{
  const API_BASE = {json.dumps(api_base_url)};
  const TOKEN = {json.dumps(access_token)};
  const USER_NAME = {json.dumps(user_name)};

  function setText(selectors, value) {{
    for (const sel of selectors) {{
      document.querySelectorAll(sel).forEach(el => {{
        if (el.children.length === 0) el.textContent = value;
      }});
    }}
  }}

  function formatMoney(n) {{
    return Number(n).toLocaleString(undefined, {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }});
  }}

  function sumByType(accounts, type) {{
    return accounts
      .filter(a => !a.is_group && a.account_type === type)
      .reduce((sum, a) => sum + Number(a.current_balance || 0), 0);
  }}

  async function apiGet(path) {{
    const res = await fetch(API_BASE + path, {{
      headers: {{ Authorization: 'Bearer ' + TOKEN }}
    }});
    if (!res.ok) throw new Error('API error ' + res.status);
    return res.json();
  }}

  async function refresh() {{
    try {{
      const [accountsRes, vouchersRes] = await Promise.all([
        apiGet('/api/v1/chart-of-accounts?page=1&page_size=500&is_active=true'),
        apiGet('/api/v1/vouchers?page=1&page_size=10'),
      ]);
      const accounts = accountsRes.data || [];
      const assets = sumByType(accounts, 'asset');
      const liabilities = sumByType(accounts, 'liability');
      const equity = sumByType(accounts, 'equity');
      const revenue = sumByType(accounts, 'revenue');
      const expenses = sumByType(accounts, 'expense');

      setText(['[data-live-metric="assets"]'], formatMoney(assets));
      setText(['[data-live-metric="liabilities"]'], formatMoney(liabilities));
      setText(['[data-live-metric="equity"]'], formatMoney(equity));
      setText(['[data-live-metric="revenue"]'], formatMoney(revenue));
      setText(['[data-live-metric="expenses"]'], formatMoney(expenses));
      setText(['[data-user-name]'], USER_NAME);
    }} catch (e) {{}}
  }}

  document.addEventListener('DOMContentLoaded', function() {{
    refresh();
    setInterval(refresh, 10000);
  }});
}})();
</script>
"""
    return _inject_before_body_close(html, live_script)


def render_stitch_login() -> None:
    hide_streamlit_chrome()
    inject_stitch_theme()

    html = build_login_html(get_api_base_url())
    if not html:
        st.error(stitch_setup_message("login"))
        return

    components.html(html, height=900, scrolling=True)


def render_stitch_dashboard(user: dict, access_token: str) -> None:
    hide_streamlit_chrome()
    inject_stitch_theme()

    html = build_dashboard_html(get_api_base_url(), access_token, user)
    if not html:
        st.error(stitch_setup_message("dashboard"))
        return

    nav_html = """
<div style="position:fixed;bottom:16px;right:16px;z-index:9999;display:flex;gap:8px;">
  <a href="/Chart_of_Accounts" target="_top" style="background:#1e40af;color:#fff;padding:8px 14px;border-radius:8px;text-decoration:none;font-family:sans-serif;font-size:13px;">Accounts</a>
  <a href="/Vouchers" target="_top" style="background:#1e40af;color:#fff;padding:8px 14px;border-radius:8px;text-decoration:none;font-family:sans-serif;font-size:13px;">Vouchers</a>
  <a href="/Reports" target="_top" style="background:#1e40af;color:#fff;padding:8px 14px;border-radius:8px;text-decoration:none;font-family:sans-serif;font-size:13px;">Reports</a>
  <a href="?logout=1" target="_top" style="background:#334155;color:#fff;padding:8px 14px;border-radius:8px;text-decoration:none;font-family:sans-serif;font-size:13px;">Logout</a>
</div>
"""
    html = _inject_before_body_close(html, nav_html)
    components.html(html, height=1000, scrolling=True)
