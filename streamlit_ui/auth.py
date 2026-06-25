import streamlit as st

from app.application.exceptions import ApplicationError
from streamlit_ui.bootstrap import get_auth_service, run_async


def require_login() -> bool:
    return bool(st.session_state.get("user"))


def render_login() -> None:
    st.title("Accounting System")
    st.caption("Sign in to manage accounts, vouchers, and reports.")

    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        with st.form("login_form"):
            username_or_email = st.text_input("Email or username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", type="primary")

        if submitted:
            try:
                user, access_token, refresh_token = run_async(
                    get_auth_service().login(username_or_email, password)
                )
                st.session_state.user = {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                }
                st.session_state.access_token = access_token
                st.session_state.refresh_token = refresh_token
                st.success("Logged in successfully.")
                st.rerun()
            except ApplicationError as exc:
                st.error(exc.message)

    with tab_register:
        with st.form("register_form"):
            username = st.text_input("Username")
            email = st.text_input("Email")
            full_name = st.text_input("Full name")
            password = st.text_input("Password", type="password", key="reg_password")
            submitted = st.form_submit_button("Create account")

        if submitted:
            try:
                user = run_async(
                    get_auth_service().register_user(
                        {
                            "username": username,
                            "email": email,
                            "full_name": full_name,
                            "password": password,
                        }
                    )
                )
                st.success(f"Account created for {user.username}. Please log in.")
            except ApplicationError as exc:
                st.error(exc.message)


def render_sidebar() -> None:
    user = st.session_state.get("user", {})
    st.sidebar.title("Accounting")
    st.sidebar.write(f"**{user.get('full_name', '')}**")
    st.sidebar.caption(user.get("email", ""))

    if st.sidebar.button("Logout"):
        for key in ("user", "access_token", "refresh_token"):
            st.session_state.pop(key, None)
        st.rerun()
