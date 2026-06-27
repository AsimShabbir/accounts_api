from streamlit_ui.config import get_setting


def bootstrap() -> None:
    get_setting("API_BASE_URL", "http://localhost:8001")
    get_setting("STITCH_PROJECT_ID", "508804251248094601")
