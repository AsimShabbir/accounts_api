from datetime import date

import pandas as pd
import streamlit as st

from streamlit_ui.api_client import (
    ApiError,
    generate_balance_sheet,
    generate_income_statement,
    generate_ledger,
    generate_trial_balance,
    list_accounts,
)
from streamlit_ui.auth import require_login
from streamlit_ui.bootstrap import bootstrap
from streamlit_ui.styles import inject_app_styles

st.set_page_config(page_title="Reports", layout="wide")
bootstrap()
inject_app_styles()

if not require_login():
    st.warning("Please log in from the home page.")
    st.stop()

st.title("Financial Reports")

today = date.today()
month_start = today.replace(day=1)

tab_ledger, tab_trial, tab_income, tab_balance = st.tabs(
    ["Ledger", "Trial Balance", "Income Statement", "Balance Sheet"]
)

with tab_ledger:
    try:
        accounts, _ = list_accounts(is_active=True, page=1, page_size=500)
    except ApiError as exc:
        st.error(exc.message)
        accounts = []

    leaf_accounts = [a for a in accounts if not a.get("is_group")]
    ledger_options = {f"{a['code']} - {a['name']}": a["id"] for a in leaf_accounts}

    if not ledger_options:
        st.info("No accounts available for ledger report.")
    else:
        selected = st.selectbox("Account", list(ledger_options.keys()), key="ledger_account")
        from_date = st.date_input("From date", value=month_start, key="ledger_from")
        to_date = st.date_input("To date", value=today, key="ledger_to")

        if st.button("Generate Ledger", key="btn_ledger"):
            with st.spinner("Generating ledger report..."):
                try:
                    report = generate_ledger(ledger_options[selected], from_date, to_date)
                    entries = report.get("line_items", [])
                    if entries:
                        st.dataframe(pd.DataFrame(entries), use_container_width=True, hide_index=True)
                    else:
                        st.info("No ledger entries for the selected period.")
                except ApiError as exc:
                    st.error(exc.message)

with tab_trial:
    as_of = st.date_input("As of date", value=today, key="trial_date")
    if st.button("Generate Trial Balance", key="btn_trial"):
        with st.spinner("Generating trial balance..."):
            try:
                report = generate_trial_balance(as_of)
                rows = report.get("line_items", [])
                if rows:
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                else:
                    st.json(report)
            except ApiError as exc:
                st.error(exc.message)

with tab_income:
    inc_from = st.date_input("From date", value=month_start, key="income_from")
    inc_to = st.date_input("To date", value=today, key="income_to")
    if st.button("Generate Income Statement", key="btn_income"):
        with st.spinner("Generating income statement..."):
            try:
                report = generate_income_statement(inc_from, inc_to)
                rows = report.get("line_items", [])
                if rows:
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                else:
                    st.json(report)
            except ApiError as exc:
                st.error(exc.message)

with tab_balance:
    bs_date = st.date_input("As of date", value=today, key="balance_date")
    if st.button("Generate Balance Sheet", key="btn_balance"):
        with st.spinner("Generating balance sheet..."):
            try:
                report = generate_balance_sheet(bs_date)
                rows = report.get("line_items", [])
                if rows:
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                else:
                    st.json(report)
            except ApiError as exc:
                st.error(exc.message)
