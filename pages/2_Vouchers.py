from datetime import date

import pandas as pd
import streamlit as st

from app.domain.enums import VoucherStatus, VoucherType
from streamlit_ui.api_client import ApiError, cancel_voucher, create_voucher, list_accounts, list_vouchers, post_voucher
from streamlit_ui.auth import require_login
from streamlit_ui.bootstrap import bootstrap
from streamlit_ui.styles import inject_app_styles

st.set_page_config(page_title="Vouchers", layout="wide")
bootstrap()
inject_app_styles()

if not require_login():
    st.warning("Please log in from the home page.")
    st.stop()

st.title("Vouchers")

filter_col1, filter_col2 = st.columns(2)
with filter_col1:
    status_filter = st.selectbox("Status", ["All"] + [s.value for s in VoucherStatus])
with filter_col2:
    type_filter = st.selectbox("Type", ["All"] + [t.value for t in VoucherType])

status = status_filter if status_filter != "All" else None
voucher_type = type_filter if type_filter != "All" else None

try:
    vouchers, total = list_vouchers(status, voucher_type, page=1, page_size=100)
except ApiError as exc:
    st.error(exc.message)
    st.stop()

if vouchers:
    st.dataframe(
        pd.DataFrame([
            {
                "Number": v["voucher_number"],
                "Type": v["voucher_type"],
                "Date": v["voucher_date"],
                "Status": v["status"],
                "Debit": float(v["total_debit"]),
                "Credit": float(v["total_credit"]),
            }
            for v in vouchers
        ]),
        use_container_width=True,
        hide_index=True,
    )
    st.caption(f"Showing {len(vouchers)} of {total} vouchers")

    draft_vouchers = [v for v in vouchers if v["status"] == "draft"]
    if draft_vouchers:
        st.subheader("Post or Cancel Draft")
        options = {f"{v['voucher_number']} ({v['voucher_date']})": v for v in draft_vouchers}
        selected = st.selectbox("Select draft voucher", list(options.keys()))
        action_col1, action_col2 = st.columns(2)
        with action_col1:
            if st.button("Post Voucher", type="primary"):
                try:
                    post_voucher(options[selected]["id"])
                    st.success("Voucher posted.")
                    st.rerun()
                except ApiError as exc:
                    st.error(exc.message)
        with action_col2:
            if st.button("Cancel Voucher"):
                try:
                    cancel_voucher(options[selected]["id"])
                    st.success("Voucher cancelled.")
                    st.rerun()
                except ApiError as exc:
                    st.error(exc.message)
else:
    st.info("No vouchers found.")

with st.expander("Create Voucher"):
    try:
        accounts, _ = list_accounts(is_active=True, page=1, page_size=500)
    except ApiError as exc:
        st.error(exc.message)
        accounts = []

    leaf_accounts = [a for a in accounts if not a.get("is_group")]
    account_options = {f"{a['code']} - {a['name']}": a for a in leaf_accounts}

    with st.form("create_voucher_form"):
        vtype = st.selectbox("Voucher type", [t.value for t in VoucherType])
        vdate = st.date_input("Voucher date", value=date.today())
        reference = st.text_input("Reference")
        narration = st.text_area("Narration")

        st.markdown("**Debit entry**")
        debit_account = st.selectbox("Debit account", list(account_options.keys()), key="debit_acc")
        debit_amount = st.number_input("Debit amount", min_value=0.01, value=100.0, step=0.01)

        st.markdown("**Credit entry**")
        credit_account = st.selectbox("Credit account", list(account_options.keys()), key="credit_acc")
        credit_amount = st.number_input("Credit amount", min_value=0.01, value=100.0, step=0.01)

        submitted = st.form_submit_button("Create Draft Voucher")

    if submitted:
        if debit_amount != credit_amount:
            st.error("Debit and credit amounts must be equal.")
        elif debit_account == credit_account:
            st.error("Debit and credit accounts must differ.")
        else:
            try:
                create_voucher({
                    "voucher_type": vtype,
                    "voucher_date": vdate.isoformat(),
                    "reference": reference or None,
                    "narration": narration or None,
                    "entries": [
                        {
                            "account_id": account_options[debit_account]["id"],
                            "debit_amount": debit_amount,
                            "credit_amount": 0,
                        },
                        {
                            "account_id": account_options[credit_account]["id"],
                            "debit_amount": 0,
                            "credit_amount": credit_amount,
                        },
                    ],
                })
                st.success("Draft voucher created.")
                st.rerun()
            except ApiError as exc:
                st.error(exc.message)
