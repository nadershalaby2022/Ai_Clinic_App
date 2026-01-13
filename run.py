import streamlit as st
import os
import sys
from pathlib import Path

# إضافة المسار الحالي للمشروع لضمان استيراد الموديولات (config, core, views)
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))

# استدعاء ملف التطبيق الأصلي
try:
    # نقوم بتشغيل محتوى الملف app/app.py
    with open(current_dir / "app" / "app.py", encoding="utf-8") as f:
        code = compile(f.read(), "app.py", "exec")
        exec(code, globals())
except Exception as e:
    st.error(f"❌ خطأ في تحميل التطبيق الرئيسي: {e}")
