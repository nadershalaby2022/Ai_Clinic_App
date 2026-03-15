import sys
from pathlib import Path

# ---- Path setup (must run before local imports) ----
BASE_DIR = Path(__file__).resolve().parent
APP_DIR = BASE_DIR / "app"
VIEWS_DIR = APP_DIR / "views"
CORE_DIR = BASE_DIR / "core"

for path in [BASE_DIR, APP_DIR, VIEWS_DIR, CORE_DIR]:
    if path.exists() and str(path) not in sys.path:
        sys.path.insert(0, str(path))

import streamlit as st

from config import FILE_PATH, MODEL_PATH
from core.utils_ml import build_engine
from core.utils_auth import authenticate_admin, save_guest_login
from core.ui_ads import render_vip_sponsors, render_sponsor_footer, render_sponsor_sidebar
from views.page_home import render_home_page
from views.page_visit_form import render_visit_form_page
from views.page_search import render_search_page
from views.page_analytics import render_analytics_page
from views.page_ai_reco import render_ai_reco_page
from views.page_admin_accounts import render_admin_accounts_page
from views.page_sponsors import render_sponsors_page

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
    if "ui_lang" not in st.session_state:
        st.session_state["ui_lang"] = "en"

    lang_label = st.selectbox(
        "Language / اللغة",
        ["English", "العربية"],
        index=0 if st.session_state["ui_lang"] == "en" else 1,
    )
    st.session_state["ui_lang"] = "en" if lang_label == "English" else "ar"
    lang = st.session_state["ui_lang"]

    def _t(en: str, ar: str) -> str:
        return en if lang == "en" else ar

    st.title(_t("Clinic & drug analysis and its effectiveness", "منصة دعم القرار السريري"))
    st.title(_t("نموذج اختبار البرنامج قبل شرائة"))
  
    render_vip_sponsors()

    col_left, col_right = st.columns([1.1, 0.9], gap="large")

    with col_left:
        st.subheader(_t("Doctor / Admin Sign-In", "دخول الطبيب / الأدمن"))
        with st.form("admin_login"):
            username = st.text_input(_t("Username", "اسم المستخدم"))
            password = st.text_input(_t("Password", "كلمة المرور"), type="password")
            submitted = st.form_submit_button(_t("Sign In", "تسجيل الدخول"))

        if submitted:
            user = authenticate_admin(username.strip(), password)
            if user is None:
                st.error(_t("Invalid admin credentials.", "بيانات الأدمن غير صحيحة."))
            else:
                _set_user(user)
                st.success(_t("Signed in successfully.", "تم تسجيل الدخول بنجاح."))
                st.rerun()

    with col_right:
        st.subheader(_t("Guest Access", "دخول كضيف"))
        st.caption(_t("Enter your name and phone number to access the demo.", "ادخل الاسم ورقم الهاتف للدخول كضيف."))
        with st.form("guest_login"):
            guest_name = st.text_input(_t("Your Name", "اسمك"))
            guest_phone = st.text_input(_t("Phone Number", "رقم الهاتف"))
            guest_submit = st.form_submit_button(_t("Enter as Guest", "دخول كضيف"))

        if guest_submit:
            if not guest_name.strip() or not guest_phone.strip():
                st.error(_t("Please enter your name and phone number.", "من فضلك أدخل الاسم ورقم الهاتف."))
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
                st.success(_t(f"Welcome, {guest_name.strip()}", f"مرحبًا، {guest_name.strip()}"))
                st.rerun()
              
    render_sponsor_footer()

    
def main() -> None:
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "ui_lang" not in st.session_state:
        st.session_state["ui_lang"] = "en"

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

    lang = st.session_state.get("ui_lang", "en")

    def _t(en: str, ar: str) -> str:
        return en if lang == "en" else ar

    with st.sidebar:
        lang_label = st.selectbox(
            "Language / اللغة",
            ["English", "العربية"],
            index=0 if st.session_state["ui_lang"] == "en" else 1,
        )
        st.session_state["ui_lang"] = "en" if lang_label == "English" else "ar"
        lang = st.session_state["ui_lang"]
        if LOGIN_IMAGE_PATH.exists():
            st.image(str(LOGIN_IMAGE_PATH), use_container_width=True)
        st.markdown(f"**{_t('Welcome', 'مرحبًا')}, {user.get('display_name', 'User')}**")
        st.markdown("---")
        if st.button(_t("Sign Out", "تسجيل الخروج"), type="primary", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    page_items = [
        ("Home", {"en": "Home", "ar": "الصفحة الرئيسية"}),
        ("New Visit", {"en": "New Visit", "ar": "زيارة جديدة"}),
        ("Search Patient", {"en": "Search Patient", "ar": "بحث عن مريض"}),
        ("Clinic Analytics", {"en": "Clinic Analytics", "ar": "تحليلات العيادة"}),
        ("AI Recommendation", {"en": "AI Recommendation", "ar": "توصيات الذكاء الاصطناعي"}),
    ]
    if role == "admin":
        page_items += [
            ("Admin Accounts", {"en": "Admin Accounts", "ar": "حسابات الأدمن"}),
            ("Sponsors", {"en": "Sponsors", "ar": "الرعاة"}),
        ]

    page_labels = [item[1][lang] for item in page_items]
    selected_label = st.sidebar.radio(_t("Select Page:", "اختر الصفحة:"), page_labels)
    page = page_items[page_labels.index(selected_label)][0]
    render_sponsor_sidebar()

    st.markdown(f"### {_t('Welcome', 'مرحبًا')}, {user.get('display_name', 'User')}")

    if page == "Home":
        render_home_page()
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
