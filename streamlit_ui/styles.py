"""Stitch theme injection — no custom streamlit_ui layout."""

from streamlit_ui.stitch_renderer import inject_stitch_theme


def inject_app_styles() -> None:
    inject_stitch_theme()
