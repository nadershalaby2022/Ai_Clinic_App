import os
import sys
import subprocess

# 1. تحديد المسار الرئيسي للمشروع
# هذا السطر يضمن أن النظام يرى مجلدات views و core و app مهما كان مكان التشغيل
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# 2. إضافة المسارات الفرعية للمكتبات
# حل مشكلة "No module named views" من خلال تعريف المسار يدوياً للسيرفر
sys.path.append(os.path.join(BASE_DIR, "app"))
sys.path.append(os.path.join(BASE_DIR, "views"))
sys.path.append(os.path.join(BASE_DIR, "core"))

def run_app():
    """تشغيل تطبيق Streamlit الأساسي من المجلد الفرعي"""
    # المسار إلى ملف app.py الحقيقي
    app_path = os.path.join(BASE_DIR, "app", "app.py")
    
    # أوامر التشغيل المتوافقة مع سيرفرات الاستضافة
    command = [
        "streamlit",
        "run",
        app_path,
        "--server.port", "8501",
        "--server.address", "0.0.0.0"
    ]
    
    try:
        print(f"🚀 Starting AI Clinic App from: {app_path}...")
        subprocess.run(command, check=True)
    except Exception as e:
        print(f"❌ Error starting the app: {e}")

if __name__ == "__main__":
    run_app()
