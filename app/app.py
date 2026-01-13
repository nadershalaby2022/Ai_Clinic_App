# app/app.py
# نقطة الدخول الرئيسية – Router بين الصفحات مع نظام حماية بكلمة سر وصورة لوجو

import sys
from pathlib import Path
import streamlit as st

# ------------------------------------
# 1. إعداد الصفحة والمسارات (يجب أن تكون في البداية)
# ------------------------------------
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
# 2. دالة حماية النظام بكلمة سر (مع الصورة)
# ------------------------------------
def check_password():
    """دالة تطلب كلمة السر وتتحقق منها، وتعرض صورة في الواجهة"""
    
    def password_entered():
        # --- كلمة السر الخاصة بالعيادة ---
        if st.session_state["password_input"] == "Clinic2026":
            st.session_state["password_correct"] = True
            del st.session_state["password_input"]  # مسح كلمة السر من الذاكرة للأمان
        else:
            st.session_state["password_correct"] = False

    # إذا لم يتم الدخول بعد، اعرض شاشة القفل
    if "password_correct" not in st.session_state or not st.session_state["password_correct"]:
        
        # --- عرض الصورة في المنتصف ---
        # نستخدم أعمدة لضبط الصورة في الوسط
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if LOGIN_IMAGE_PATH.exists():
                st.image(str(LOGIN_IMAGE_PATH), use_container_width=True)
            else:
                # لو الصورة مش موجودة، نعرض أيقونة بديلة
                st.markdown("<h1 style='text-align: center; font-size: 80px;'>🏥</h1>", unsafe_allow_html=True)

        # عنوان شاشة الدخول
        st.markdown("<h2 style='text-align: center;'>🔒 نظام إدارة العيادة الذكي</h2>", unsafe_allow_html=True)
        
        # خانة إدخال كلمة السر
        st.text_input(
            "برجاء إدخال كلمة السر للوصول للنظام", 
            type="password", 
            on_change=password_entered, 
            key="password_input"
        )
        
        # رسالة خطأ لو كلمة السر غلط
        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("❌ كلمة السر غير صحيحة، حاول مرة أخرى.")
            
        return False # لم ينجح الدخول
    
    else:
        return True # تم الدخول بنجاح

# ------------------------------------
# 3. التحقق من الحماية قبل تحميل باقي التطبيق
# ------------------------------------
if not check_password():
    st.stop()  # 🛑 إيقاف تحميل أي شيء آخر إذا لم يتم إدخال كلمة السر

# ============================================================
# ⬇️⬇️⬇️ ما بعد هذا الخط لا يعمل إلا بعد كتابة كلمة السر الصحيحة ⬇️⬇️⬇️
# ============================================================

# استيراد باقي ملفات المشروع
from config import FILE_PATH, MODEL_PATH  # noqa: E402
from core.utils_ml import build_engine  # noqa: E402

# استيراد الصفحات (Views)
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
    return build_engine(file_path, model_path, retrain_if_missing=True)

# تحميل الـ Engine مرة واحدة من الكاش
try:
    engine = build_engine_cached(FILE_PATH, MODEL_PATH)
except Exception as e:
    st.error(f"حدث خطأ أثناء تحميل قاعدة البيانات أو الموديل: {e}")
    st.stop()


# ------------------------------------
# إعداد القائمة الجانبية (Sidebar)
# ------------------------------------
# استخدام نفس الصورة في السايدبار أيضاً لو أحببت
SIDEBAR_IMAGE = LOGIN_IMAGE_PATH 

with st.sidebar:
    if SIDEBAR_IMAGE.exists():
        st.image(
            str(SIDEBAR_IMAGE),
            use_container_width=True
        )
    
    st.title("القائمة الرئيسية")

    # زر تسجيل الخروج
    st.markdown("---")
    if st.button("🔒 تسجيل الخروج", type="primary", use_container_width=True):
        # مسح حالة الدخول ليعود لشاشة القفل
        del st.session_state["password_correct"]
        st.rerun()

# ------------------------------------
# كنترول بسيط للكاش من الـ Sidebar (للمطور)
# ------------------------------------
with st.sidebar.expander("⚙️ إعدادات متقدمة"):
    if st.button("مسح الكاش وإعادة التحميل"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()


# ------------------------------------
# عنوان الصفحة الرئيسية
# ------------------------------------
# st.title("🩺 Pediatric Smart Clinic Assistant")

# ------------------------------------
# قائمة التنقل بين الصفحات
# ------------------------------------
page = st.sidebar.radio(
    "اختر الصفحة:",
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
# توجيه (Routing) للصفحة المختارة
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
