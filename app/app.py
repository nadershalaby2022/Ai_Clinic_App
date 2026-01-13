# app/app.py
# نقطة الدخول الرئيسية – Router بين الصفحات

import sys
from pathlib import Path

import streamlit as st

# ------------------------------------
# إعداد المسارات
# ------------------------------------
APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR.parent

if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from config import FILE_PATH, MODEL_PATH  # noqa: E402
from core.utils_ml import build_engine  # noqa: E402

# 💡 مهم: بعد ما تغيّر اسم المجلد من pages إلى views
from views.page_home import render_home_page  # noqa: E402
from views.page_patient_form import render_patient_form_page  # noqa: E402
from views.page_visit_form import render_visit_form_page  # noqa: E402
from views.page_search import render_search_page  # noqa: E402
from views.page_analytics import render_analytics_page  # noqa: E402
from views.page_ai_reco import render_ai_reco_page  # noqa: E402


# ------------------------------------
# كاش للـ Engine (داتا + موديل)
# ------------------------------------
@st.cache_resource
def build_engine_cached(file_path: Path, model_path: Path):
    """
    يبني الـ engine (داتا + موديل التوصية) مرة واحدة
    ويتخزن في الكاش لتحسين الأداء.
    """
    return build_engine(file_path, model_path, retrain_if_missing=True)


# ------------------------------------
# إعداد الصفحة العامة
# ------------------------------------
st.set_page_config(
    page_title="Pediatric Smart Clinic Assistant",
    layout="wide",
)
# ------------------------------------
# صورة الطبيب في أعلى الـ Sidebar
# ------------------------------------
SIDEBAR_IMAGE = BASE_DIR / "pics" / "photo.jpg"

with st.sidebar:
    if SIDEBAR_IMAGE.exists():
        st.image(
            str(SIDEBAR_IMAGE),
            use_container_width=True
        )
    else:
        st.warning("⚠️ صورة الطبيب غير موجودة")

# ------------------------------------
# كنترول بسيط للكاش من الـ Sidebar
# ------------------------------------
with st.sidebar.expander("إعدادات النظام"):
    if st.button("مسح الكاش وإعادة التحميل"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()  # ✅ النسخة الجديدة من Streamlit


# تحميل الـ Engine مرة واحدة من الكاش
engine = build_engine_cached(FILE_PATH, MODEL_PATH)

st.title("🩺 Pediatric Smart Clinic Assistant")

# ------------------------------------
# قائمة الصفحات
# ------------------------------------
page = st.sidebar.radio(
    "اختر الصفحة",
    [
        "الصفحة الرئيسية",
        "إدخال مريض جديد",
        "إدخال زيارة جديدة (روشتة متعددة)",
        "بحث عن مريض",
        "تحليلات العيادة",
        "توصية علاج (AI)",
    ],
)

# ------------------------------------
# ربط كل اختيار بدالة الصفحة الخاصة به
# ------------------------------------
if page == "الصفحة الرئيسية":
    render_home_page()

elif page == "إدخال مريض جديد":
    render_patient_form_page(FILE_PATH, engine)

elif page == "إدخال زيارة جديدة (روشتة متعددة)":
    render_visit_form_page(FILE_PATH, engine)

elif page == "بحث عن مريض":
    render_search_page(engine)

elif page == "تحليلات العيادة":
    render_analytics_page(engine)

elif page == "توصية علاج (AI)":
    render_ai_reco_page(engine)
