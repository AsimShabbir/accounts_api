from datetime import date

import pandas as pd
import streamlit as st

from app.application.exceptions import ApplicationError
from streamlit_ui.auth import render_sidebar, require_login
from streamlit_ui.bootstrap import bootstrap, get_chart_of_account_service, get_report_service, run_async

st.set_page_config(page_title="Reports", layout="wide")
bootstrap()

if not require_login():
    st.warning("Please log in from the home page.")
    st.stop()

render_sidebar()
st.title("Financial Reports")

report_service = get_report_service()
account_service = get_chart_of_account_service()

tab1, tab2, tab3, tab4 = st.tabs(
    ["Ledger", "Trial Balance", "Income Statement", "Balance Sheet"]
)

accounts, _ = run_async(account_service.list_accounts(is_active=True, skip=0, limit=500))
ledger_accounts = [a for a in accounts if not a.is_group and a.id]
ledger_options = {f"{a.code} - {a.name}": a.id for a in ledger_accounts}

with tab1:
    st.subheader("Account Ledger")
    selected = st.selectbox("Account", list(ledger_options.keys()), key="ledger_acc")
    c1, c2 = st.columns(2)
    from_date = c1.date_input("From date", value=date(date.today().year, 1, 1), key="ledger_from")
    to_date = c2.date_input("To date", value=date.today(), key="ledger_to")

    if st.button("Generate Ledger", type="primary"):
        try:
            report = run_async(
                report_service.generate_ledger(ledger_options[selected], from_date, to_date)
            )
            rows = [
                {
                    "Date": item.metadata.get("voucher_date", ""),
                    "Voucher": item.metadata.get("voucher_number", ""),
                    "Debit": float(item.debit),
                    "Credit": float(item.credit),
                    "Balance": float(item.balance),
                    "Description": item.metadata.get("description", ""),
                }
                for item in report.line_items
            ]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            st.json({k: float(v) for k, v in report.totals.items()})
        except ApplicationError as exc:
            st.error(exc.message)

with tab2:
    st.subheader("Trial Balance")
    as_of_tb = st.date_input("As of date", value=date.today(), key="tb_date")
    if st.button("Generate Trial Balance", type="primary"):
        try:
            report = run_async(report_service.generate_trial_balance(as_of_tb))
            rows = [
                {
                    "Code": item.account_code,
                    "Name": item.account_name,
                    "Type": item.account_type,
                    "Debit": float(item.debit),
                    "Credit": float(item.credit),
                }
                for item in report.line_items
            ]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            st.json({k: float(v) for k, v in report.totals.items()})
        except ApplicationError as exc:
            st.error(exc.message)

with tab3:
    st.subheader("Income Statement")
    c1, c2 = st.columns(2)
    from_is = c1.date_input("From date", value=date(date.today().year, 1, 1), key="is_from")
    to_is = c2.date_input("To date", value=date.today(), key="is_to")
    if st.button("Generate Income Statement", type="primary"):
        try:
            report = run_async(report_service.generate_income_statement(from_is, to_is))
            rows = [
                {
                    "Code": item.account_code,
                    "Name": item.account_name,
                    "Type": item.account_type,
                    "Amount": float(item.balance),
                }
                for item in report.line_items
            ]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            st.json({k: float(v) for k, v in report.totals.items()})
        except ApplicationError as exc:
            st.error(exc.message)

with tab4:
    st.subheader("Balance Sheet")
    as_of_bs = st.date_input("As of date", value=date.today(), key="bs_date")
    if st.button("Generate Balance Sheet", type="primary"):
        try:
            report = run_async(report_service.generate_balance_sheet(as_of_bs))
            rows = [
                {
                    "Code": item.account_code,
                    "Name": item.account_name,
                    "Type": item.account_type,
                    "Balance": float(item.balance),
                }
                for item in report.line_items
            ]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            st.json({k: float(v) for k, v in report.totals.items()})
        except ApplicationError as exc:
            st.error(exc.message)
