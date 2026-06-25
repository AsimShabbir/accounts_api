import streamlit as st

from streamlit_ui.auth import render_login, render_sidebar, require_login
from streamlit_ui.bootstrap import bootstrap

st.set_page_config(
    page_title="Accounting System",
    page_icon="📒",
    layout="wide",
    initial_sidebar_state="expanded",
)

bootstrap()

if not require_login():
    render_login()
    st.stop()

render_sidebar()

st.title("Dashboard")
st.markdown(
    """
Welcome to the **Accounting System**. Use the sidebar pages to:

- **Chart of Accounts** — manage your account hierarchy
- **Vouchers** — create, edit, post, and cancel double-entry vouchers
- **Reports** — ledger, trial balance, income statement, and balance sheet
"""
)

user = st.session_state["user"]
col1, col2, col3 = st.columns(3)
col1.metric("Logged in as", user.get("username", ""))
col2.metric("Email", user.get("email", ""))
col3.metric("Status", "Active")
