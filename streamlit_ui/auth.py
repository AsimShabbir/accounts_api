import streamlit as st

from streamlit_ui.api_client import get_api_base_url
from streamlit_ui.stitch_loader import get_stitch_api_key, get_stitch_project_id, sync_screens_to_cache
from streamlit_ui.stitch_renderer import render_stitch_login, stitch_available


def require_login() -> bool:
    return bool(st.session_state.get("user"))


def apply_auth_callback() -> None:
    params = st.query_params
    if params.get("logout") == "1":
        for key in ("user", "access_token", "refresh_token"):
            st.session_state.pop(key, None)
        st.query_params.clear()
        st.rerun()

    if params.get("access_token") and params.get("refresh_token"):
        import json

        try:
            user = json.loads(params.get("user", "{}"))
        except json.JSONDecodeError:
            user = {}

        st.session_state.access_token = params.get("access_token")
        st.session_state.refresh_token = params.get("refresh_token")
        st.session_state.user = user
        st.query_params.clear()
        st.rerun()


def render_login() -> None:
    apply_auth_callback()

    if not stitch_available("login"):
        st.error(
            f"Stitch login screen not found for project `{get_stitch_project_id()}`. "
            "Set `STITCH_API_KEY` in `.env` and run `python scripts/sync_stitch_screens.py`."
        )
        st.info(f"API: {get_api_base_url()}")

        if get_stitch_api_key() and st.button("Sync Stitch screens now"):
            try:
                sync_screens_to_cache()
                st.success("Stitch screens synced. Refresh the page.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
        return

    render_stitch_login()


def render_sidebar() -> None:
    pass
