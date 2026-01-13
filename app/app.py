# app/app.py
import sys
import os
from pathlib import Path
import streamlit as st

# ------------------------------------
# 1. إعداد الصفحة والمسارات
# ------------------------------------
# ملاحظة: st.set_page_config يجب أن تظل أول أمر Streamlit
st.set_page_config(
    page_title="Pediatric Smart Clinic Assistant",
    layout="wide",
    page_icon="🩺"
)

# تحديد المسارات الأساسية
APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR.parent

# إضافة المجلد الرئيسي للـ path لضمان استيراد الموديولات
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

# مسار صورة واجهة الدخول
LOGIN_IMAGE_PATH = BASE_DIR / "pics" / "photo.jpg"

# ------------------------------------
# 2. دالة حماية النظام بكلمة سر
# ------------------------------------
def check_password():
    def password_entered():
        # الأمان: يقرأ كلمة السر من Secrets في Hugging Face باسم MY_PASSWORD
        # إذا لم تكن موجودة، يستخدم القيمة الافتراضية Clinic2026
        correct_password = os.environ.get("MY_PASSWORD", "Clinic2026")
        
        if st.session_state["password_input"] == correct_password:
            st.session_state["password_correct"] = True
            del st.session_state["password_input"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state or not st.session_state["password_correct"]:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if LOGIN_IMAGE_PATH.exists():
                st.image(str(LOGIN_IMAGE_PATH), use_container_width=True)
            else:
                st.markdown("<h1 style='text-align: center; font-size: 80px;'>🏥</h1>", unsafe_allow_html=True)

        st.markdown("<h2 style='text-align: center;'>🔒 نظام إدارة العيادة الذكي</h2>", unsafe_allow_html=True)
        
        st.text_input(
            "برجاء إدخال كلمة السر للوصول للنظام", 
            type="password", 
            on_change=password_entered, 
            key="password_input"
        )
        
        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("❌ كلمة السر غير صحيحة، حاول مرة أخرى.")
            
        return False
    return True

# التحقق من الحماية
if not check_password():
    st.stop()

# ============================================================
# ⬇️ تحميل باقي التطبيق (المكتبات والصفحات) ⬇️
# ============================================================

from config import FILE_PATH, MODEL_PATH
from core.utils_ml import build_engine
from views.page_home import render_home_page
from views.page_patient_form import render_patient_form_page
from views.page_visit_form import render_visit_form_page
from views.page_search import render_search_page
from views.page_analytics import render_analytics_page
from views.page_ai_reco import render_ai_reco_page

@st.cache_resource
def build_engine_cached(file_path: Path, model_path: Path):
    return build_engine(file_path, model_path, retrain_if_missing=True)

try:
    engine = build_engine_cached(FILE_PATH, MODEL_PATH)
except Exception as e:
    st.error(f"حدث خطأ أثناء تحميل قاعدة البيانات أو الموديل: {e}")
    st.stop()

# القائمة الجانبية (Sidebar)
with st.sidebar:
    if LOGIN_IMAGE_PATH.exists():
        st.image(str(LOGIN_IMAGE_PATH), use_container_width=True)
    
    st.title("القائمة الرئيسية")
    st.markdown("---")
    if st.button("🔒 تسجيل الخروج", type="primary", use_container_width=True):
        del st.session_state["password_correct"]
        st.rerun()

# التنقل (Navigation)
page = st.sidebar.radio(
    "اختر الصفحة:",
    ["الصفحة الرئيسية", "إدخال مريض جديد", "إدخال زيارة جديدة (روشتة متعددة)", "بحث عن مريض", "تحليلات العيادة", "توصية علاج (AI)"]
)

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
