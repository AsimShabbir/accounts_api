from datetime import date
from decimal import Decimal

import pandas as pd
import streamlit as st

from app.application.exceptions import ApplicationError
from app.domain.enums import VoucherStatus, VoucherType
from streamlit_ui.auth import render_sidebar, require_login
from streamlit_ui.bootstrap import bootstrap, get_chart_of_account_service, get_voucher_service, run_async

st.set_page_config(page_title="Vouchers", layout="wide")
bootstrap()

if not require_login():
    st.warning("Please log in from the home page.")
    st.stop()

render_sidebar()
st.title("Voucher Management")

voucher_service = get_voucher_service()
account_service = get_chart_of_account_service()

status_filter = st.selectbox(
    "Status filter",
    ["All"] + [s.value for s in VoucherStatus],
)
voucher_type_filter = st.selectbox(
    "Voucher type",
    ["All"] + [t.value for t in VoucherType],
)

status = VoucherStatus(status_filter) if status_filter != "All" else None
voucher_type = VoucherType(voucher_type_filter) if voucher_type_filter != "All" else None

try:
    vouchers, total = run_async(
        voucher_service.list_vouchers(status, voucher_type, None, None, 0, 100)
    )
except ApplicationError as exc:
    st.error(exc.message)
    st.stop()

if vouchers:
    rows = [
        {
            "Number": v.voucher_number,
            "Type": v.voucher_type.value,
            "Date": str(v.voucher_date),
            "Status": v.status.value,
            "Debit": float(v.total_debit),
            "Credit": float(v.total_credit),
            "Narration": v.narration or "",
            "ID": v.id,
        }
        for v in vouchers
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.caption(f"Showing {len(vouchers)} of {total} vouchers")

    st.subheader("Voucher actions")
    action_id = st.text_input("Voucher ID for action")
    c1, c2, c3 = st.columns(3)
    if c1.button("Post voucher"):
        try:
            run_async(voucher_service.post_voucher(action_id))
            st.success("Voucher posted.")
            st.rerun()
        except ApplicationError as exc:
            st.error(exc.message)
    if c2.button("Cancel voucher"):
        try:
            run_async(voucher_service.cancel_voucher(action_id))
            st.success("Voucher cancelled.")
            st.rerun()
        except ApplicationError as exc:
            st.error(exc.message)
else:
    st.info("No vouchers found.")

st.divider()
st.subheader("Create draft voucher")

accounts, _ = run_async(account_service.list_accounts(is_active=True, skip=0, limit=500))
postable = [a for a in accounts if not a.is_group and a.id]
account_options = {f"{a.code} - {a.name}": a.id for a in postable}

with st.form("create_voucher"):
    v_type = st.selectbox("Voucher type", [t.value for t in VoucherType])
    v_date = st.date_input("Voucher date", value=date.today())
    reference = st.text_input("Reference")
    narration = st.text_area("Narration")

    st.markdown("**Entry 1 (Debit)**")
    acc1 = st.selectbox("Account 1", list(account_options.keys()), key="acc1")
    debit1 = st.number_input("Debit amount", min_value=0.0, value=0.0, step=0.01, key="debit1")

    st.markdown("**Entry 2 (Credit)**")
    acc2 = st.selectbox("Account 2", list(account_options.keys()), key="acc2")
    credit2 = st.number_input("Credit amount", min_value=0.0, value=0.0, step=0.01, key="credit2")

    submitted = st.form_submit_button("Create draft", type="primary")

    if submitted:
        try:
            entries = [
                {
                    "account_id": account_options[acc1],
                    "debit_amount": Decimal(str(debit1)),
                    "credit_amount": Decimal("0"),
                },
                {
                    "account_id": account_options[acc2],
                    "debit_amount": Decimal("0"),
                    "credit_amount": Decimal(str(credit2)),
                },
            ]
            voucher = run_async(
                voucher_service.create_voucher(
                    {
                        "voucher_type": v_type,
                        "voucher_date": v_date,
                        "reference": reference or None,
                        "narration": narration or None,
                        "entries": entries,
                    }
                )
            )
            st.success(f"Draft voucher {voucher.voucher_number} created.")
            st.rerun()
        except ApplicationError as exc:
            st.error(exc.message)
