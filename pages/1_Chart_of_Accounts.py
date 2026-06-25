from datetime import date
from decimal import Decimal

import pandas as pd
import streamlit as st

from app.application.exceptions import ApplicationError
from app.domain.enums import AccountType
from streamlit_ui.auth import render_sidebar, require_login
from streamlit_ui.bootstrap import bootstrap, get_chart_of_account_service, run_async

st.set_page_config(page_title="Chart of Accounts", layout="wide")
bootstrap()

if not require_login():
    st.warning("Please log in from the home page.")
    st.stop()

render_sidebar()
st.title("Chart of Accounts")

service = get_chart_of_account_service()

col1, col2, col3 = st.columns(3)
with col1:
    filter_type = st.selectbox(
        "Account type",
        ["All"] + [t.value for t in AccountType],
    )
with col2:
    filter_active = st.selectbox("Status", ["All", "Active", "Inactive"])
with col3:
    page_size = st.number_input("Rows", min_value=10, max_value=500, value=50)

is_active = None
if filter_active == "Active":
    is_active = True
elif filter_active == "Inactive":
    is_active = False

account_type = AccountType(filter_type) if filter_type != "All" else None

try:
    accounts, total = run_async(
        service.list_accounts(account_type, is_active, skip=0, limit=int(page_size))
    )
except ApplicationError as exc:
    st.error(exc.message)
    st.stop()

if accounts:
    rows = [
        {
            "Code": a.code,
            "Name": a.name,
            "Type": a.account_type.value,
            "Group": a.is_group,
            "Active": a.is_active,
            "Opening": float(a.opening_balance),
            "Current": float(a.current_balance),
            "ID": a.id,
        }
        for a in accounts
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.caption(f"Showing {len(accounts)} of {total} accounts")
else:
    st.info("No accounts found.")

st.divider()
st.subheader("Create account")

with st.form("create_account"):
    c1, c2 = st.columns(2)
    code = c1.text_input("Code")
    name = c2.text_input("Name")
    account_type_new = st.selectbox("Type", [t.value for t in AccountType], key="new_type")
    is_group = st.checkbox("Group account")
    opening_balance = st.number_input("Opening balance", min_value=0.0, value=0.0, step=0.01)
    description = st.text_area("Description")
    submitted = st.form_submit_button("Create account", type="primary")

    if submitted:
        try:
            run_async(
                service.create_account(
                    {
                        "code": code,
                        "name": name,
                        "account_type": account_type_new,
                        "is_group": is_group,
                        "opening_balance": Decimal(str(opening_balance)),
                        "description": description or None,
                    }
                )
            )
            st.success("Account created.")
            st.rerun()
        except ApplicationError as exc:
            st.error(exc.message)
