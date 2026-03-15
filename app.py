import sys
from pathlib import Path

import streamlit as st

from config import FILE_PATH, MODEL_PATH
from core.utils_ml import build_engine
from core.utils_auth import authenticate_admin, save_guest_login
from core.ui_ads import render_vip_sponsors, render_sponsor_footer, render_sponsor_sidebar
from views.page_home import render_home_page
from views.page_patient_form import render_patient_form_page
from views.page_visit_form import render_visit_form_page
from views.page_search import render_search_page
from views.page_analytics import render_analytics_page
from views.page_ai_reco import render_ai_reco_page
from views.page_admin_accounts import render_admin_accounts_page
from views.page_sponsors import render_sponsors_page


# ---- Path setup ----
BASE_DIR = Path(__file__).resolve().parent
APP_DIR = BASE_DIR / "app"
VIEWS_DIR = APP_DIR / "views"
CORE_DIR = BASE_DIR / "core"

for path in [BASE_DIR, APP_DIR, VIEWS_DIR, CORE_DIR]:
    if path.exists() and str(path) not in sys.path:
        sys.path.insert(0, str(path))


st.set_page_config(
    page_title="AI Clinic App",
    layout="wide",
    page_icon="🩺",
)

LOGIN_IMAGE_PATH = BASE_DIR / "pics" / "photo.jpg"


@st.cache_resource
def build_engine_cached(file_path: Path, model_path: Path):
    return build_engine(file_path, model_path, retrain_if_missing=True)


def _set_user(user: dict) -> None:
    st.session_state["authenticated"] = True
    st.session_state["user"] = user


def _render_login() -> None:
    st.title("Clinical Decision Support Platform")

    render_vip_sponsors()

    col_left, col_right = st.columns([1.1, 0.9], gap="large")

    with col_left:
        st.subheader("Doctor / Admin Sign-In")
        with st.form("admin_login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In")

        if submitted:
            user = authenticate_admin(username.strip(), password)
            if user is None:
                st.error("Invalid admin credentials.")
            else:
                _set_user(user)
                st.success("Signed in successfully.")
                st.rerun()

    with col_right:
        st.subheader("Guest Access")
        st.caption("Enter your name and phone number to access the demo.")
        with st.form("guest_login"):
            guest_name = st.text_input("Your Name")
            guest_phone = st.text_input("Phone Number")
            guest_submit = st.form_submit_button("Enter as Guest")

        if guest_submit:
            if not guest_name.strip() or not guest_phone.strip():
                st.error("Please enter your name and phone number.")
            else:
                save_guest_login(guest_name.strip(), guest_phone.strip())
                _set_user(
                    {
                        "user_id": "GUEST",
                        "username": "guest",
                        "display_name": guest_name.strip(),
                        "phone": guest_phone.strip(),
                        "role": "guest",
                    }
                )
                st.success(f"Welcome, {guest_name.strip()}")
                st.rerun()

    render_sponsor_footer()


def main() -> None:
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state.get("authenticated"):
        _render_login()
        return

    try:
        engine = build_engine_cached(FILE_PATH, MODEL_PATH)
    except Exception as e:
        st.error(f"Error loading data/model: {e}")
        st.stop()

    user = st.session_state.get("user", {})
    role = user.get("role", "guest")

    with st.sidebar:
        if LOGIN_IMAGE_PATH.exists():
            st.image(str(LOGIN_IMAGE_PATH), use_container_width=True)
        st.markdown(f"**Welcome, {user.get('display_name', 'User')}**")
        st.markdown("---")
        if st.button("Sign Out", type="primary", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    pages = [
        "Home",
        "New Patient",
        "New Visit",
        "Search Patient",
        "Clinic Analytics",
        "AI Recommendation",
    ]
    if role == "admin":
        pages += ["Admin Accounts", "Sponsors"]

    page = st.sidebar.radio("Select Page:", pages)
    render_sponsor_sidebar()

    st.markdown(f"### Welcome, {user.get('display_name', 'User')}")

    if page == "Home":
        render_home_page()
    elif page == "New Patient":
        render_patient_form_page(FILE_PATH, engine)
    elif page == "New Visit":
        render_visit_form_page(FILE_PATH, engine)
    elif page == "Search Patient":
        render_search_page(engine)
    elif page == "Clinic Analytics":
        render_analytics_page(engine)
    elif page == "AI Recommendation":
        render_ai_reco_page(engine)
    elif page == "Admin Accounts" and role == "admin":
        render_admin_accounts_page()
    elif page == "Sponsors" and role == "admin":
        render_sponsors_page()

    render_sponsor_footer()


if __name__ == "__main__":
    main()
