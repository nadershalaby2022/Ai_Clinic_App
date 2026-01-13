# config.py
# إعداد مسارات الملفات الرئيسية للمشروع

from pathlib import Path

# جذر المشروع (المجلد اللي فيه هذا الملف)
BASE_DIR = Path(__file__).resolve().parent

# ملف الإكسل الرئيسي
FILE_PATH = BASE_DIR / "clinic_data2.xlsx"

# مسار ملف الموديل ML
MODEL_PATH = BASE_DIR / "model_drug_reco.pkl"
