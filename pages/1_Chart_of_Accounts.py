import pandas as pd
import streamlit as st

from app.domain.enums import AccountType
from streamlit_ui.api_client import ApiError, create_account, list_accounts
from streamlit_ui.auth import require_login
from streamlit_ui.bootstrap import bootstrap
from streamlit_ui.styles import inject_app_styles

st.set_page_config(page_title="Chart of Accounts", layout="wide")
bootstrap()
inject_app_styles()

if not require_login():
    st.warning("Please log in from the home page.")
    st.stop()

st.title("Chart of Accounts")

col1, col2, col3 = st.columns(3)
with col1:
    filter_type = st.selectbox("Account type", ["All"] + [t.value for t in AccountType])
with col2:
    filter_active = st.selectbox("Status", ["All", "Active", "Inactive"])
with col3:
    page_size = st.number_input("Rows", min_value=10, max_value=500, value=50)

is_active = None
if filter_active == "Active":
    is_active = True
elif filter_active == "Inactive":
    is_active = False

account_type = filter_type if filter_type != "All" else None

try:
    accounts, total = list_accounts(account_type, is_active, page=1, page_size=int(page_size))
except ApiError as exc:
    st.error(exc.message)
    st.stop()

if accounts:
    rows = [
        {
            "Code": a["code"],
            "Name": a["name"],
            "Type": a["account_type"],
            "Balance": float(a["current_balance"]),
            "Group": a["is_group"],
            "Active": a["is_active"],
        }
        for a in accounts
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.caption(f"Showing {len(accounts)} of {total} accounts")
else:
    st.info("No accounts found.")

with st.expander("Add Account"):
    with st.form("create_account_form"):
        code = st.text_input("Code")
        name = st.text_input("Name")
        atype = st.selectbox("Type", [t.value for t in AccountType])
        is_group = st.checkbox("Is group account")
        opening_balance = st.number_input("Opening balance", min_value=0.0, value=0.0, step=0.01)
        description = st.text_area("Description")
        submitted = st.form_submit_button("Create Account")

    if submitted:
        if not code or not name:
            st.error("Code and name are required.")
        else:
            try:
                create_account({
                    "code": code,
                    "name": name,
                    "account_type": atype,
                    "is_group": is_group,
                    "opening_balance": opening_balance,
                    "description": description or None,
                })
                st.success("Account created.")
                st.rerun()
            except ApiError as exc:
                st.error(exc.message)
