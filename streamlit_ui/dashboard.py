import streamlit as st

from streamlit_ui.stitch_renderer import render_stitch_dashboard, stitch_available


def render_financial_dashboard() -> None:
    user = st.session_state.get("user", {})
    token = st.session_state.get("access_token", "")

    if not stitch_available("dashboard"):
        st.error(
            "Stitch Financial Dashboard screen not synced. "
            "Run: `python scripts/sync_stitch_screens.py`"
        )
        return

    render_stitch_dashboard(user, token)
