from datetime import date
from typing import Any

import requests
import streamlit as st

from streamlit_ui.config import get_setting

DEFAULT_TIMEOUT = 30
REPORT_TIMEOUT = 90


class ApiError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def get_api_base_url() -> str:
    return get_setting("API_BASE_URL", "http://localhost:8001").rstrip("/")


def check_api_health() -> tuple[bool, str]:
    try:
        response = requests.get(f"{get_api_base_url()}/health", timeout=5)
        if response.status_code == 200:
            return True, "API is online"
        return False, f"API returned status {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "API not reachable. Run: uvicorn app.main:app --port 8001 --reload"
    except requests.exceptions.Timeout:
        return False, "API health check timed out"
    except Exception as exc:
        return False, str(exc)


def _prepare_json(payload: dict | None) -> dict | None:
    if payload is None:
        return None
    result = {}
    for key, val in payload.items():
        result[key] = val.isoformat() if isinstance(val, date) else val
    return result


def _extract_error(response: requests.Response) -> str:
    try:
        data = response.json()
        if isinstance(data, dict) and "detail" in data:
            return str(data["detail"])
    except Exception:
        pass
    return response.text or f"Request failed ({response.status_code})"


def _connection_error_message() -> str:
    return (
        f"Cannot connect to API at {get_api_base_url()}. "
        "Start the API: uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload"
    )


def _refresh_access_token() -> bool:
    refresh_token = st.session_state.get("refresh_token")
    if not refresh_token:
        return False
    try:
        response = requests.post(
            f"{get_api_base_url()}/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
            headers={"Content-Type": "application/json"},
            timeout=DEFAULT_TIMEOUT,
        )
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return False
    if response.status_code != 200:
        return False
    data = response.json()
    st.session_state.access_token = data["access_token"]
    st.session_state.refresh_token = data["refresh_token"]
    st.session_state.user = data["user"]
    return True


def _request(
    method: str,
    path: str,
    *,
    params: dict | None = None,
    json: dict | None = None,
    auth: bool = True,
    retry: bool = True,
    conn_retry: bool = True,
    timeout: int = DEFAULT_TIMEOUT,
) -> Any:
    headers = {"Content-Type": "application/json"}
    if auth:
        token = st.session_state.get("access_token")
        if not token:
            raise ApiError("Not authenticated. Please log in.", 401)
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.request(
            method,
            f"{get_api_base_url()}{path}",
            params=params,
            json=_prepare_json(json),
            headers=headers,
            timeout=timeout,
        )
    except requests.exceptions.Timeout as exc:
        raise ApiError("API request timed out.", 504) from exc
    except requests.exceptions.ConnectionError as exc:
        if conn_retry:
            import time
            time.sleep(1.5)
            return _request(method, path, params=params, json=json, auth=auth, retry=retry, conn_retry=False, timeout=timeout)
        raise ApiError(_connection_error_message(), 503) from exc

    if response.status_code == 401 and auth and retry:
        if _refresh_access_token():
            return _request(method, path, params=params, json=json, auth=auth, retry=False, conn_retry=conn_retry, timeout=timeout)
        for key in ("user", "access_token", "refresh_token"):
            st.session_state.pop(key, None)
        raise ApiError("Session expired. Please log in again.", 401)

    if response.status_code >= 400:
        raise ApiError(_extract_error(response), response.status_code)

    return response.json() if response.content else {}


def login(username_or_email: str, password: str) -> dict:
    return _request("POST", "/api/v1/auth/login",
        json={"username_or_email": username_or_email, "password": password},
        auth=False, retry=False, conn_retry=False)


def register(username: str, email: str, full_name: str, password: str) -> dict:
    return _request("POST", "/api/v1/user-registrations",
        json={"username": username, "email": email, "full_name": full_name, "password": password},
        auth=False, retry=False, conn_retry=False)


def list_accounts(account_type: str | None = None, is_active: bool | None = None, page: int = 1, page_size: int = 50) -> tuple[list[dict], int]:
    params: dict[str, Any] = {"page": page, "page_size": page_size}
    if account_type:
        params["account_type"] = account_type
    if is_active is not None:
        params["is_active"] = is_active
    data = _request("GET", "/api/v1/chart-of-accounts", params=params)
    return data.get("data", []), data.get("total", 0)


def create_account(payload: dict) -> dict:
    return _request("POST", "/api/v1/chart-of-accounts", json=payload)


def list_vouchers(status: str | None = None, voucher_type: str | None = None, page: int = 1, page_size: int = 100) -> tuple[list[dict], int]:
    params: dict[str, Any] = {"page": page, "page_size": page_size}
    if status:
        params["status"] = status
    if voucher_type:
        params["voucher_type"] = voucher_type
    data = _request("GET", "/api/v1/vouchers", params=params)
    return data.get("data", []), data.get("total", 0)


def create_voucher(payload: dict) -> dict:
    return _request("POST", "/api/v1/vouchers", json=payload)


def post_voucher(voucher_id: str) -> dict:
    return _request("POST", f"/api/v1/vouchers/{voucher_id}/post")


def cancel_voucher(voucher_id: str) -> dict:
    return _request("POST", f"/api/v1/vouchers/{voucher_id}/cancel")


def generate_ledger(account_id: str, from_date: date | None, to_date: date | None) -> dict:
    payload: dict[str, Any] = {"account_id": account_id, "save": True}
    if from_date:
        payload["from_date"] = from_date
    if to_date:
        payload["to_date"] = to_date
    return _request("POST", "/api/v1/reports/ledger", json=payload, timeout=REPORT_TIMEOUT)


def generate_trial_balance(as_of_date: date) -> dict:
    return _request("POST", "/api/v1/reports/trial-balance", json={"as_of_date": as_of_date, "save": True}, timeout=REPORT_TIMEOUT)


def generate_income_statement(from_date: date, to_date: date) -> dict:
    return _request("POST", "/api/v1/reports/income-statement", json={"from_date": from_date, "to_date": to_date, "save": True}, timeout=REPORT_TIMEOUT)


def generate_balance_sheet(as_of_date: date) -> dict:
    return _request("POST", "/api/v1/reports/balance-sheet", json={"as_of_date": as_of_date, "save": True}, timeout=REPORT_TIMEOUT)
