import streamlit as st

from streamlit_ui.auth import apply_auth_callback, render_login, require_login
from streamlit_ui.bootstrap import bootstrap
from streamlit_ui.dashboard import render_financial_dashboard
from streamlit_ui.stitch_renderer import hide_streamlit_chrome

st.set_page_config(
    page_title="Financial Portal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

bootstrap()
apply_auth_callback()

if not require_login():
    render_login()
    st.stop()

hide_streamlit_chrome()
render_financial_dashboard()
